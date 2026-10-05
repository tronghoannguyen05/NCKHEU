# CLAUDE.md: hướng dẫn cho các phiên làm việc với Claude

Đọc tệp này trước mọi việc. Sau đó đọc:
- `docs/analysis_plan.md`: phương pháp đã chốt, nguồn chân lý cho mã;
- `docs/review_notes.md`: các vấn đề đang mở.

## Đề tài

**Identified, Yet Excluded? Digital Identification and the Right to Social Protection for Marginalised Groups: Cross-Country Evidence.** Đề cương ở `docs/proposal.md`.

- Thiết kế: panel quốc gia–năm 2014–2024 và quốc gia–đợt Findex (2014, 2017, 2021, 2024), các nước thu nhập thấp và trung bình.
- Can thiệp: năm bắt đầu cấp định danh nền tảng số trên toàn quốc, mã hóa thủ công (`data/rollout/`, `docs/coding_protocol.md`).
- Kết quả: SDG 1.3.1 (H1 chính); tỷ lệ nhận trợ cấp nhà nước theo Findex, tổng và theo nhóm; khoảng cách trong nước (H2).
- Ước lượng chính: Callaway–Sant'Anna, đối chứng là các nước chưa triển khai, hồi quy kết quả với biến kiểm soát năm gốc, bootstrap theo quốc gia.
- Giả thuyết: H1 (trung bình), H2 (khoảng cách, Holm), H3 (bảo đảm quyền, Holm), H4 (thiết kế, thăm dò, BH).
- Công cụ: Python (`src/idsp/`); Rambachan–Roth bằng R (`r/honestdid.R`).

## Trạng thái (cập nhật khi thay đổi)

- [x] Repo, bộ ước lượng, dữ liệu giả lập, pipeline, kiểm thử (37 bài, đều qua).
- [x] Lệnh tải dữ liệu `python -m idsp.data.download` (mới kiểm tra với tệp giả lập).
- [x] Kế hoạch phân tích bản chốt (5/10/2026).
- [ ] Đối chiếu ngưỡng ý nghĩa thực tiễn 2 điểm phần trăm với số liệu ILO (`analysis_plan.md` mục 8).
- [ ] Đăng ký OSF (khuyến nghị) trước khi ghép kết quả với mốc triển khai.
- [ ] Mã hóa năm triển khai và luật bảo vệ dữ liệu; mã hóa kép 20%; khóa bằng tag `coding-freeze`.
- [ ] Tải dữ liệu, kiểm tra các mã VERIFY, dựng panel.
- [ ] Chạy `r/honestdid.R` trên kết quả giả lập (chưa từng chạy).
- [ ] Chạy trên dữ liệu thật, rồi viết bài.

## Quy tắc bắt buộc

1. **Không diễn giải vượt thiết kế.** Theo đề cương, kết quả là "mối liên hệ có điều kiện, vững với các kiểm tra". Chỉ nói về tác động nhân quả khi nêu kèm giả định xu hướng song song và giá trị phá vỡ Rambachan–Roth.
2. **Không đổi lựa chọn đã chốt** (mẫu, định nghĩa can thiệp, độ trễ, biến kiểm soát, nhóm đối chứng, họ kiểm định, danh mục độ vững) sau khi thấy kết quả. Mọi thay đổi ghi vào `docs/deviations.md`, kèm ngày và lý do, **trước** khi chạy lại.
3. **Mã hóa không xem kết quả.** Không mở dữ liệu kết quả hay đầu ra ước lượng khi đang mã hóa năm triển khai. Mỗi năm triển khai ở trạng thái `final` cần hai nguồn độc lập.
4. **Luôn báo cáo khoảng tin cậy 95%.** Không viết "gần có ý nghĩa". Không suy ra hai nhóm khác nhau chỉ vì một nhóm có ý nghĩa thống kê và nhóm kia không.
5. **TWFE chỉ để so sánh.** Kết luận H1–H4 dựa trên Callaway–Sant'Anna.
6. **Phân tích thăm dò** (H4, từng thành phần của chỉ số bảo đảm quyền) phải gắn nhãn thăm dò.
7. **Đầu ra từ dữ liệu giả lập** luôn mang nhãn SYNTHETIC và không bao giờ được trích dẫn như kết quả.
8. Không commit dữ liệu tải về (`data/raw`, `data/processed`). Dữ liệu mã hóa thủ công trong `data/rollout/` thì được commit.
9. Chạy `pytest` trước khi commit thay đổi mã.

## Văn phong

- Tài liệu làm việc viết bằng tiếng Việt học thuật, câu ngắn, mỗi câu một ý.
- Tài liệu đi kèm bộ dữ liệu công bố (`README.md`, `docs/codebook.md`, `docs/coding_protocol.md`) và bài báo viết bằng tiếng Anh.
- Hạn chế câu dùng dấu gạch ngang dài (—) để chen ý. Viết lại thành câu riêng, dấu phẩy, dấu hai chấm hoặc ngoặc đơn. Khoảng số dùng gạch nối (2014–2024).
- Trích dẫn theo APA 7.

## Bản đồ repo

| Đường dẫn | Nội dung |
|---|---|
| `docs/proposal.md` | Đề cương |
| `docs/analysis_plan.md` | Phương pháp đã chốt |
| `docs/coding_protocol.md` | Quy tắc mã hóa năm triển khai và luật bảo vệ dữ liệu |
| `docs/codebook.md` | Biến trong `data/processed/` |
| `docs/data_sources.md` | Cách tải từng nguồn |
| `docs/review_notes.md`, `docs/deviations.md` | Vấn đề đang mở; nhật ký lệch kế hoạch |
| `config/settings.yaml`, `config/sources.yaml` | Tham số phân tích; nguồn dữ liệu và mã chỉ tiêu |
| `data/rollout/` | Dữ liệu mã hóa thủ công (được commit) |
| `src/idsp/estimators/` | Callaway–Sant'Anna, Sun–Abraham, DID_M, TWFE, chẩn đoán, wild bootstrap |
| `src/idsp/data/` | Tải dữ liệu (`download.py`, `worldbank.py`), dựng panel |
| `src/idsp/pipeline.py` | Chạy toàn bộ phân tích |
| `r/honestdid.R` | Rambachan–Roth |
| `tests/` | Kiểm thử, gồm đối chiếu với `csdid` và `drdid` |

## Cách chạy

```
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,crosscheck]"
pytest                                   # kiểm thử
python -m idsp.pipeline --synthetic      # chạy thử trên dữ liệu giả lập
python -m idsp.data.download             # tải biến kiểm soát (WDI/WGI, OGHIST, V-Dem)
python -m idsp.data.download --outcomes  # thêm SDG 1.3.1 và Findex (sau coding-freeze)
python -m idsp.data.panel                # dựng panel (cần các tệp thủ công)
python -m idsp.pipeline                  # chạy trên dữ liệu thật
Rscript r/honestdid.R                    # Rambachan–Roth
```
