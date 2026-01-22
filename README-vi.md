🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ  
**Hệ thống lập kế hoạch sản xuất, phân tích và quan sát vận hành dựa trên workflow cho ngành ép nhựa.**

---

## Trạng thái dự án

- **Cột mốc ổn định hiện tại:** **Milestone 03 – Sẵn sàng cho framework**
- **Cột mốc tiếp theo:** Milestone 04 – Phát hành Framework

Chú thích: ✅ Hoàn thành | 🔄 Đang thực hiện | 📝 Dự kiến

---

## Tổng quan

**OptiMoldIQ** là một hệ thống sản xuất đa tác nhân (multi-agent) được thiết kế để điều phối: luồng dữ liệu, lập kế hoạch sản xuất, phân tích, và trực quan hóa cho các hoạt động ép nhựa (injection molding).

Hệ thống được phát triển theo các cột mốc rõ ràng, ưu tiên:
- Logic nghiệp vụ mang tính quyết định (deterministic)
- Quan sát hệ thống (observability) trước khi tối ưu hóa
- Tiến hóa hệ thống có khả năng tương thích ngược

Milestone 03 hoàn thiện hành vi cốt lõi và chuẩn hóa mô hình thực thi của các agent, chuẩn bị cho việc chính thức hóa thành framework.

---

## Tiến trình phát triển hệ thống
```
M01: Pipeline dữ liệu cốt lõi
↓
M02: Workflow lập kế hoạch sản xuất
↓
M03: Phân tích & Dashboard (Sẵn sàng cho framework) ← hiện tại
↓
M04: Chuẩn hóa các contract thành framework thực thi có thể tái sử dụng
↓
M05: Điều phối tác vụ & tầng chính sách

```

---

## Tổng quan kiến trúc

OptiMoldIQ **tuân theo kiến trúc agent-based, điều khiển bằng workflow:**:

- **Agents** đóng vai trò runtime thực thi
- **Modules** đóng gói logic nghiệp vụ mang tính quyết định
- **Analytics and dashboards** là các thành phần tiêu thụ dữ liệu phía downstream
- Không có thành phần downstream nào được phép thay đổi hành vi lập kế hoạch phía upstream

👉 Chi tiết kiến trúc:
- [Cấu trúc thư mục dự án](docs/v2/OptiMoldIQ-projectDirectory.md)
- [Sơ đồ hệ thống (ASCII)](docs/v2/OptiMoldIQ-systemDiagram-ASCII.md)
- [Phân rã các agent](docs/v2/OptiMoldIQ-agentsBreakDown.md)
- [Mô tả agent](docs/v2/OptiMoldIQ-agentsDescriptions.md)
- [Hợp đồng cấu hình dùng chung](docs/v2/OptiMoldIQ-sharedConfig.md)
- [Định dạng thực thi agent](docs/v2/OptiMoldIQ-agentExecutionFormat.md)

--- 

## Bối cảnh nghiệp vụ

OptiMoldIQ giải quyết các vấn đề phổ biến trong sản xuất ép nhựa như:
- Dữ liệu vận hành bị phân mảnh
- Hiệu suất sử dụng khuôn – máy thấp
- Thiếu khả năng quan sát xuyên suốt các cấp độ lập kế hoạch

👉 Bối cảnh đầy đủ:
- [Bài toán nghiệp vụ](docs/v2/OptiMoldIQ-business-problem.md)
- [Giải pháp định hướng theo bài toán](docs/v2/OptiMoldIQ-problem_driven_solution.md)

---

## Mô hình dữ liệu

OptiMoldIQ vận hành theo pipeline **raw → shared database pipeline**, cho phép mọi agent truy cập dữ liệu một cách nhất quán.

👉 Tài liệu cơ sở dữ liệu:
- [Raw database](docs/v2/OptiMoldIQ-rawDatabase.md)
- [Shared database](docs/v2/OptiMoldIQ-sharedDatabase.md)
- [ERD & schema](docs/v2/OptiMoldIQ-dbSchema.md)

---

## Cấu trúc repository (mức cao)

```bash
.
├── agents/        # Runtime thực thi agent đã được chuẩn hóa
├── modules/       # Logic nghiệp vụ mang tính quyết định
├── database/      # Schema và dữ liệu tham chiếu
├── docs/          # Kiến trúc, cột mốc, đặc tả
├── logs/          # Log thực thi
└── README.md
```

---

## Các cột mốc

### Cột mốc 01: Các agent pipeline dữ liệu cốt lõi (Hoàn thành tháng 07/2025)
> 👉 [Chi tiết](docs/v1/milestones/OptiMoldIQ-milestone_01.md)
> 
### Cột mốc 02: Hệ thống lập kế hoạch sản xuất ban đầu (Hoàn thành tháng 08/2025)
> 👉 [Chi tiết](docs/v1/milestones/OptiMoldIQ-milestone_02.md)

### Cột mốc 03: Hệ thống lập kế hoạch nâng cao kèm phân tích & dashboard (Hoàn thành tháng 01/2026)
> 👉 [Chi tiết](docs/v2/milestones/OptiMoldIQ-milestone_03.md)

---

## Demo & Trực quan hóa

**🌐 OptiMoldIQ Lite (Demo tương tác)**

Khám phá các giai đoạn workflow và dashboard mà không cần chạy toàn bộ hệ thống.

> 👉 [Xem demo](https://thuyhale.github.io/OptiMoldIQ/)

---

## Bắt đầu nhanh (Quickstart)

Một ví dụ có thể chạy được đã được cung cấp trong tài liệu.

> 👉 [Xem tại đây](docs/v2/quickstart.md)

--- 

## Đóng góp
Mọi đóng góp đều được hoan nghênh! Để tham gia:
1. Fork repository
2. Tạo feature branch
3. Gửi pull request

---

## Giấy phép
Dự án được phát hành theo giấy phép MIT. Xem [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) để biết chi tiết.

---

## Liên hệ
Nếu có câu hỏi hoặc nhu cầu hợp tác, vui lòng liên hệ qua:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*OptiMoldIQ đang được phát triển liên tục — tài liệu và năng lực hệ thống sẽ được mở rộng theo từng cột mốc.*