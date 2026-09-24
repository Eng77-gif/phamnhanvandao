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
