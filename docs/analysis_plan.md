# Kế hoạch phân tích (bản chốt ngày 5/10/2026)

Tệp này chốt phương pháp của đề cương "Identified, Yet Excluded?" (`docs/proposal.md`) thành các quyết định có thể chạy ngay. Mã trong `src/idsp/` và tham số trong `config/settings.yaml` phải khớp với tệp này.

- Thứ tự ưu tiên khi có mâu thuẫn: **bản đăng ký OSF (nếu có) > tệp này > đề cương**.
- Sau khi đăng ký hoặc sau khi đã ghép dữ liệu kết quả với mốc triển khai, mọi thay đổi phải ghi vào `docs/deviations.md` **trước** khi chạy lại.
- Những chỗ tệp này khác đề cương được liệt kê ở mục 12, kèm lý do.

---

## 0. Tóm tắt các quyết định

| Hạng mục | Quyết định |
|---|---|
| Đơn vị, thời gian | Quốc gia–năm 2014–2024 (SDG 1.3.1); quốc gia–đợt Findex 2014, 2017, 2021, 2024 |
| Khung mẫu | Các nước thu nhập thấp, trung bình thấp, trung bình cao theo phân loại của World Bank năm tài khóa 2015 (công bố 7/2014), cố định tại thời điểm gốc |
| Can thiệp | Năm bắt đầu cấp định danh nền tảng số (sinh trắc hoặc điện tử) trên toàn quốc, mã hóa thủ công, có tính hấp thụ (đã triển khai thì không quay lại) |
| Độ trễ | Năm: được coi là đã triển khai từ chính năm triển khai. Findex: đã triển khai ở đợt w nếu năm triển khai ≤ w − 1 |
| Kết quả chính H1 | SDG 1.3.1 (tỷ lệ dân số được ít nhất một chế độ bảo trợ xã hội); kết quả phụ: tỷ lệ người trưởng thành nhận trợ cấp hoặc lương hưu của nhà nước (Findex) |
| Ước lượng chính | Callaway và Sant'Anna (2021), nhóm đối chứng là các nước chưa triển khai, kỳ gốc thay đổi, hồi quy kết quả (OR) với biến kiểm soát đo tại năm gốc |
| Đại lượng báo cáo chính | ATT tổng thể theo cách gộp theo nhóm (group aggregation), đơn vị điểm phần trăm |
| Suy luận | Bootstrap theo quốc gia, 999 lần; khoảng tin cậy 95%; dải đồng thời cho event study |
| H2 | ATT trên khoảng cách trong nước: nam − nữ, giàu 60% − nghèo 40%, thành thị − nông thôn; hiệu chỉnh Holm |
| H3 | Ước lượng Callaway–Sant'Anna tách theo chỉ số bảo đảm quyền đo năm 2014 (chia theo trung vị); kiểm định hiệu cao − thấp; hiệu chỉnh Holm; hồi quy TWFE có tương tác theo đề cương chỉ để so sánh |
| H4 | Thăm dò: tách theo việc bắt buộc xác thực sinh trắc khi nhận trợ cấp; hiệu chỉnh BH |
| Độ nhạy xu hướng song song | Kiểm định Wald trước can thiệp, event study kỳ gốc cố định, Rambachan–Roth (độ lớn tương đối M̄ ∈ {0; 0,5; 1; 1,5; 2}) |
| Kết quả giả (placebo) | Tỷ lệ tiếp cận điện, tỷ lệ đất nông nghiệp |
| Bộ ước lượng so sánh | Sun–Abraham, DID_M của de Chaisemartin–D'Haultfœuille, TWFE tĩnh và event study, chẩn đoán trọng số âm của TWFE |

---

## 1. Đại lượng ước lượng và cách diễn giải

**Đại lượng nhóm–thời điểm.** ATT(g,t) là chênh lệch kỳ vọng về độ bao phủ tại năm t giữa các nước triển khai năm g và chính các nước đó nếu chưa triển khai, theo giả định xu hướng song song có điều kiện với các nước chưa triển khai:

ATT(g,t) = E[Y_t − Y_{g−1} | G = g] − E[Y_t − Y_{g−1} | D_t = 0, G ≠ g]

