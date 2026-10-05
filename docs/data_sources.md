# Nguồn dữ liệu và cách tải

Tất cả nguồn đều công khai hoặc miễn phí khi đăng ký. Giữ bản tải gốc kèm ngày tải trong `data/raw/original/`, rồi chuyển sang tệp gọn theo đúng các cột ghi trong `config/sources.yaml`, lưu vào `data/raw/manual/`. Những chỗ ghi **VERIFY** phải được kiểm tra trên trang của nhà cung cấp trước lần chạy thật đầu tiên. Mã trong repo chưa từng chạy trên dữ liệu thật, vì môi trường phát triển không truy cập được các trang này.

## 1. Tải tự động: World Bank API (WDI, WGI)

```
python -m idsp.data.worldbank
```

Lệnh này tạo `data/raw/wb_<tên>.csv` (cột `iso3, year, value`) cho các chỉ tiêu trong `config/sources.yaml`:
- GDP bình quân PPP, dân số đô thị, thuê bao di động, dân số;
- số người chết trong xung đột (UCDP, qua WDI);
- hai biến placebo;
- tỷ lệ có tài khoản;
- WGI.

**VERIFY:** mã WGI (`VA.EST`, `RL.EST`, nguồn 3) có thể đã đổi trong lần sửa đổi WGI năm 2024. Kiểm tra trên DataBank. Nếu mã đổi, sửa `config/sources.yaml`.

Giấy phép: CC BY 4.0.

## 2. Tải thủ công

| Tệp gọn (`data/raw/manual/`) | Cột | Nguồn và cách lấy |
|---|---|---|
| `income_classification.csv` | iso3, country, region, income_group | Tệp `OGHIST.xlsx` (World Bank historical classification by income). Lấy cột FY2015 và giữ nguyên ký hiệu L, LM, UM, H |
| `sdg131.csv` | iso3, year, sdg131_total | ILOSTAT, chỉ tiêu SDG 1.3.1 "Proportion of population covered by at least one social protection benefit", tổng chung (không tách giới). **VERIFY** mã chỉ tiêu. Giữ lại cột ghi chú loại ước lượng (số liệu quốc gia hay ước lượng mô hình) trong bản gốc |
| `sp_spending.csv` | iso3, year, sp_spending | ILO World Social Protection Database: chi bảo trợ xã hội công không gồm y tế, % GDP |
| `findex_transfers.csv` | iso3, wave, transfer_total, transfer_female, transfer_male, transfer_poor40, transfer_rich60, transfer_rural, transfer_urban | Global Findex Database 2025 (bản dữ liệu cấp quốc gia, gồm các đợt trước). **VERIFY** mã câu hỏi từng đợt và ghi vào `docs/codebook.md`. Đơn vị là phần trăm (0–100) |
| `vdem.csv` | iso3, year, v2x_cspart, v2csreprss | V-Dem Country-Year dataset (bản mới nhất). `country_text_id` là mã ISO3. Giấy phép CC BY-SA 4.0 |
| `id4d.csv` (tùy chọn) | iso3, year, id_ownership | ID4D Global Dataset. Dùng để kiểm tra bước đầu: triển khai có đi kèm tỷ lệ sở hữu định danh cao hơn không |

## 3. Mã hóa thủ công

- `data/rollout/rollout_coding.csv`: năm triển khai và đặc điểm thiết kế (`docs/coding_protocol.md`).
- `data/rollout/rollout_second_coder.csv`: mã hóa độc lập lần hai cho 20% số nước.
- `data/rollout/dp_law_coding.csv`: năm luật bảo vệ dữ liệu cá nhân có hiệu lực. Bảng của UNCTAD chỉ cho biết tình trạng hiện tại, nên năm phải lấy từ chính văn bản luật.

## 4. Dựng panel

```
python -m idsp.data.panel
```

Lệnh này kiểm tra tệp mã hóa, khóa trùng lặp và phạm vi 0–100. Nó dừng lại nếu thiếu tệp hoặc tệp mã hóa còn lỗi.

## 5. Giấy phép khi công bố bộ dữ liệu

- Bộ dữ liệu năm triển khai do nhóm tự mã hóa, nên có thể công bố riêng (đề xuất CC BY 4.0).
- Nếu công bố kèm biến V-Dem, phần đó phải theo CC BY-SA 4.0.
- Các biến World Bank và ILO ghi rõ nguồn theo CC BY 4.0.
