#!/usr/bin/env python3
"""Tự động tóm tắt chi tiết truyện (TXT/PDF) bằng Claude API, phục vụ thiết kế game.

Pipeline:
  1. Tải file (thư mục Google Drive công khai) hoặc dùng file có sẵn.
  2. Tách chương (TXT hoặc PDF qua pdftotext/pypdf).
  3. MAP   - gom vài chương thành một "chunk", Claude trích xuất JSON chi tiết:
             tóm tắt từng chương, sự kiện, nhân vật, địa điểm, vật phẩm,
             công pháp/thần thông, yêu thú, cảnh giới của nhân vật chính, lore.
  4. MERGE - gộp thực thể (nhân vật, vật phẩm...) bằng code, đếm số lần xuất hiện.
  5. ARC   - mỗi ~100 chương: Claude viết tóm tắt hồi + gợi ý thiết kế game
             (quest chính, boss, bản đồ, cơ chế).
  6. PROFILE - hồ sơ đầy đủ cho các nhân vật xuất hiện nhiều nhất.
  7. BOOK  - tổng quan cả bộ từ các hồi.
  8. Xuất JSON + Markdown.

Mọi kết quả trung gian được cache trong thư mục output, chạy lại sẽ tiếp tục
từ chỗ dừng (không gọi API lại cho phần đã xong).

Ví dụ:
  pip install -r tools/requirements-tom-tat.txt
  export ANTHROPIC_API_KEY=...
  # Tải cả thư mục Drive rồi tóm tắt mọi file trong đó
  python tools/tom_tat_truyen.py --drive-folder 1jDH1IPViGl4MgKU2bCjXrtH4xV_bMhwn --out tom_tat
  # Hoặc dùng file có sẵn
  python tools/tom_tat_truyen.py --input "Pham Nhan Tu Tien Full 2446c.txt" --out tom_tat
  # Chỉ xem số chương/chunk và ước lượng chi phí, không gọi API
  python tools/tom_tat_truyen.py --input truyen.pdf --dry-run
  # Chạy thử 30 chương đầu
  python tools/tom_tat_truyen.py --input truyen.txt --chapters 1-30
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

DEFAULT_MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

# --------------------------------------------------------------------------- #
# Tải từ Google Drive
# --------------------------------------------------------------------------- #

def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return resp.read()


def list_drive_folder(folder_id: str) -> list[tuple[str, str]]:
    """Trả về [(file_id, tên file)] của một thư mục Drive chia sẻ công khai."""
    page = _http_get(f"https://drive.google.com/embeddedfolderview?id={folder_id}").decode("utf-8", "replace")
    entries = re.findall(
        r'<div class="flip-entry" id="entry-([\w-]+)".*?<div class="flip-entry-title">(.*?)</div>',
        page, re.S)
    return [(fid, html.unescape(name).strip()) for fid, name in entries]


def download_drive_folder(folder_id: str, dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for fid, name in list_drive_folder(folder_id):
        if not name.lower().endswith((".txt", ".pdf")):
            log(f"Bỏ qua {name} (chỉ hỗ trợ .txt/.pdf)")
            continue
        path = dest / name
        if path.exists() and path.stat().st_size > 0:
            log(f"Đã có {name}, không tải lại")
        else:
            log(f"Đang tải {name} ...")
            data = _http_get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t")
            if data[:15].lower().startswith((b"<!doctype html", b"<html")):
                raise RuntimeError(f"Drive trả về trang HTML thay vì file {name}; kiểm tra quyền chia sẻ.")
            path.write_bytes(data)
        paths.append(path)
    if not paths:
        raise RuntimeError("Không tìm thấy file .txt/.pdf nào trong thư mục Drive.")
    return paths

# --------------------------------------------------------------------------- #
# Đọc file và tách chương
# --------------------------------------------------------------------------- #

CHAPTER_RE = re.compile(r"^\s*Chương\s*(\d{1,5})\s*[:：.\-–]?\s*(.*)$", re.M)
# Dòng rác hay gặp trong ebook PDF (header/footer trang)
JUNK_LINE_RE = re.compile(r"^\s*(dtv-ebook\.com|bachngocsach\.com|Người dịch:.*|Nguồn:.*|\d{1,5})\s*$", re.I)


def read_book_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        if shutil.which("pdftotext"):
            out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                                 check=True, capture_output=True)
            text = out.stdout.decode("utf-8", "replace")
        else:
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    else:
        raw = path.read_bytes()
        for enc in ("utf-8-sig", "utf-16", "cp1258"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = raw.decode("utf-8", "replace")
    return unicodedata.normalize("NFC", text.replace("\r", ""))


def split_chapters(text: str, title_hint: str = "") -> dict[int, dict]:
    """Tách văn bản thành {số chương: {title, text}}.

    Mục lục ở đầu ebook cũng khớp regex, nên với mỗi số chương giữ bản dài nhất.
    """
    title_upper = title_hint.upper().strip()
    matches = list(CHAPTER_RE.finditer(text))
    chapters: dict[int, dict] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        lines = []
        for line in text[start:end].split("\n"):
            if JUNK_LINE_RE.match(line):
                continue
            if title_upper and line.strip().upper() == title_upper:
                continue
            lines.append(line.rstrip())
        body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
        num = int(m.group(1))
        title = re.sub(r"^Chương\s*", "", m.group(2).strip())
        if num not in chapters or len(body) > len(chapters[num]["text"]):
            chapters[num] = {"title": title, "text": body}
    return dict(sorted(chapters.items()))


def make_chunks(chapters: dict[int, dict], max_chars: int, max_chapters: int) -> list[list[int]]:
    chunks, cur, size = [], [], 0
    for num, ch in chapters.items():
        n = len(ch["text"])
        if cur and (size + n > max_chars or len(cur) >= max_chapters):
            chunks.append(cur)
            cur, size = [], 0
        cur.append(num)
        size += n
    if cur:
        chunks.append(cur)
    return chunks

# --------------------------------------------------------------------------- #
# JSON schema cho structured output
# --------------------------------------------------------------------------- #

def obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def arr(item: dict) -> dict:
    return {"type": "array", "items": item}


S = {"type": "string"}
I = {"type": "integer"}
SA = arr(S)

CHUNK_SCHEMA = obj({
    "chuong": arr(obj({
        "so": I, "tieu_de": S,
        "tom_tat": {"type": "string", "description": "Tóm tắt chi tiết 150-400 chữ: ai làm gì, ở đâu, vì sao, kết quả."},
        "dia_diem": SA, "nhan_vat_xuat_hien": SA,
    })),
    "su_kien": arr(obj({
        "chuong": I, "ten": S, "loai": {"type": "string", "enum": [
            "chien_dau", "dot_pha", "co_duyen", "kham_pha", "giao_dich", "dau_gia", "am_muu",
            "tinh_cam", "luyen_dan_luyen_khi", "truy_sat_chay_tron", "nhiem_vu", "chuyen_canh", "khac"]},
        "mo_ta": S, "dia_diem": S, "nhan_vat": SA, "ket_qua": S,
        "goi_y_game": {"type": "string", "description": "Có thể làm thành gì trong game: main quest, side quest, boss, cutscene, bí cảnh, hệ thống..."},
    })),
    "nhan_vat": arr(obj({
        "ten": S, "bi_danh": SA, "gioi_tinh": S, "chung_toc": S, "the_luc": S,
        "canh_gioi": S, "quan_he_voi_nhan_vat_chinh": S, "tinh_cach": S,
        "phap_bao": SA, "cong_phap_than_thong": SA, "hanh_dong_trong_doan": S,
        "trang_thai": {"type": "string", "enum": ["song", "chet", "bi_phong_an", "chuyen_the", "khong_ro"]},
    })),
    "dia_diem": arr(obj({
        "ten": S, "loai": S, "thuoc_khu_vuc": S, "mo_ta": S,
        "muc_do_nguy_hiem": S, "tai_nguyen_dac_san": SA, "the_luc_kiem_soat": S,
    })),
    "vat_pham": arr(obj({
        "ten": S, "loai": {"type": "string", "enum": [
            "phap_bao", "tien_khi", "dan_duoc", "linh_thao", "tai_lieu", "phu_luc", "tran_phap",
            "khoi_loi", "linh_trung_linh_thu", "ngoc_gian_cong_phap", "tien_te", "khac"]},
        "pham_cap": S, "cong_dung": S, "chu_so_huu": S, "cach_co_duoc": S,
    })),
    "cong_phap_than_thong": arr(obj({
        "ten": S, "loai": {"type": "string", "enum": [
            "cong_phap_tu_luyen", "luyen_the", "than_thong", "bi_thuat", "kiem_quyet",
            "tran_phap", "phap_tac", "khac"]},
        "cap_do": S, "hieu_qua": S, "nguoi_su_dung": SA,
    })),
    "yeu_thu_quai_vat": arr(obj({"ten": S, "cap_do": S, "nang_luc": S, "dia_diem": S, "chien_loi_pham": SA})),
    "the_luc": arr(obj({"ten": S, "loai": S, "lanh_dao": S, "mo_ta": S, "quan_he_voi_nhan_vat_chinh": S})),
    "the_gioi_quan": {"type": "array", "items": S,
                      "description": "Quy tắc thế giới/lore mới: hệ thống cảnh giới, giới diện, thiên kiếp, quy luật pháp tắc..."},
    "canh_gioi_nhan_vat_chinh_cuoi_doan": S,
    "tom_tat_doan": {"type": "string", "description": "Tóm tắt cả đoạn 200-500 chữ."},
})

ARC_SCHEMA = obj({
    "ten_hoi": S, "chuong_tu": I, "chuong_den": I,
    "boi_canh": S, "canh_gioi_dau_hoi": S, "canh_gioi_cuoi_hoi": S,
    "tom_tat": {"type": "string", "description": "Tóm tắt hồi rất chi tiết, 1200-2500 chữ, theo trình tự thời gian."},
    "dong_su_kien_chinh": arr(obj({"chuong": S, "su_kien": S, "y_nghia": S})),
    "nhan_vat_quan_trong": arr(obj({"ten": S, "vai_tro_trong_hoi": S})),
    "ban_do_khu_vuc": arr(obj({"ten": S, "mo_ta": S, "goi_y_thiet_ke_map": S})),
    "thiet_ke_game": obj({
        "main_quest": arr(obj({"ten": S, "chuong": S, "muc_tieu": S, "cac_buoc": SA, "phan_thuong": SA})),
        "side_quest": arr(obj({"ten": S, "chuong": S, "mo_ta": S, "phan_thuong": SA})),
        "boss": arr(obj({"ten": S, "chuong": S, "canh_gioi": S, "chieu_thuc": SA, "co_che_goi_y": S, "roi_do": SA})),
        "co_che_he_thong": arr(obj({"ten": S, "mo_ta": S, "lay_cam_hung_tu": S})),
        "cutscene": arr(obj({"ten": S, "chuong": S, "noi_dung": S})),
    }),
    "phuc_but_va_bi_an": SA,
})

PROFILE_SCHEMA = obj({
    "ten": S, "bi_danh": SA, "gioi_tinh": S, "chung_toc": S, "xuat_than": S, "the_luc": SA,
    "tinh_cach": S, "ngoai_hinh": S,
    "tien_trinh_canh_gioi": arr(obj({"chuong": S, "canh_gioi": S})),
    "phap_bao": arr(obj({"ten": S, "mo_ta": S})),
    "cong_phap_than_thong": arr(obj({"ten": S, "mo_ta": S})),
    "quan_he": arr(obj({"voi": S, "quan_he": S})),
    "cuoc_doi": {"type": "string", "description": "Tiểu sử chi tiết theo thời gian, có số chương."},
    "ket_cuc": S,
    "goi_y_game": obj({"vai_tro": S, "chi_so_dac_trung": S, "ky_nang_goi_y": SA, "thoai_mau": SA}),
})

BOOK_SCHEMA = obj({
    "ten_truyen": S, "tac_gia": S, "the_loai": S,
    "tom_tat_tong_quan": {"type": "string", "description": "2000-4000 chữ, toàn bộ cốt truyện từ đầu đến cuối."},
    "he_thong_canh_gioi": arr(obj({"canh_gioi": S, "mo_ta": S, "tuoi_tho_hoac_dac_diem": S})),
    "cac_gioi_dien_va_ban_do": arr(obj({"ten": S, "mo_ta": S})),
    "cac_hoi": arr(obj({"ten_hoi": S, "chuong": S, "tom_tat_ngan": S})),
    "chu_de_va_tinh_than": SA,
    "de_xuat_cau_truc_game": obj({
        "vong_lap_gameplay_chinh": S, "cac_chuong_game": arr(obj({"ten": S, "pham_vi_chuong": S, "noi_dung": S})),
        "he_thong_goi_y": SA,
    }),
})

# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #

SYSTEM_BASE = """Bạn là biên tập viên truyện tiên hiệp kiêm game designer. Nhiệm vụ: đọc nguyên văn truyện tiếng Việt \
và trích xuất dữ liệu CHI TIẾT, CHÍNH XÁC để đội ngũ làm game nhập vai tu tiên dùng làm tài liệu thiết kế.