(công thức của đề cương mục 6; khi có biến kiểm soát, số hạng thứ hai được thay bằng giá trị dự báo từ hồi quy trên nhóm đối chứng).

**Đại lượng báo cáo chính.** θ = Σ_g P(G = g) · θ(g), trong đó θ(g) là trung bình của ATT(g,t) qua các năm sau triển khai của nhóm g. Đây là cách gộp Callaway và Sant'Anna (2021) khuyến nghị làm con số tổng hợp. Các cách gộp đơn giản, theo thời gian lịch và trung bình event study được báo cáo kèm.

**Quần thể.** Đại lượng chỉ áp dụng cho các nước triển khai trong 2015–2024 (dữ liệu năm) hoặc trước các đợt 2017, 2021, 2024 (Findex). Các nước đã triển khai trước 2014, như Ấn Độ với Aadhaar, không có kỳ trước can thiệp nên bị loại khỏi ước lượng. Số nước bị loại được báo cáo trong mọi bảng. Kết quả vì vậy không nói gì về các hệ thống triển khai sớm.

**Cách diễn giải.** Theo đề cương, kết quả được trình bày là "mối liên hệ có điều kiện, vững với các kiểm tra", không phải tác động nhân quả chắc chắn. Chỉ được diễn giải theo nghĩa nhân quả kèm giả định xu hướng song song, và luôn kèm kết quả Rambachan–Roth.

---

## 2. Mẫu

1. **Khung mẫu:** các nước có nhóm thu nhập L, LM hoặc UM theo phân loại World Bank năm tài khóa 2015. Mẫu cố định tại năm gốc, nên một nước lên nhóm thu nhập cao sau 2014 vẫn ở trong mẫu. Lý do: chọn mẫu theo nhóm thu nhập sau triển khai là chọn mẫu theo một biến có thể chịu ảnh hưởng của chính quá trình phát triển đi kèm định danh số.
2. **Không loại trước** nước nào vì quy mô dân số hay vì xung đột. Các nước không có dữ liệu kết quả tự rơi khỏi các ô ATT(g,t) tương ứng.
3. **Nước đã triển khai từ trước** (năm triển khai ≤ 2014 với dữ liệu năm; ≤ 2013 với Findex theo quy tắc độ trễ) chỉ xuất hiện trong thống kê mô tả.
4. Mọi bảng kết quả báo cáo số nước theo nhóm triển khai (`output/tables/cohorts_annual.csv`, `cohorts_waves.csv`).

---

## 3. Biến

### 3.1. Can thiệp

- `rollout_year`: năm đầu tiên một hệ thống định danh nền tảng (foundational ID) dạng số, sinh trắc hoặc chip điện tử, **bắt đầu cấp trên phạm vi toàn quốc** cho dân cư. Thí điểm cấp tỉnh, đăng ký cử tri và định danh chuyên ngành (chỉ dùng cho một chương trình) không được tính. Quy tắc chi tiết ở `docs/coding_protocol.md`.
- `rollout_year_alt`: năm văn bản pháp lý thành lập hệ thống có hiệu lực. Chỉ dùng cho kiểm tra độ vững.
- Can thiệp có tính hấp thụ: một nước đã triển khai thì giữ trạng thái đã triển khai cho các năm sau.
- **Độ trễ:**
  - với dữ liệu năm, nhóm g = `rollout_year`;
  - với Findex, nhóm là đợt w đầu tiên thỏa `rollout_year + 1 ≤ w`. Vì vậy các nước triển khai 2014–2016 thuộc nhóm 2017, 2017–2020 thuộc nhóm 2021, 2021–2023 thuộc nhóm 2024, và năm 2024 được coi là chưa triển khai trong cửa sổ quan sát.
  - Lý do của độ trễ một năm: đợt khảo sát cùng năm triển khai thường được thực địa trước khi việc cấp thẻ có tác dụng.
- **Đặc điểm thiết kế** (H4, mã hóa tại thời điểm triển khai):
  - `biometric_auth_mandatory_benefits`: bắt buộc xác thực sinh trắc khi nhận trợ cấp;
  - `non_biometric_fallback`: có phương án thay thế không sinh trắc;
  - `linked_social_registry`: gắn với cơ sở dữ liệu an sinh;
  - `donor_financed`: có dự án tài trợ của nhà tài trợ cho việc triển khai.

