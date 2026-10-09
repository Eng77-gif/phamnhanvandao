Phàm Nhân Vấn Đạo — Tam Giới Tu Tiên
Phàm Nhân Vấn Đạo là một tựa game nhập vai tĩnh (text-based/incremental RPG) chạy trực tiếp trên trình duyệt, lấy cảm hứng sâu sắc từ bộ đại thuyết tiên hiệp nổi tiếng Phàm Nhân Tu Tiên của tác giả Vong Ngữ.
Người chơi sẽ bắt đầu từ một phàm nhân với tư chất bình thường (hoặc dị bẩm), từng bước thu thập tài nguyên, luyện đan, rèn khí, khám phá bí cảnh và vượt qua các thiên kiếp để phi thăng từ Nhân Giới lên Linh Giới, và cuối cùng là Tiên Giới.

✨ Tính năng nổi bật
Hệ thống Cảnh giới & Phi thăng: Trải dài từ Luyện Khí Kỳ cho đến Đạo Tổ. Đột phá cảnh giới cần có linh lực, thọ nguyên và tài nguyên tương ứng, đi kèm với các sự kiện thiên kiếp khắc nghiệt.
Bản đồ Tam Giới nguyên tác: Khám phá các địa danh quen thuộc như Hư Thiên Điện, Địa Uyên, Tẩy Linh Trì, Hôi Giới, Tích Không Giới hay Man Hoang Tiên Vực.
Hệ thống Nghề phụ (Nghề Phủ): Luyện đan, Luyện khí, Trận pháp. Yêu cầu nguyên liệu đa dạng (Linh thảo, Khoáng thạch, Yêu đan...) để chế tác ra Liệu Thương Đan, Pháp bảo, hoặc Khôi lỗi.
Thể tu & Pháp quyết: Nổi bật với hệ thống luyện thể Thiên Sát Trấn Ngục Công gồm 1080 huyền khiếu.
Tương tác NPC (Nhân mạch): Gặp gỡ, kết giao hoặc kết thù với các nhân vật từ nguyên tác như Nam Cung Uyển, Tề Vân Tiêu, Băng Phượng, Vương Thiền, hay Cực Âm Tổ Sư. Thanh hảo cảm ảnh hưởng trực tiếp đến kết quả tương tác.
Danh hiệu & Thành tựu: 16 danh hiệu thành tựu vinh dự (như Lão Ma, Thanh Trúc Kiếm Chủ, Trảm Ma Tôn, Đạo Tổ...) để thể hiện đẳng cấp.
Quản lý Thọ nguyên & Thời gian: Game mô phỏng sự khắc nghiệt của thời gian. Nếu không kịp đột phá trước khi cạn kiệt thọ nguyên, nhân vật sẽ tọa hóa (game over).

🛠 Công nghệ & Kiến trúc
Dự án này là một Single-Page Application (SPA) hoàn toàn tĩnh, không cần máy chủ backend, được xây dựng theo triết lý "Everything in one file" (Tất cả trong một tệp):
HTML5: Cấu trúc ngữ nghĩa, tích hợp sẵn hệ thống SVG icons nét mảnh (<symbol>) giúp tối ưu băng thông và hiển thị sắc nét trên mọi thiết bị.
CSS3 (Vanilla):
Sử dụng CSS Variables để quản lý theme, màu sắc chủ đạo (Jade, Gold, Blood).
Hệ thống bố cục Flexbox/Grid đáp ứng (Responsive) tốt cho cả Mobile và Desktop.
Hiệu ứng chuyển động (Animations) mượt mà cho các thông báo, thanh máu, và hiệu ứng thăng cấp.
JavaScript (Vanilla):
Xử lý toàn bộ logic game: Vòng lặp thời gian, tính toán chỉ số, chiến đấu, RNG (random number generation) cho rớt đồ và đột phá.
Sử dụng localStorage để tự động lưu/tải tiến trình chơi một cách liền mạch.

🫧 Game mới: Chuyển Sinh Thành Slime
Thư mục `slime/` chứa một tựa game độc lập (mỗi bản là một tệp HTML, không cần máy chủ), dựa trên light novel *Tensei Shitara Slime Datta Ken*.

**Bản chính — Text RPG + Xây dựng Quốc gia** (`/slime/`, ví dụ https://phamnhan.click/slime/)
- Cốt truyện 10 chương theo nguyên tác: Hang Phong Ấn & Veldora → Làng Goblin & Hắc Lang → Vương Quốc Dwargon (Kaijin) → Shizu & Ifrit → Quỷ Nhân (Benimaru, Shuna, Shion, Souei, Hakurou, Kurobe) → Orc Disaster Geld → Ma Vương Milim & Charybdis → Kiếm Vương Gazel & Blumund → Hinata & Lễ Hội Thu Hoạch → Walpurgis & Clayman.
- Kẻ Săn Mồi & Đại Hiền Giả: Nuốt Chửng ma vật để phân tích từng phần trăm và học kỹ năng (Thủy Nhẫn, Tơ Thép, Độc Tức, Hắc Lôi, Hắc Viêm…), tích lũy kháng tính (Kháng Nhiệt Biến, Kháng Tấn Công Vật Lý, Kháng Đau, Kháng Độc…) tới Vô Hiệu Hóa. Đại Hiền Giả dự đoán đòn của địch, tính tỉ lệ né, phân tích điểm yếu Boss, đề xuất chế tạo & dung hợp.
- Mô Phỏng: Dạng Slime, Nhân Hình (từ Shizu), Hắc Lang, Dơi Khổng Lồ, Thằn Lằn Giáp — mỗi dạng có ưu nhược điểm riêng.
- Ban tên: Rigurd, Gobta, Ranga, các Quỷ Nhân, Geld, Gabiru… thuộc hạ tiến hóa; tiêu tốn Ma tố và có thể khiến ngài rơi vào Ngủ Đông. Hành Lang Linh Hồn chia sẻ kỹ năng của thuộc hạ.
- Lĩnh địa: từ Làng Goblin tới Liên Bang Jura Tempest; phân công hàng nghìn Hobgoblin, High Orc, Long Nhân vào 8 ngành nghề; 11 công trình; thông thương & hiệp ước với Dwargon, Blumund; sự kiện văn bản hằng ngày.
- Dung hợp kỹ năng & Kỹ năng Tối thượng: Trí Tuệ Chi Vương Raphael, Bạo Thực Chi Vương Beelzebuth, Thệ Ước Chi Vương Uriel, Bạo Phong Chi Vương Veldora, Thần Chi Nộ: Megiddo…
- Hai con đường thức tỉnh: Ma Vương Thực Thụ (Lễ Hội Thu Hoạch, như nguyên tác) hoặc Tinh Linh Hóa (khế ước Ifrit, Sylphide, Undine, Gnome).

**Bản hành động** (`/slime/hanh-dong/`): game hành động thời gian thực điều khiển bằng bàn phím/cảm ứng.
