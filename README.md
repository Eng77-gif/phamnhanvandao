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
Thư mục `slime/` chứa một tựa game hành động độc lập (một tệp HTML, không cần máy chủ), mở tại `/slime/` (ví dụ: https://phamnhan.click/slime/).
- Hấp thụ & Phân tích: Nuốt Chửng quái vật suy yếu (HP < 35%) hoặc nguyên liệu rơi trên đất vào "Dạ Dày". Học kỹ năng đặc trưng (Phun độc, Tàng Hình, Phân Thân Thuật, Băng Tiễn…) và tích lũy kháng tính (Nhiệt, Băng, Độc, Vật lý). Đại Hiền Giả phân tích điểm yếu Boss, đề xuất công thức chế tạo/dung hợp và tính tỉ lệ né.
- Tiến hóa phân nhánh: Tuyến Nguyên Tố (Slime Nước → Slime Băng/Lửa → Slime Nguyên Tố Cổ Đại) hoặc Tuyến Ma Vương (Ma Slime → Slime Hắc Ám → Slime Ma Vương, cần tích lũy Ma lực từ các trận chiến lớn).
- Biến hình: Dạng Khối (nhanh, nảy né đòn vật lý, bơi nhanh, chui qua lùm gai để lấy rương bí mật) và Dạng Nhân Hình (trang bị vũ khí, ma thuật mạnh hơn, dùng Kỹ năng Tối thượng, giao tiếp với loài người).
- Ban tên & Thu phục: tiêu tốn MP để đặt tên cho Goblin, Sói, Ogre, Thằn Lằn Nhân — chúng tiến hóa thành Hobgoblin, Lang Tinh, Quỷ Nhân, Long Nhân. Thiếu MP sẽ rơi vào Ngủ Đông.
- Lĩnh địa: phát triển Làng Goblin → Thị Trấn → Thành Phố → Quốc Gia Liên Minh Ma Vật; xây Nhà Ở, Nông Trại, Lò Rèn, Trạm Gác, Chợ, Tường Thành, Đại Sứ Quán; phân công thuộc hạ; buôn bán và ký hiệp ước với Vương Quốc Lam Thạch; phòng thủ trước Giáo Hội Thánh Quang.
- Dung hợp kỹ năng: ví dụ Tự Phục Hồi + Kháng Độc + Kháng Băng → Cơ Thể Bất Hoại; cuối game mở Kỹ năng Tối thượng: Thao Túng Không Gian, Ngưng Đọng Thời Gian, Pháp Tắc Cải Biến, Bạo Thực Chi Vương.
- Trùm cuối: Quỷ Vương Heo ở phương Bắc. Nuốt chửng nó để thức tỉnh.
- Điều khiển: WASD + chuột trên máy tính; joystick ảo + nút cảm ứng trên điện thoại. Tự động lưu bằng localStorage.