Quy tắc:
- Chỉ ghi điều có trong văn bản được cung cấp; không bịa, không lấy kiến thức ngoài. Không rõ thì ghi "không rõ".
- Giữ nguyên tên riêng Hán Việt như trong truyện (nhân vật, pháp bảo, công pháp, địa danh).
- Ghi số chương cho sự kiện. Cảnh giới ghi cụ thể (ví dụ "Kết Đan sơ kỳ", "Kim Tiên hậu kỳ").
- Nhân vật dùng bí danh/đổi tên: dùng tên thật làm "ten", tên giả vào "bi_danh".
- Liệt kê đầy đủ: mọi nhân vật có tên, mọi pháp bảo/đan dược/công pháp được nhắc có tác dụng, mọi địa danh.
- Viết bằng tiếng Việt có dấu.
"""


def build_system(book_name: str, glossary: str) -> list[dict]:
    text = SYSTEM_BASE + f"\nTruyện đang xử lý: {book_name}\n"
    if glossary:
        text += f"\nGhi chú bối cảnh (dùng để nhận diện tên, không phải nguồn sự kiện):\n{glossary}\n"
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

# --------------------------------------------------------------------------- #
# Gọi Claude
# --------------------------------------------------------------------------- #

_log_lock = threading.Lock()


def log(msg: str) -> None:
    with _log_lock:
        print(time.strftime("[%H:%M:%S]"), msg, file=sys.stderr, flush=True)


class Claude:
    def __init__(self, model: str, effort: str, max_tokens: int):
        import anthropic
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(max_retries=6, timeout=1800)
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.usage = defaultdict(int)
        self._lock = threading.Lock()

    def json_call(self, system: list[dict], prompt: str, schema: dict) -> dict:
        kwargs = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
        )
        # Fallback phía server khi bị từ chối (chỉ áp dụng cho dòng Opus/Fable/Sonnet 5.5 trên Claude API).
        if self.model.startswith(("claude-opus-5", "claude-fable-5", "claude-sonnet-5-5")):
            kwargs["betas"] = [FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        with self.client.beta.messages.stream(**kwargs) as stream:
            msg = stream.get_final_message()
        with self._lock:
            u = msg.usage
            self.usage["input"] += u.input_tokens or 0
            self.usage["output"] += u.output_tokens or 0
            self.usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
            self.usage["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
        if msg.stop_reason == "refusal":
            raise RuntimeError(f"Model từ chối: {getattr(msg, 'stop_details', None)}")
        if msg.stop_reason == "max_tokens":
            raise RuntimeError("Hết max_tokens - tăng --max-tokens hoặc giảm --chunk-chars")
        text = next(b.text for b in msg.content if b.type == "text")
        return json.loads(text)

# --------------------------------------------------------------------------- #
# Các bước xử lý
# --------------------------------------------------------------------------- #

def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_parallel(jobs: list, fn, workers: int, label: str) -> int:
    """Chạy fn(job) song song, trả về số job lỗi (job lỗi sẽ được làm lại ở lần chạy sau)."""
    if not jobs:
        return 0
    failed = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, j): j for j in jobs}
        for done, fut in enumerate(cf.as_completed(futs), 1):
            try:
                fut.result()
                log(f"{label}: xong {done}/{len(jobs)}")
            except Exception as e:  # noqa: BLE001 - ghi log rồi tiếp tục các job khác
                failed += 1
                log(f"{label}: LỖI ở {futs[fut]}: {type(e).__name__}: {e}")
    return failed


def stage_map(claude: Claude, system, chapters, chunks, out: Path, workers: int) -> int:
    def job(chunk):
        path = out / "chunks" / f"{chunk[0]:05d}-{chunk[-1]:05d}.json"
        if path.exists():
            return
        body = "\n\n".join(
            f"===== Chương {n}: {chapters[n]['title']} =====\n{chapters[n]['text']}" for n in chunk)
        prompt = (f"Dưới đây là nguyên văn chương {chunk[0]} đến {chunk[-1]}. "
                  f"Trích xuất dữ liệu theo schema; mỗi chương phải có một mục trong 'chuong'.\n\n{body}")
        data = claude.json_call(system, prompt, CHUNK_SCHEMA)
        data["_chuong_tu"], data["_chuong_den"] = chunk[0], chunk[-1]
        write_json(path, data)

    todo = [c for c in chunks if not (out / "chunks" / f"{c[0]:05d}-{c[-1]:05d}.json").exists()]
    log(f"MAP: {len(chunks) - len(todo)} chunk đã có cache, cần xử lý {len(todo)}")
    return run_parallel(todo, job, workers, "MAP")


def load_chunk_results(out: Path) -> list[dict]:
    return [read_json(p) for p in sorted((out / "chunks").glob("*.json"))]


def norm_key(name: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", name)).strip().lower()


def merge_entities(results: list[dict]) -> dict[str, list[dict]]:
    """Gộp thực thể cùng tên qua các chunk; giữ mọi mô tả + chương xuất hiện."""
    kinds = ["nhan_vat", "dia_diem", "vat_pham", "cong_phap_than_thong", "yeu_thu_quai_vat", "the_luc"]
    merged: dict[str, dict[str, dict]] = {k: {} for k in kinds}
    for r in results:
        span = f"{r['_chuong_tu']}-{r['_chuong_den']}"
        for kind in kinds:
            for e in r.get(kind, []):
                name = (e.get("ten") or "").strip()
                if not name or name.lower() == "không rõ":
                    continue
                cur = merged[kind].setdefault(norm_key(name), {"ten": name, "so_lan_xuat_hien": 0,
                                                               "doan_xuat_hien": [], "ghi_chep": []})
                cur["so_lan_xuat_hien"] += 1
                cur["doan_xuat_hien"].append(span)
                note = {k: v for k, v in e.items() if k != "ten" and v not in ("", [], "không rõ")}
                note["doan"] = span
                cur["ghi_chep"].append(note)
                # Trường dạng danh sách: hợp nhất; trường chuỗi: lấy giá trị mới nhất
                for k, v in e.items():
                    if k == "ten" or v in ("", [], "không rõ"):
                        continue
                    if isinstance(v, list):
                        cur.setdefault(k, [])
                        cur[k] += [x for x in v if x not in cur[k]]
                    else:
                        cur[k + "_moi_nhat"] = v
    return {k: sorted(v.values(), key=lambda e: -e["so_lan_xuat_hien"]) for k, v in merged.items()}


def group_arcs(results: list[dict], arc_size: int) -> list[list[dict]]:
    arcs: list[list[dict]] = []
    for r in results:
        if not arcs or r["_chuong_den"] - arcs[-1][0]["_chuong_tu"] + 1 > arc_size:
            arcs.append([])
        arcs[-1].append(r)
    return arcs


def compact_for_arc(r: dict) -> dict:
    keep = ["chuong", "su_kien", "canh_gioi_nhan_vat_chinh_cuoi_doan", "tom_tat_doan", "the_gioi_quan"]
    d = {k: r.get(k) for k in keep}
    d["nhan_vat"] = [{"ten": n["ten"], "canh_gioi": n["canh_gioi"], "quan_he": n["quan_he_voi_nhan_vat_chinh"],
                      "hanh_dong": n["hanh_dong_trong_doan"]} for n in r.get("nhan_vat", [])]
    d["vat_pham"] = [f"{v['ten']} ({v['loai']}): {v['cong_dung']}" for v in r.get("vat_pham", [])]
    d["dia_diem"] = [f"{p['ten']}: {p['mo_ta']}" for p in r.get("dia_diem", [])]
    return d


def stage_arcs(claude: Claude, system, results, out: Path, arc_size: int, workers: int) -> int:
    arcs = group_arcs(results, arc_size)

    def job(arc):
        a, b = arc[0]["_chuong_tu"], arc[-1]["_chuong_den"]
        path = out / "arcs" / f"{a:05d}-{b:05d}.json"
        if path.exists():
            return
        payload = json.dumps([compact_for_arc(r) for r in arc], ensure_ascii=False)
        prompt = (f"Dưới đây là dữ liệu đã trích xuất cho chương {a}-{b} (JSON theo từng đoạn). "
                  "Hãy viết tổng kết hồi truyện này và đề xuất thiết kế game bám sát nội dung. "
                  f"Chỉ dùng thông tin trong dữ liệu.\n\n{payload}")
        data = claude.json_call(system, prompt, ARC_SCHEMA)
        data["chuong_tu"], data["chuong_den"] = a, b
        write_json(path, data)

    todo = [arc for arc in arcs if not (out / "arcs" /
            f"{arc[0]['_chuong_tu']:05d}-{arc[-1]['_chuong_den']:05d}.json").exists()]
    log(f"ARC: {len(arcs)} hồi, cần xử lý {len(todo)}")
    return run_parallel(todo, job, workers, "ARC")


def stage_profiles(claude: Claude, system, entities, out: Path, top: int, workers: int) -> int:
    people = entities["nhan_vat"][:top]

    def job(p):
        slug = re.sub(r"[^\w]+", "_", norm_key(p["ten"]))[:60]
        path = out / "profiles" / f"{slug}.json"
        if path.exists():
            return
        notes = p["ghi_chep"]
        if len(notes) > 400:  # nhân vật chính: lấy mẫu đều để vừa ngữ cảnh
            step = len(notes) / 400
            notes = [notes[int(i * step)] for i in range(400)]
        prompt = (f"Các ghi chép về nhân vật '{p['ten']}' qua toàn bộ truyện (theo thứ tự chương). "
                  "Lập hồ sơ nhân vật đầy đủ cho game.\n\n" + json.dumps(notes, ensure_ascii=False))
        write_json(path, claude.json_call(system, prompt, PROFILE_SCHEMA))

    log(f"PROFILE: {len(people)} nhân vật")
    return run_parallel(people, job, workers, "PROFILE")


def stage_book(claude: Claude, system, out: Path) -> None:
    path = out / "tong_quan.json"
    if path.exists():
        return
    arcs = [read_json(p) for p in sorted((out / "arcs").glob("*.json"))]
    slim = [{k: a[k] for k in ("ten_hoi", "chuong_tu", "chuong_den", "boi_canh", "canh_gioi_dau_hoi",
                               "canh_gioi_cuoi_hoi", "tom_tat", "dong_su_kien_chinh")} for a in arcs]
    lore = []
    for r in load_chunk_results(out):
        lore += r.get("the_gioi_quan", [])
    prompt = ("Dưới đây là tóm tắt tất cả các hồi và các ghi chép lore. Viết tổng quan toàn bộ truyện "
              "và đề xuất cấu trúc game.\n\nHỒI:\n" + json.dumps(slim, ensure_ascii=False) +
              "\n\nLORE:\n" + json.dumps(list(dict.fromkeys(lore)), ensure_ascii=False))
    write_json(path, claude.json_call(system, prompt, BOOK_SCHEMA))

# --------------------------------------------------------------------------- #
# Xuất Markdown
# --------------------------------------------------------------------------- #

def md_list(items) -> str:
    return "\n".join(f"- {x}" for x in items) if items else "_(không có)_"


def export_markdown(out: Path, book_name: str) -> Path:
    lines = [f"# Tóm tắt chi tiết: {book_name}", ""]
    if (out / "tong_quan.json").exists():
        b = read_json(out / "tong_quan.json")
        lines += ["## Tổng quan", "", b["tom_tat_tong_quan"], "", "## Hệ thống cảnh giới", "",
                  "| Cảnh giới | Mô tả | Đặc điểm |", "|---|---|---|"]
        lines += [f"| {c['canh_gioi']} | {c['mo_ta']} | {c['tuoi_tho_hoac_dac_diem']} |" for c in b["he_thong_canh_gioi"]]
        lines += ["", "## Đề xuất cấu trúc game", "", b["de_xuat_cau_truc_game"]["vong_lap_gameplay_chinh"], ""]
        lines += [f"- **{c['ten']}** (chương {c['pham_vi_chuong']}): {c['noi_dung']}"
                  for c in b["de_xuat_cau_truc_game"]["cac_chuong_game"]]
        lines.append("")
    for p in sorted((out / "arcs").glob("*.json")):
        a = read_json(p)
        g = a["thiet_ke_game"]
        lines += [f"## {a['ten_hoi']} (chương {a['chuong_tu']}–{a['chuong_den']})", "",
                  f"*Bối cảnh:* {a['boi_canh']}  ", f"*Cảnh giới:* {a['canh_gioi_dau_hoi']} → {a['canh_gioi_cuoi_hoi']}",
                  "", a["tom_tat"], "", "### Sự kiện chính", ""]
        lines += [f"- **Ch.{e['chuong']}** {e['su_kien']} — {e['y_nghia']}" for e in a["dong_su_kien_chinh"]]
        lines += ["", "### Thiết kế game", "", "**Main quest**"]
        lines += [f"- {q['ten']} (ch.{q['chuong']}): {q['muc_tieu']} | Bước: {'; '.join(q['cac_buoc'])} | Thưởng: {', '.join(q['phan_thuong'])}"
                  for q in g["main_quest"]]
        lines += ["", "**Side quest**"] + [f"- {q['ten']} (ch.{q['chuong']}): {q['mo_ta']}" for q in g["side_quest"]]
        lines += ["", "**Boss**"] + [f"- {x['ten']} [{x['canh_gioi']}] (ch.{x['chuong']}): chiêu {', '.join(x['chieu_thuc'])}; "
                                     f"cơ chế: {x['co_che_goi_y']}; rơi: {', '.join(x['roi_do'])}" for x in g["boss"]]
        lines += ["", "**Hệ thống**"] + [f"- {x['ten']}: {x['mo_ta']}" for x in g["co_che_he_thong"]]
        lines += ["", "**Phục bút / bí ẩn**", md_list(a["phuc_but_va_bi_an"]), ""]
    lines += ["## Tóm tắt từng chương", ""]
    for r in load_chunk_results(out):
        for c in r["chuong"]:
            lines += [f"### Chương {c['so']}: {c['tieu_de']}", "", c["tom_tat"], ""]
    md = out / "tom_tat.md"
    md.write_text("\n".join(lines), encoding="utf-8")
    return md

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def parse_range(s: str | None):
    if not s:
        return None
    a, _, b = s.partition("-")
    return int(a), int(b or a)


def process_book(path: Path, args) -> None:
    book_name = path.stem
    out = Path(args.out) / re.sub(r"[^\w\-]+", "_", book_name)
    log(f"=== {book_name} ===")
    text = read_book_text(path)
    pdf_title = ""
    if path.suffix.lower() == ".pdf":
        # Header trang PDF thường là tên truyện in hoa ở dòng đầu mỗi trang
        first = [l.strip() for l in text.split("\n") if l.strip()][:5]
        pdf_title = first[0] if first else ""
    chapters = split_chapters(text, pdf_title)
    if not chapters:
        log("Không tách được chương nào (không thấy dòng 'Chương N: ...').")
        return
    rng = parse_range(args.chapters)
    if rng:
        chapters = {n: c for n, c in chapters.items() if rng[0] <= n <= rng[1]}
    nums = list(chapters)
    missing = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums))
    total_chars = sum(len(c["text"]) for c in chapters.values())
    chunks = make_chunks(chapters, args.chunk_chars, args.chunk_chapters)
    log(f"{len(chapters)} chương ({nums[0]}–{nums[-1]}), {total_chars:,} ký tự, {len(chunks)} chunk")
    if missing:
        log(f"Cảnh báo: thiếu {len(missing)} số chương (gộp vào chương trước hoặc lỗi định dạng), "
            f"ví dụ: {missing[:15]}")
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "chapters_index.json", {n: c["title"] for n, c in chapters.items()})

    if args.dry_run:
        est_in = total_chars / args.chars_per_token
        log(f"DRY RUN: ước lượng ~{est_in / 1e6:.1f}M token đầu vào cho bước MAP "
            f"(giả định {args.chars_per_token} ký tự/token - kiểm tra lại bằng count_tokens). "
            f"Đầu ra ước ~{len(chapters) * 450 / 1e6:.1f}M token.")
        return

    glossary = Path(args.glossary).read_text(encoding="utf-8") if args.glossary else ""
    system = build_system(book_name, glossary)
    claude = Claude(args.model, args.effort, args.max_tokens)

    failed = stage_map(claude, system, chapters, chunks, out, args.workers)
    if failed:
        log(f"{failed} chunk lỗi - chạy lại lệnh để xử lý tiếp; dừng trước bước gộp.")
        return
    results = [r for r in load_chunk_results(out)
               if not rng or (rng[0] <= r["_chuong_tu"] and r["_chuong_den"] <= rng[1])]
    entities = merge_entities(results)
    for kind, items in entities.items():
        write_json(out / "entities" / f"{kind}.json", items)
    log("Đã gộp thực thể: " + ", ".join(f"{k}={len(v)}" for k, v in entities.items()))

    if not args.skip_arcs:
        if stage_arcs(claude, system, results, out, args.arc_size, args.workers):
            log("Có hồi lỗi - chạy lại để tiếp tục.")
            return
    if args.profiles > 0:
        stage_profiles(claude, system, entities, out, args.profiles, args.workers)
    if not args.skip_arcs and not args.skip_book:
        stage_book(claude, system, out)
    md = export_markdown(out, book_name)
    u = claude.usage
    log(f"Hoàn tất {book_name}: {md}")
    log(f"Token lần chạy này: input={u['input']:,} output={u['output']:,} "
        f"cache_read={u['cache_read']:,} cache_write={u['cache_write']:,}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--drive-folder", help="ID thư mục Google Drive công khai (tải mọi .txt/.pdf)")
    src.add_argument("--input", nargs="+", help="Đường dẫn file .txt/.pdf có sẵn")
    ap.add_argument("--out", default="tom_tat", help="Thư mục kết quả (mặc định: tom_tat)")
    ap.add_argument("--download-dir", default="nguon_truyen", help="Nơi lưu file tải từ Drive")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--max-tokens", type=int, default=64000, help="Giới hạn token đầu ra mỗi lần gọi")
    ap.add_argument("--workers", type=int, default=4, help="Số request song song")
    ap.add_argument("--chunk-chars", type=int, default=45000, help="Số ký tự tối đa mỗi chunk")
    ap.add_argument("--chunk-chapters", type=int, default=10, help="Số chương tối đa mỗi chunk")
    ap.add_argument("--arc-size", type=int, default=100, help="Số chương mỗi hồi khi tổng kết")
    ap.add_argument("--profiles", type=int, default=60, help="Lập hồ sơ cho N nhân vật xuất hiện nhiều nhất (0 = bỏ)")
    ap.add_argument("--chapters", help="Chỉ xử lý một khoảng chương, ví dụ 1-50")
    ap.add_argument("--glossary", help="File text ghi chú bối cảnh/tên riêng đưa vào system prompt")
    ap.add_argument("--skip-arcs", action="store_true", help="Chỉ chạy MAP + gộp thực thể")
    ap.add_argument("--skip-book", action="store_true", help="Bỏ bước tổng quan cả bộ")
    ap.add_argument("--dry-run", action="store_true", help="Chỉ tách chương và ước lượng, không gọi API")
    ap.add_argument("--chars-per-token", type=float, default=2.2, help="Dùng cho ước lượng --dry-run")
    args = ap.parse_args()

    paths = (download_drive_folder(args.drive_folder, Path(args.download_dir)) if args.drive_folder
             else [Path(p) for p in args.input])
    for p in paths:
        process_book(p, args)


if __name__ == "__main__":
    main()