### 3.2. Kết quả

| Biến | Định nghĩa | Nguồn | Dùng cho |
|---|---|---|---|
| `sdg131_total` | % dân số được ít nhất một chế độ bảo trợ xã hội (SDG 1.3.1) | ILO WSPD / ILOSTAT | H1 chính, H3 |
| `transfer_total` | % người từ 15 tuổi nhận trợ cấp hoặc lương hưu của nhà nước trong 12 tháng | Global Findex | H1 phụ, H3 |
| `transfer_female`, `transfer_male`, `transfer_poor40`, `transfer_rich60`, `transfer_rural`, `transfer_urban` | Như trên, theo nhóm | Global Findex | H2 |
| `gap_sex`, `gap_income`, `gap_residence` | Nam − nữ; giàu 60% − nghèo 40%; thành thị − nông thôn | Tính từ Findex | H2 |
| `elec_access` | % dân số có điện | WDI | Placebo |
| `agri_land` | % diện tích là đất nông nghiệp | WDI | Placebo |

Ghi chú:
- Câu hỏi Findex về nhận tiền từ nhà nước có thay đổi cách hỏi giữa các đợt. Biến `transfer_total` phải được dựng theo một định nghĩa thống nhất qua bốn đợt, và cách dựng được ghi trong `docs/codebook.md` trước khi chạy.
- Placebo được chọn vì hai lý do. Tỷ lệ tiếp cận điện phát hiện việc định danh số trùng thời điểm với một đợt đầu tư hạ tầng hoặc tăng năng lực nhà nước nói chung. Đất nông nghiệp không có cơ chế hợp lý nào liên quan đến định danh số.

### 3.3. Biến kiểm soát (đo tại năm gốc)

Giá trị là quan sát gần nhất trong khoảng 2010–2014. Chỉ dùng giá trị năm gốc, không dùng biến thay đổi theo thời gian, vì chúng có thể chịu ảnh hưởng của chính việc triển khai.

| Biến | Định nghĩa | Lý do |
|---|---|---|
| `log_gdppc_2014` | log GDP bình quân đầu người theo PPP | Năng lực tài khóa và xu hướng mở rộng an sinh |
| `urban_2014` | % dân số đô thị | Chi phí tiếp cận dân cư |
| `mobile_2014` | Thuê bao di động trên 100 dân | Mức sẵn sàng số; dự báo cả thời điểm triển khai lẫn xu hướng chi trả số |
| `conflict_2010_2014` | 1 nếu có ít nhất 25 người chết trong xung đột vũ trang ở một năm bất kỳ trong 2010–2014 (UCDP qua WDI) | Xung đột ảnh hưởng cả việc triển khai lẫn chi trả |
| `sp_spending_2014` | Chi bảo trợ xã hội công, % GDP (không gồm y tế) | Chỉ trong đặc tả mở rộng, vì số liệu thiếu nhiều |

Không đưa vào mô hình chính:
- **tỷ lệ có tài khoản và mức phổ cập di động theo từng năm**, vì đây là kênh trung gian (định danh → mở tài khoản, đăng ký SIM);
- **tài trợ của nhà tài trợ cho dự án định danh**, vì đây là một phần của chính gói can thiệp. Thay vào đó có một kiểm tra độ vững loại các nước được tài trợ.

### 3.4. Biến điều tiết

- **Chỉ số bảo đảm quyền** (`safeguard`): trung bình các điểm chuẩn hóa (z) của bốn thành phần đo năm 2014:
  - có luật bảo vệ dữ liệu cá nhân đang có hiệu lực (0/1, năm hiệu lực mã hóa thủ công);
  - WGI Voice and Accountability;
  - WGI Rule of Law;
  - V-Dem civil society participation index (`v2x_cspart`).
- `high_safeguard` = 1 nếu chỉ số lớn hơn trung vị của mẫu.
- **Lý do đo năm 2014 thay vì "tại thời điểm triển khai" như đề cương:** đo tại thời điểm triển khai không xác định được cho nhóm đối chứng chưa triển khai. Nó cũng có thể chịu ảnh hưởng của chính quá trình triển khai, ví dụ khi luật bảo vệ dữ liệu được ban hành cùng hệ thống định danh. Năm 2014 có trước triển khai với mọi nhóm trong cửa sổ ước lượng.

