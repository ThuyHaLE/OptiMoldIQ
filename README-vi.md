🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ: Hệ Thống Lập Kế Hoạch Ép Nhựa Thông Minh

OptiMoldIQ là một hệ thống sản xuất thông minh được thiết kế để tối ưu hóa và tự động hóa quy trình ép nhựa. Hệ thống sử dụng kiến trúc đa tác tử (multi-agent) để tự động lập kế hoạch sản xuất, theo dõi tài nguyên, và cung cấp các phân tích hỗ trợ ra quyết định nhằm nâng cao hiệu suất và chất lượng.

---

## Mục Lục
- [Giai Đoạn Hiện Tại](#giai-đoạn-hiện-tại)
- [Vấn Đề Kinh Doanh](#vấn-đề-kinh-doanh)
- [Mục Tiêu Chính](#mục-tiêu-chính)
- [Giải Pháp Dự Kiến](#giải-pháp-dự-kiến)
- [Tổng Quan Dữ Liệu](#tổng-quan-dữ-liệu)
- [Cấu Trúc Dữ Liệu](#cấu-trúc-dữ-liệu)
- [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)
- [Lộ Trình Phát Triển](#lộ-trình-phát-triển)
- [Tóm Tắt Trạng Thái Hiện Tại](#tóm-tắt-trạng-thái-hiện-tại)
- [Các Cột Mốc](#các-cột-mốc)
- [Khởi Động Nhanh](#khởi-động-nhanh-sắp-có)
- [Đóng Góp](#đóng-góp)
- [Giấy Phép](#giấy-phép)
- [Liên Hệ](#liên-hệ)

---

## Giai Đoạn Hiện Tại
OptiMoldIQ đang ở **giai đoạn thiết kế hệ thống**, tập trung vào định nghĩa cấu trúc cơ sở dữ liệu, luồng tác tử, và kiến trúc tổng thể.

---

## Vấn Đề Kinh Doanh

### Bối Cảnh
Trong sản xuất ép nhựa, việc đạt hiệu suất tối ưu đồng thời duy trì chất lượng sản phẩm cao là một thách thức lớn do nhiều yếu tố liên quan như:
- Việc sử dụng khuôn và bảo trì máy móc.
- Quản lý tồn kho nguyên liệu nhựa.
- Lập kế hoạch sản xuất và tối ưu năng suất.

### Thách Thức
Quản lý không hiệu quả hoặc thiếu tích hợp có thể dẫn đến:
- Tăng thời gian dừng máy.
- Lãng phí nguyên liệu hoặc thiếu hụt tồn kho.
- Sử dụng máy móc và khuôn lệch pha.
- Chất lượng sản phẩm không đồng đều hoặc tỷ lệ NG (không đạt) cao.
- Năng suất sản xuất thấp.

### Vấn Đề Cốt Lõi
Các hệ thống hiện tại:
- Chủ yếu thủ công hoặc tĩnh, không có khả năng phân tích thời gian thực.
- Dễ gây ra thiếu hiệu quả trong lập kế hoạch, theo dõi tài nguyên và quản lý chất lượng.

## Mục Tiêu Chính

- **Tích Hợp Lập Kế Hoạch và Giám Sát**: Tự động hóa lập kế hoạch sản xuất và theo dõi tài nguyên.
- **Phân Tích Chất Lượng và Năng Suất**: Tối ưu chu kỳ sản xuất nhưng vẫn đảm bảo chất lượng.
- **Bảo Trì Chủ Động và Cảnh Báo Thiếu Nguyên Liệu**: Ngăn ngừa thời gian chết và sự cố thiếu vật liệu.
- **Trực Quan Hóa và Hỗ Trợ Quyết Định**: Xây dựng bảng điều khiển trung tâm để hiển thị thông tin phân tích.

👉 [Đọc thêm chi tiết](docs/OptiMoldIQ-business-problem.md)

---

## Giải pháp Dự kiến

Hệ thống **OptiMoldIQ** sử dụng kiến trúc đa tác tử (multi-agent) để giải quyết các thách thức:

| Agent                        | Mô tả                                                                                                                  |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **DataPipelineOrchestrator** | **Collector**: Thu thập dữ liệu phân tán theo tháng → hợp nhất → **Loader**: tải vào cơ sở dữ liệu chia sẻ. Xử lý cả dữ liệu động và tĩnh. |
| **ValidationOrchestrator**   | Thực hiện kiểm tra chéo: <br>1. **PORequiredCriticalValidator**: `productRecords` ↔ `purchaseOrders` <br>2. **StaticCrossDataChecker**: Cả hai ↔ dữ liệu tĩnh <br>3. **DynamicCrossDataValidator**: Cả hai ↔ dữ liệu động |
| **OrderProgressTracker**     | Tổng hợp sản lượng theo máy/ca → liên kết với PO → Đánh dấu các sai lệch dựa trên kết quả xác minh.                     |
| **AutoPlanner**              | Tạo và tinh chỉnh lịch sản xuất: <br>• `InitialPlanner`: Tạo kế hoạch ban đầu dựa trên thông tin tĩnh. <br>• `PlanRefiner`: Tinh chỉnh kế hoạch dựa trên kết quả theo dõi và xác minh. |
| **AnalyticsOrchestrator**    | Thực hiện: <br>1. **DataChangeAnalyzer**: Theo dõi và cập nhật các thay đổi trong lịch sử (ví dụ: bố trí máy, sử dụng khuôn) <br>2. **MultiLevelDataAnalytics**: Phân tích dữ liệu sản phẩm ở nhiều cấp độ (năm, tháng, ngày, ca) để có cái nhìn sâu hơn. |
| **TaskOrchestrator**         | Thực hiện: <br>1. **ResinCoordinator**: Giám sát tồn kho và tiêu thụ nhựa. <br>2. **MoldCoordinator**: Theo dõi sử dụng và bảo trì khuôn. <br>3. **MachineCoordinator**: Theo dõi việc sử dụng máy, tính sẵn sàng và thời gian chờ máy. <br>4. **ProductQualityCoordinator**: Theo dõi tỷ lệ đạt và tỷ lệ NG. <br>5. **MaintenanceCoordinator**: Lên lịch bảo trì dự đoán để giảm thời gian chết cho khuôn và máy. <br>6. **YieldOptimizator**: Theo dõi mối quan hệ giữa thời gian chu kỳ, năng suất và tỷ lệ NG để tối ưu hóa sản lượng. Đồng thời phân tích mô hình sử dụng nhựa để đề xuất yêu cầu vật liệu hiệu quả hơn. |
| **DashBoardBuilder**         | Tạo bảng điều khiển tương tác để giám sát theo thời gian thực và hỗ trợ ra quyết định. |

🔗  Chi tiết: [OptiMoldIQ-agentsBreakDown](docs/OptiMoldIQ-agentsBreakDown.md)

---

## Sơ đồ kiến trúc hệ thống

Sơ đồ sau minh họa luồng dữ liệu từ các nguồn bên ngoài vào hệ thống và cách các tác tử khác nhau tương tác trong quy trình xử lý.

🔗 Chi tiết:  [OptiMoldIQ-systemDiagram-ASCII](docs/OptiMoldIQ-systemDiagram-ASCII.md)

<details> <summary> Hoặc click để xem chi tiết </summary>

```plaintext
                   ┌────────────────────────────────┐
                   │       External Inputs          │
                   │ DynamicDB (purchaseOrders,     │
                   │    productRecords) + StaticDB  │
                   └────────────┬───────────────────┘
                                │
                                ▼                                                          ┌────────────────────────────┐ 
                 ┌────────────────────────────┐                                            │    ValidationOrchestrator  │ 
                 │  DataPipelineOrchestrator  │                   ┌──────────────────────► │(Check consistency between  │ 
                 └────────────┬───────────────┘                   │                        │  Static & Dynamic Data)    │
                              │                                   │                        └────────────┬───────────────┘ 
        ┌────────────────────┴────────────────────┐               │         ┌───────────────────────┬───┴────────────────────┐                     
        ▼                                         ▼               │         ▼                       ▼                        ▼
┌────────────────────┐                 ┌─────────────────────┐    │    ┌────────────┐  ┌─────────────────────────┐ ┌────────────────────┐  
│    DataCollector   │                 │   DataLoaderAgent   │    │    │StaticCross │  │DynamicCrossDataValidator│ │ PORequiredCritical │       
│ (monthly dynamic DB│                 │ (load & unify static│    │    │DataChecker │  └────────────┬────────────┘ │ Validator          │
│   .xlsx → .parquet)│                 │   data → .parquet)  │    │    └─────┬──────┘               │              └───────────┬────────┘
└─────────┬──────────┘                 └─────────┬───────────┘    │          ▼                      ▼                          ▼
          ▼                                      ▼                │     ┌────────────────────────────────────────────────────────┐
    ┌──────────────────────────────────────────────────┐          │     │                    PO Mistmatch information            │
    │           ✅ Shared Database (.parquet)         │          │     └────────────────────────────────────────────────────────┘
    │     (static + dynamic for all other agents)      │──────────┘                                │
    └──────────────────────────────────────────────────┘                                           │
                          │                                                                        │
                          ▼                                                                        ▼
                   ┌──────────────────────────────────────────────────────────────────────────────────────┐
                   │                                  OrderProgressTracker                                │
                   │ (Group product records by PO, flag mismatch note from Validation agent (if any))     │
                   └──────────────────────────────────────────┬───────────────────────────────────────────┘
                                                              ▼
                                                    🛠️  To Be Continued...
```
</details>



---

## Tổng Quan Dữ Liệu

Dự án sử dụng tập dữ liệu 27 tháng từ một nhà máy ép nhựa, bao gồm hơn 61.000 bản ghi sản xuất và 6.200 đơn hàng nội bộ, phản ánh đầy đủ sự phức tạp trong sản xuất thực tế.

### Đối Tượng Chính
- **Items** – 694 sản phẩm nhựa
- **Molds** – 251 khuôn
- **Machines** – 49 máy đúc
- **Materials** – 445 nguyên liệu (nhựa, màu, phụ gia)
- **Orders** – 6.234 đơn hàng
- **Production Records** –  61.185 bản ghi sản xuất

🔗 Chi tiết: [OptiMoldIQ-dataset](docs/OptiMoldIQ-dataset.md)

---

## Cấu Trúc Dữ Liệu

OptiMoldIQ sử dụng dữ liệu chia sẻ chung, với 2 loại dataset động và tĩnh: 

### Dữ Liệu Động
- `productRecords`: Nhật ký sản xuất theo ca và máy.
- `purchaseOrders`: Đơn hàng cần thực hiện kèm thông tin nguyên vật liệu.

### Dữ Liệu Tĩnh
- `itemCompositionSummary`: Thành phần nguyên liệu theo từng sản phẩm.
- `itemInfo`: Thông tin sản phẩm.
- `machineInfo`: Thông tin máy móc và lịch sử bố trí.
- `moldInfo`: Thông số kỹ thuật và vòng đời khuôn.
- `moldSpecificationSummary`: Liên kết sản phẩm ↔ khuôn.
- `resinInfo`: Mã, tên và loại nhựa.

🔗 Chi tiết: [OptiMoldIQ-dbSchema](docs/OptiMoldIQ-dbSchema.md) for full field details and formats.

---

## Cấu Trúc Thư Mục

```bash
.
├── agents/                # Logic của các tác tử
├── database/              # Các schema JSON (tĩnh + chia sẻ)
├── logs/                  # Log tự động (trạng thái/lỗi)
├── docs/                  # Tài liệu (business_problem.md, agent_specifications.md, ...)
└── README-vi.md           # Tập tin này
```

---

## Lộ Trình Phát Triển

| Giai đoạn       | Mô tả                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------- |
| **Giai đoạn 1** | ✅ Định nghĩa CSDL tĩnh & động                                                                      |
| **Giai đoạn 2** | ✅ Xây dựng các tác tử tiền xử lý                                                                   |
| **Giai đoạn 3** | 🔄 Tích hợp tối ưu hóa bằng RL <br> • Định nghĩa hàm thưởng <br> • Huấn luyện trên dữ liệu lịch sử |
| **Giai đoạn 4** | 🔄 Xây dựng dashboard <br> • Thiết kế giao diện <br> • Tích hợp API                                |

---

## Tóm Tắt Trạng Thái Hiện Tại

| Thành phần                 | Trạng thái              |
| -------------------------- | ----------------------- |
| CSDL tĩnh (khuôn/máy/nhựa) | ✅ Đã định nghĩa         |
| Pipeline dữ liệu động      | ✅ Đã triển khai         |
| CSDL chia sẻ               | ✅ Phiên bản đầu tiên    |
| Hệ thống xác thực          | ✅ Đã hoạt động          |
| Tracker tiến độ            | ✅ Mapping theo PO và ca |
| AnalyticsOrchestrator      | 🔄 Sắp triển khai       |
| DashBoardBuilder           | 🔄 Sắp triển khai       |
| AutoPlanner                | 🔄 Sắp triển khai       |
| TaskOrchestrator           | 🔄 Sắp triển khai       |

---

## Các Cột Mốc
- ✅ **Milestone 01**: Hoàn thành Core Data Pipeline Agents
  Tháng 07/2025 — gồm `dataPipelineOrchestrator`, `validationOrchestrator`, `orderProgressTracker`.
  ➤ [Xem thêm](docs/milestones/OptiMoldIQ-milestone_01.md)
  ➤ [Xem orderProgressTracker Demo](docs/agents_output_overviews/orderProgressTracker_output_overviews.md)

- 🔄 Sắp tới: AnalyticsOrchestrator + DashBoardBuilder

---

## Khởi Động Nhanh (Sắp có)
- Cài đặt môi trường Python
- Chạy các tác tử với dữ liệu mẫu
- Trực quan hóa kết quả qua dashboard

--- 

## Đóng Góp
Chào đón mọi đóng góp! Hãy:
- Fork repo.
- Tạo nhánh mới cho tính năng.
- Gửi pull request để được xem xét.

---

## Giấy Phép
Dự án theo giấy phép MIT. Xem chi tiết tại [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) for details.

---

## Liên Hệ
Mọi câu hỏi hoặc hợp tác, vui lòng liên hệ:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*README này sẽ được cập nhật thường xuyên trong quá trình phát triển hệ thống OptiMoldIQ.*
