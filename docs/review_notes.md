# Nhận xét đề cương và các vấn đề đang mở

Xếp theo mức ưu tiên. Đánh dấu [x] khi đã xử lý và ghi vị trí đã sửa. Các quyết định đã chốt nằm ở `docs/analysis_plan.md`. Tệp này chỉ giữ những điểm còn phải kiểm tra, hoặc phải viết vào phần hạn chế của bài.

## A. Ảnh hưởng đến phạm vi của kết luận

- [ ] **A1. Nhiều nước triển khai trước 2014 bị loại.** Các nước này không có kỳ trước can thiệp, nên kết quả chỉ nói về các nước triển khai 2015–2024. Ấn Độ là một ví dụ, mà Ấn Độ lại là nguồn của phần lớn bằng chứng hiện có. Bài phải nói rõ điều này. Có thể cân nhắc mở rộng cửa sổ về trước nếu SDG 1.3.1 có số liệu cho các năm trước 2014, hoặc thêm đợt Findex 2011 nếu câu hỏi tương đương. Cả hai phải ghi vào `deviations.md` trước khi chạy.
- [ ] **A2. Ít nước chưa triển khai đến 2024.** Các ô cuối giai đoạn có ít đối chứng. Các nước không bao giờ triển khai có thể khác biệt hệ thống (dễ tổn thương, xung đột). Kiểm tra R1 và số nước trong từng ô (`n_control` trong `H1_*_attgt.csv`) phải được đọc cùng nhau.
- [ ] **A3. COVID-19.** Năm 2020–2021 nhiều nước mở rộng chi trả khẩn cấp, và các nước có định danh số có thể mở rộng nhanh hơn. Đó là một dạng hiệu ứng không đồng nhất theo thời gian lịch, có thể đọc nhầm thành hiệu ứng của việc triển khai. Cần đọc cùng nhau: cách gộp theo thời gian lịch, kiểm tra R7 (≤ 2019), và với Findex 2021 là khả năng tách các khoản chi trả liên quan đến COVID.
- [ ] **A4. Số nước thực tế.** Đề cương nêu khoảng 120 nước. Sau khi loại các nước đã triển khai từ trước, các nước thiếu số liệu kết quả và thiếu biến kiểm soát, số nước dùng được có thể thấp hơn nhiều. Báo cáo số nước theo từng nhóm triển khai và nêu độ rộng khoảng tin cậy ngay ở phần kết quả chính.

## B. Đo lường

- [ ] **B1. SDG 1.3.1** thiếu nhiều năm. Một phần số liệu là ước lượng mô hình của ILO, không phải số liệu quốc gia. Nếu dữ liệu gốc có cột phân loại, chạy thêm một kiểm tra chỉ dùng quan sát là số liệu quốc gia (ghi `deviations.md`).
- [ ] **B2. Findex** đổi cách hỏi về các khoản nhận từ nhà nước giữa các đợt. Ghi mã câu hỏi từng đợt vào `docs/codebook.md` và kiểm tra tính so sánh được trước khi chạy.
- [ ] **B3. Nhóm nông thôn/thành thị** trong Findex có thể không có đủ ở mọi đợt. Nếu thiếu, `gap_residence` bị bỏ khỏi họ H2, và Holm tính trên hai khoảng cách. Phải ghi vào `deviations.md` trước khi chạy.
- [ ] **B4. Kiểm tra bước đầu:** dùng ID4D để xem việc triển khai có đi kèm tỷ lệ sở hữu định danh cao hơn không. Đây là cách kiểm tra rằng mốc mã hóa phản ánh một thay đổi thật. Nên làm như phân tích mô tả.
- [ ] **B5. Ngưỡng ý nghĩa thực tiễn** (2 điểm phần trăm) phải được đối chiếu với số liệu ILO rồi chốt trước khi xem kết quả (`analysis_plan.md` mục 8).

## C. Suy luận

- [ ] **C1.** Với khoảng 80 nước, bootstrap theo cụm là đủ. Các phân tích tách nhóm (H3, H4) có thể chỉ còn 30–40 nước mỗi nhóm. Khi đó nên đọc thêm p wild bootstrap từ đặc tả TWFE, và trình bày các phân tích tách nhóm là thận trọng.
- [ ] **C2. Kỳ vọng trước triển khai:** việc vận động đăng ký có thể diễn ra trước năm mở cấp đại trà. Có thể thêm kiểm tra `anticipation = 1` (ghi `deviations.md`).
- [ ] **C3.** Kiểm tra cuối: chạy lại đặc tả chính bằng R `did` trên mẫu cân bằng.

## D. Thủ tục

- [ ] **D1. Đăng ký kế hoạch** trên OSF trước khi ghép dữ liệu kết quả với mốc triển khai. Dữ liệu kết quả là công khai, nên phải nói rõ tác giả đã xem những gì trước khi đăng ký, ví dụ các con số mô tả trong báo cáo ILO và Findex.
- [ ] **D2. Mã hóa không xem kết quả** và khóa bằng tag `coding-freeze` (`coding_protocol.md` mục 1).
- [ ] **D3. Tìm kiếm tài liệu có hệ thống** (Scopus, Web of Science) để xác nhận khoảng trống, như đề cương mục 2 đã hứa.
- [ ] **D4.** Kiểm tra lại tài liệu tham khảo của đề cương trước khi nộp. Ví dụ: bản NBER năm 2020 của Muralidharan và cộng sự đã có bản công bố chính thức hay chưa.

## E. Kiểm tra mã trước lần chạy thật đầu tiên

- [ ] E1. Kiểm tra các mã **VERIFY** trong `config/sources.yaml` và `docs/codebook.md`.
- [ ] E2. Chạy `Rscript r/honestdid.R` trên kết quả giả lập. Script này chưa từng chạy, vì môi trường phát triển không có R.
- [ ] E3. Chạy `python -m idsp.data.worldbank`. Hàm tải chỉ mới được kiểm tra với phản hồi giả lập.