---

## 4. Ước lượng

### 4.1. Đặc tả chính (H1)

`idsp.estimators.cs.att_gt` với:
- `control_group = "notyettreated"`: nhóm đối chứng gồm các nước chưa triển khai tại cả t và kỳ gốc, kể cả các nước không triển khai trong cửa sổ;
- `base_period = "varying"`: ô sau can thiệp so với g − 1; ô trước can thiệp là chênh lệch ngắn t − 1 → t, dùng cho kiểm định trước can thiệp;
- hồi quy kết quả của Sant'Anna và Zhao (2020) với bốn biến kiểm soát năm gốc ở mục 3.3;
- `anticipation = 0`;
- **panel không cân bằng:** mỗi ô ATT(g,t) dùng các nước có quan sát ở cả t và kỳ gốc. Cách này giữ nguyên phép lấy sai phân trong cùng một nước. Nó khác lựa chọn mặc định của gói R `did`, vốn loại các nước thiếu bất kỳ năm nào, hoặc chuyển sang ước lượng lát cắt lặp. Với SDG 1.3.1 thiếu nhiều năm, lựa chọn mặc định đó sẽ làm mất phần lớn mẫu hoặc mất phép sai phân trong nước.

Bộ ước lượng đã được đối chiếu với các gói tham chiếu (`tests/test_estimators.py`):
- trường hợp không có biến kiểm soát khớp chính xác với gói `csdid` (bản Python của R `did`), cho cả hai nhóm đối chứng;
- hồi quy kết quả khớp từng ô với `drdid.reg_did_panel`.

Gói `csdid` 0.4.2 cho số khác khi có biến kiểm soát, nên bước kiểm tra cuối nên chạy lại bằng R `did` trên mẫu cân bằng.

### 4.2. Cách gộp và event study

- Con số chính: ATT tổng thể theo cách gộp theo nhóm.
- Event study, kỳ gốc thay đổi: dùng cho kiểm định Wald trước can thiệp.
- Event study, kỳ gốc cố định (e = −1): dùng cho hình và cho Rambachan–Roth.
- Event study cân bằng, chỉ các nhóm quan sát được đủ e = 0..3 (năm) hoặc e = 0..1 (đợt): kiểm tra độ vững, vì thành phần nhóm thay đổi theo e có thể tạo ra một động thái giả.
- Với Findex, thời gian sự kiện tính theo **đợt khảo sát**, không theo năm. Khoảng cách giữa các đợt không đều (3, 4 và 3 năm).

### 4.3. Suy luận

- Bootstrap phi tham số theo quốc gia, 999 lần, rút lại cả quốc gia. Cách này đưa cả sai số của trọng số gộp vào phương sai.
- Sai số chuẩn tính theo khoảng tứ phân vị như R `did`; khoảng tin cậy 95%.
- Event study dùng dải đồng thời (sup-t).
- Kiểm định hiệu giữa hai nhóm độc lập (H3, H4): SE = √(SE₁² + SE₂²).
- Hồi quy TWFE (H3 so sánh) dùng sai số chuẩn cụm theo quốc gia (CRV1) và giá trị p bằng wild cluster bootstrap có ràng buộc (trọng số Webb, 9.999 lần).

### 4.4. H2: tác động phân phối

- Biến kết quả là ba khoảng cách ở mục 3.2, ước lượng theo đặc tả chính trên dữ liệu đợt Findex.
- ATT > 0 nghĩa là khoảng cách tăng sau triển khai, phù hợp với H2.
- Báo cáo kèm ATT riêng từng nhóm (nữ, nam, nghèo 40%, giàu 60%, nông thôn, thành thị) để thấy khoảng cách thay đổi do nhóm nào. Phần này chỉ mô tả.
- Khoảng cách tính từ các ước lượng mẫu khảo sát, nên có sai số đo, nhất là nhóm nông thôn ở những nước nhỏ. Sai số này không gây chệch nhưng làm rộng khoảng tin cậy.

### 4.5. H3: điều kiện bảo đảm quyền

