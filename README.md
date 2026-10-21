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

🌏 Thế Giới Trực Tuyến (v1.73)
Bản đồ 2D: mỗi địa vực là một bản đồ riêng, đi lại bằng chạm/chuột hoặc WASD, thấy đạo hữu khác di chuyển theo thời gian thực (Supabase Realtime Presence). Yêu thú lang thang trong vùng săn, chạm để giao chiến; giữa thành có Lôi Đài, Bang Hội Đường, Truyền Tống Trận, Phường Thị.
Lôi Đài: khiêu chiến người đang trực tuyến, máy chủ phân thắng bại theo thực lực, có điểm và bảng xếp hạng.
Bang Hội: người chơi tự khai lập, góp quỹ nâng cấp, phong trưởng lão, kênh chat riêng.
Kênh chat thế giới, lời nói hiện thành bong bóng trên bản đồ.

Cài phần máy chủ: mở Supabase ▸ SQL Editor và chạy tệp supabase/world_online.sql (chỉ thêm bảng/hàm mới). Khi chưa chạy, bản đồ 2D và chat vẫn hoạt động qua Realtime (chat không lưu lịch sử); Lôi Đài và Bang Hội cần tệp SQL này.

🎨 Đồ họa pixel-art (v1.74)
Bản đồ Thế Giới dùng sprite sheet trong assets/sprites/ (nhân vật 4 hướng × đứng/đi 4 khung/ra chiêu, yêu thú, ô nền, cây, nhà, truyền tống trận, hiệu ứng chém).
Sinh lại: node tools/sprites/build.js (cần Playwright). Xem trước toàn bộ: tools/sprites/preview.png.
Thay bằng tranh PixelLab: xuất cùng kích thước khung và thứ tự hàng/cột như mô tả đầu tệp tools/sprites/pixel-gen.js rồi ghi đè tệp PNG tương ứng — không cần sửa code.
