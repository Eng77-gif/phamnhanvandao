# Script tự động tóm tắt truyện cho thiết kế game

`tom_tat_truyen.py` đọc file truyện (.txt hoặc .pdf), tách theo chương rồi dùng Claude API để trích xuất dữ liệu chi tiết phục vụ làm game.

## Cài đặt

```bash
pip install -r tools/requirements-tom-tat.txt
# PDF: nên có pdftotext (apt install poppler-utils / brew install poppler), nếu không có thì script dùng pypdf
export ANTHROPIC_API_KEY=sk-ant-...
```

## Chạy

```bash
# 1) Kiểm tra tách chương + ước lượng token (không tốn tiền)
python tools/tom_tat_truyen.py --drive-folder 1jDH1IPViGl4MgKU2bCjXrtH4xV_bMhwn --dry-run

# 2) Chạy thử 30 chương đầu để xem chất lượng
python tools/tom_tat_truyen.py --input "nguon_truyen/Pham Nhan Tu Tien Full 2446c.txt" \
    --glossary tools/glossary-pham-nhan.txt --chapters 1-30 --profiles 5

# 3) Chạy toàn bộ cả 2 bộ trong thư mục Drive
python tools/tom_tat_truyen.py --drive-folder 1jDH1IPViGl4MgKU2bCjXrtH4xV_bMhwn \
    --glossary tools/glossary-pham-nhan.txt --out tom_tat
```

Bị ngắt giữa chừng thì chạy lại đúng lệnh cũ: phần nào đã xong (được cache trong `--out`) sẽ không bị gọi API lại.

## Kết quả (mỗi bộ một thư mục trong `--out`)

| File | Nội dung |
|---|---|
| `chunks/*.json` | Mỗi nhóm ~10 chương: tóm tắt **từng chương**, sự kiện (kèm gợi ý game), nhân vật, địa điểm, vật phẩm, công pháp/thần thông, yêu thú, thế lực, lore, cảnh giới nhân vật chính |
| `entities/*.json` | Gộp toàn bộ nhân vật / địa điểm / vật phẩm / công pháp / yêu thú / thế lực, sắp theo số lần xuất hiện, có danh sách đoạn chương xuất hiện |
| `arcs/*.json` | Mỗi ~100 chương: tóm tắt hồi 1.200–2.500 chữ, dòng sự kiện, **main quest, side quest, boss, cơ chế, cutscene**, phục bút |
| `profiles/*.json` | Hồ sơ đầy đủ cho N nhân vật quan trọng nhất (tiến trình cảnh giới, pháp bảo, quan hệ, gợi ý kỹ năng/thoại) |
| `tong_quan.json` | Tổng quan cả bộ, hệ thống cảnh giới, giới diện, đề xuất cấu trúc game |
| `tom_tat.md` | Bản đọc được: tổng quan → từng hồi → tóm tắt từng chương |

## Tuỳ chọn hay dùng

- `--model` (mặc định `claude-opus-5-5`). Chi phí ước lượng cho cả 2 bộ (~19M token đầu vào ở bước MAP) với Opus 5.5 là khoảng 100–150 USD; `--model claude-haiku-5-5` rẻ hơn rất nhiều nhưng kém chính xác hơn. Hãy chạy thử `--chapters 1-30` với từng model để so.
- `--effort low|medium|high` – độ kỹ khi suy luận (mặc định `medium`).
- `--workers 4` – số request song song (giảm nếu bị rate limit).
- `--chunk-chars`, `--chunk-chapters` – kích thước mỗi lần gửi; nhỏ hơn thì chi tiết hơn nhưng tốn hơn.
- `--arc-size 100` – số chương mỗi hồi.
- `--profiles 60` – số nhân vật được lập hồ sơ.
- `--skip-arcs` – chỉ trích xuất dữ liệu từng chương + gộp thực thể.

## Lưu ý về file nguồn

- TXT thiếu tiêu đề các chương 25, 264, 325, 404, 428, 434, 505, 746, 1545, 1877, 2061, 2247, 2285 (nội dung nếu có sẽ nằm trong chương liền trước).
- PDF Tiên Giới Thiên thiếu chương 507 và 1383.