- **Kiểm định chính:** ước lượng đặc tả chính riêng trong nhóm `high_safeguard = 1` và `= 0`. Đối chứng là các nước chưa triển khai trong cùng nhóm. Hiệu θ_cao − θ_thấp được kiểm định cho SDG 1.3.1 và `transfer_total`, hiệu chỉnh Holm trên hai kiểm định.
- **So sánh theo đề cương:** Y_it = α_i + λ_t + β·D_it + γ·(D_it × S_i) + ε_it, với S_i là chỉ số liên tục đo năm 2014, đã trừ trung bình. Hệ số γ được báo cáo kèm p wild bootstrap, nhưng không dùng để kết luận H3, vì TWFE có thể chệch khi hiệu ứng thay đổi theo nhóm và theo thời gian.
- **Độ vững:** so sánh nhóm một phần ba cao nhất với một phần ba thấp nhất; từng thành phần của chỉ số riêng lẻ (thăm dò).

### 4.6. H4: thiết kế hệ thống (thăm dò)

- Ước lượng đặc tả chính trong hai nhóm: các nước bắt buộc xác thực sinh trắc khi nhận trợ cấp, và các nước cho phép phương án khác. Các nước chưa triển khai giữ vai trò đối chứng trong cả hai nhóm.
- Hiệu chỉnh BH. Không dùng để củng cố kết luận chính.

### 4.7. Bộ ước lượng so sánh

- Sun và Abraham (2021), đối chứng là các nước không triển khai trong cửa sổ.
- DID_M của de Chaisemartin và D'Haultfœuille (2020): tác động tức thời. Bản động `did_multiplegt_dyn` chạy bằng Stata hoặc R nếu cần.
- TWFE tĩnh, TWFE event study, và chẩn đoán trọng số âm của TWFE: số ô có trọng số âm và tổng trọng số âm. Mục đích là cho thấy vì sao không dùng TWFE làm ước lượng chính.

---

## 5. Kiểm tra xu hướng song song

1. **Kiểm định Wald** cho toàn bộ hệ số trước can thiệp (kỳ gốc thay đổi), dùng ma trận hiệp phương sai bootstrap. Không bác bỏ không có nghĩa là xu hướng song song đúng: kiểm định trước có độ mạnh thấp (Roth, 2022).
2. **Rambachan–Roth (2023)**, chạy bằng `r/honestdid.R`:
   - đại lượng: trung bình ATT của e = 0, 1, 2, 3 (năm) hoặc e = 0, 1 (đợt);
   - giới hạn độ lớn tương đối M̄ ∈ {0; 0,5; 1; 1,5; 2}, và giới hạn độ trơn M ∈ {0; 0,25; 0,5; 1} × SE của e = 0;
   - báo cáo giá trị phá vỡ M̄*: giá trị M̄ lớn nhất mà khoảng tin cậy vững vẫn không chứa 0.
   - Cách đọc: M̄* ≥ 1 nghĩa là kết luận vẫn giữ khi vi phạm xu hướng sau can thiệp lớn bằng vi phạm lớn nhất quan sát được trước can thiệp.
3. **Placebo:** đặc tả chính trên `elec_access` và `agri_land`. Một ATT khác 0 rõ rệt ở placebo là dấu hiệu gây nhiễu do các chương trình đi kèm.
4. Với Findex, nhóm 2017 không có kỳ trước can thiệp thứ hai, nên kiểm định trước can thiệp chỉ dựa vào nhóm 2021 và 2024.

---

## 6. Kiểm tra độ vững (cho H1, cả hai kết quả)

| Mã | Kiểm tra | Câu hỏi nó trả lời |
|---|---|---|
| R1 | Đối chứng là các nước không bao giờ triển khai | Kết quả có phụ thuộc vào việc dùng các nước triển khai muộn làm đối chứng không |
| R2 | Không có biến kiểm soát | Biến kiểm soát có làm thay đổi kết luận không |
| R3 | Thêm chi bảo trợ xã hội năm gốc | Năng lực tài khóa ban đầu |
| R4 | Độ trễ khác: năm +1; Findex 0 và 2 | Quy tắc gán thời điểm |
| R5 | Năm triển khai theo văn bản pháp lý | Định nghĩa can thiệp |
| R6 | SDG 1.3.1 nội suy tuyến tính trong khoảng có số liệu | Cách xử lý năm thiếu. Lưu ý: nội suy qua năm triển khai làm mờ bước nhảy nên kéo ước lượng về 0 |
| R7 | Chỉ các năm ≤ 2019 | Chi trả khẩn cấp thời COVID-19 |
| R8 | Loại các nước được nhà tài trợ cấp vốn triển khai | Gói can thiệp đi kèm |
| R9 | Event study cân bằng | Thành phần nhóm thay đổi theo thời gian sự kiện |
| R10 | Bỏ lần lượt từng khu vực | Kết quả có do một khu vực chi phối không |

Không đặt ngưỡng kiểu "bao nhiêu kiểm tra cùng dấu thì vững". Báo cáo toàn bộ, và chỉ ra kiểm tra nào làm đổi kết luận.

---

## 7. Kiểm soát kiểm định đa lần

| Họ | Kiểm định | Hiệu chỉnh |
|---|---|---|
| H1 | ATT tổng thể trên SDG 1.3.1 | Không (kiểm định chính duy nhất) |
| H1 phụ | ATT tổng thể trên `transfer_total` | Không, báo cáo như kết quả phụ |
| H2 | Ba khoảng cách | Holm |
| H3 | Hiệu cao − thấp trên hai kết quả | Holm |
| H4 và các phân tích thành phần | Mọi kiểm định thăm dò | BH |

---

## 8. Quy tắc kết luận

- Mọi hệ số đi kèm khoảng tin cậy 95%. Không viết "gần có ý nghĩa".
- **H1 được ủng hộ** khi ATT tổng thể trên SDG 1.3.1 dương và khoảng tin cậy 95% không chứa 0. Nếu khoảng tin cậy chứa cả 0 và những giá trị có ý nghĩa thực tiễn, kết luận là "chưa xác định".
- **Ngưỡng ý nghĩa thực tiễn đề xuất: 2 điểm phần trăm** độ bao phủ. Trước khi đăng ký, tác giả đối chiếu con số này với mức tăng độ bao phủ bình quân hằng năm trong World Social Protection Report 2024–26 (ILO, 2024), sửa nếu cần, và chốt trước khi xem kết quả. Kết luận "không có liên hệ đáng kể" chỉ đưa ra khi khoảng tin cậy 90% nằm trọn trong (−ngưỡng; +ngưỡng).
- **H2 được ủng hộ** cho một khoảng cách khi ATT > 0 và p sau Holm < 0,05.
- **H3 được ủng hộ** khi θ_cao − θ_thấp > 0 với p sau Holm < 0,05. Một nhóm có ý nghĩa thống kê và nhóm kia không có thì chưa đủ để kết luận.
- Kết luận nhân quả chỉ đi kèm giả định xu hướng song song và giá trị phá vỡ Rambachan–Roth.

---

## 9. Dữ liệu thiếu

- SDG 1.3.1 thiếu nhiều năm: xử lý theo từng ô (mục 4.1), không gán giá trị. Kiểm tra R6 dùng nội suy.
- Findex thiếu đợt: ô tương ứng bị bỏ.
- Biến kiểm soát thiếu: nước đó bị loại khỏi đặc tả có biến kiểm soát nhưng vẫn có trong đặc tả R2. Số nước bị loại được ghi trong `output/summary.md`.
- Không dùng gán giá trị đa lần (mục 12).

---

## 10. Các trường hợp minh họa: Việt Nam, Campuchia, Lào

- Ghi nhóm triển khai của từng nước và vị trí của nhóm đó trên event study.
- Chỉ báo cáo ATT theo nhóm g có chứa nước đó. Không báo cáo một ước lượng nhân quả cho riêng một nước, vì ô một nước không có suy luận đáng tin cậy.
- Phần diễn giải dựa vào văn bản chính sách và được trình bày tách khỏi kết quả định lượng.

---

## 11. Trình tự chạy

1. **Mã hóa năm triển khai** theo `docs/coding_protocol.md`.
   - Người mã hóa không được xem dữ liệu kết quả trong lúc mã hóa.
   - 20% số nước được mã hóa độc lập lần hai: `python -m idsp.coding sample` cho danh sách; `python -m idsp.coding agreement` cho các chỉ số trùng khớp; `python -m idsp.coding validate` để kiểm tra tệp mã hóa.
   - Nếu tỷ lệ trùng khớp chính xác dưới 0,80, sửa quy tắc rồi mã hóa lại.
   - Khóa bộ mã hóa bằng một git tag `coding-freeze`.
2. **Đăng ký kế hoạch này trên OSF** (khuyến nghị), trước bước 4.
3. **Kiểm tra pipeline:** `make test`, `make synthetic`, `Rscript r/honestdid.R` trên kết quả giả lập.
4. **Dựng dữ liệu thật:** `make download`, tải các tệp thủ công (`docs/data_sources.md`), `make build`.
5. **Chạy:** `make analysis`, rồi `make honestdid`.
6. Đối chiếu đặc tả chính với R `did` trên mẫu cân bằng.

---

## 12. Những điểm khác đề cương và lý do

| Đề cương | Bản chốt | Lý do |
|---|---|---|
| Biến điều tiết đo "tại thời điểm triển khai" | Đo năm 2014 | Không xác định được cho nhóm đối chứng; có thể chịu ảnh hưởng của chính việc triển khai |
| Kiểm soát chi bảo trợ xã hội, mức phổ cập di động và tài khoản, dự án định danh do nhà tài trợ cấp vốn | Chỉ dùng giá trị năm gốc; mức phổ cập tài khoản và dự án tài trợ không vào mô hình chính | Biến thay đổi theo thời gian có thể là kênh trung gian hoặc một phần của gói can thiệp |
| H3 ước lượng bằng TWFE có tương tác | Kiểm định chính bằng Callaway–Sant'Anna tách nhóm; TWFE chỉ để so sánh | TWFE chệch khi hiệu ứng thay đổi theo nhóm và thời gian (chính đề cương nêu lý do này) |
| Gán giá trị đa lần cho SDG 1.3.1 | Không dùng; xử lý theo từng ô, thêm kiểm tra nội suy | Việc thiếu số liệu SDG có thể liên quan đến năng lực thống kê, vốn tương quan với việc triển khai định danh số, nên giả định MAR không đáng tin hơn |
| "Kiểm định placebo trên các kết quả không chịu ảnh hưởng" | Chọn cụ thể: tiếp cận điện, đất nông nghiệp | Đề cương chưa nêu biến |
| Không nêu nhóm đối chứng khi tách nhóm | Đối chứng là các nước chưa triển khai trong cùng nhóm | Giữ so sánh trong cùng điều kiện bảo đảm quyền |

---

## 13. Ánh xạ giả thuyết → mã → bảng

| Giả thuyết | Mã | Bảng và hình |
|---|---|---|
| H1 | `pipeline.run`, khối H1 | `results_overall.csv` (analysis = H1), `H1_*_attgt.csv`, `H1_*_event_study_*.csv`, `figures/H1_*_event_study.png`, `honestdid/H1_*.json` |
| H2 | khối H2 | `results_overall.csv` (H2), `H2_*_event_study.csv` |
| H3 | khối H3 | `results_overall.csv` (H3, H3 robustness, H3 TWFE comparison) |
| H4 | khối H4 | `results_overall.csv` (H4) |
| Độ vững | khối Robustness | `results_overall.csv` (H1 robustness, H1 comparison, Placebo), `compare_*`, `diagnostic_*` |

## Tài liệu tham khảo cho tệp này

- Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. *Journal of Econometrics, 225*(2), 200–230.
- de Chaisemartin, C., & D'Haultfœuille, X. (2020). Two-way fixed effects estimators with heterogeneous treatment effects. *American Economic Review, 110*(9), 2964–2996.
- Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *Journal of Econometrics, 225*(2), 254–277.
- Rambachan, A., & Roth, J. (2023). A more credible approach to parallel trends. *Review of Economic Studies, 90*(5), 2555–2591.
- Roth, J. (2022). Pretest with caution: Event-study estimates after testing for parallel trends. *American Economic Review: Insights, 4*(3), 305–322.
- Sant'Anna, P. H. C., & Zhao, J. (2020). Doubly robust difference-in-differences estimators. *Journal of Econometrics, 219*(1), 101–122.
- Sun, L., & Abraham, S. (2021). Estimating dynamic treatment effects in event studies with heterogeneous treatment effects. *Journal of Econometrics, 225*(2), 175–199.
