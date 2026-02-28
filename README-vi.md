🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ
**Hệ thống lập kế hoạch sản xuất, phân tích và giám sát vận hành dựa trên workflow — dành cho ngành đúc nhựa.**

---

## Trạng thái dự án

- **Milestone ổn định hiện tại:** **Milestone 05 – UI Release**
- **Milestone tiếp theo:** Milestone 06 – Task Orchestration & Cloud Integration

Chú thích: ✅ Hoàn thành | 🔄 Đang thực hiện | 📝 Đã lên kế hoạch

---

## Tổng quan

**OptiMoldIQ** là hệ thống điều phối workflow theo module, phục vụ tối ưu hóa sản xuất. Hệ thống đóng gói các business agent thành module chuẩn hóa, kết hợp chúng thành các workflow khai báo, và điều phối thực thi với cơ chế kiểm tra dependency có thể cấu hình — được thiết kế cho hoạt động đúc phun nhựa.

Hệ thống phát triển qua các milestone được định nghĩa rõ ràng, ưu tiên:
- Business logic xác định (deterministic)
- Quan sát được trước khi tối ưu
- Phát triển tương thích ngược

Milestone 05 giới thiệu control panel chạy trên trình duyệt, xây dựng bằng React + Vite, cho phép người dùng không có nền tảng kỹ thuật kích hoạt workflow, theo dõi quá trình thực thi và khám phá dữ liệu phân tích — mà không cần chạm vào code. Panel được phục vụ trực tiếp bởi FastAPI backend và có thể truy cập qua URL chia sẻ.

---

## Tiến trình phát triển

```
M01: Core Data Pipeline
↓
M02: Production Planning Workflow
↓
M03: Analytics & Dashboards (Framework-ready)
↓
M04: Framework Release
↓
M05: UI Release ← hiện tại
↓
M06: Task Orchestration & Cloud Integration
```

---

## Kiến trúc hệ thống

OptiMoldIQ theo kiến trúc **workflow-driven, module-based**:

- **Modules** đóng gói business agent theo contract chung `BaseModule`
- **Workflows** là các định nghĩa JSON khai báo — không cần thay đổi code để cấu hình lại pipeline
- **Dependency policies** (`strict` / `hybrid` / `flexible`) kiểm soát cách mỗi module giải quyết đầu vào
- **ModuleRegistry** kết hợp đăng ký Python class và YAML config thành một nguồn sự thật duy nhất
- **Control Panel** là frontend React + Vite được phục vụ qua FastAPI — không cần server frontend riêng

```
OptiMoldIQ (Orchestration)
    └── WorkflowExecutor (Execution Engine)
            └── Modules (Business Logic) ← tất cả kế thừa BaseModule
                    └── Shared Database / Filesystem

FastAPI (Backend + Static Server)
    └── control_panel_dist/ ← React UI đã build sẵn
            └── Browser (Control Panel)
```

👉 Tài liệu kiến trúc đầy đủ:
- [Tổng quan kiến trúc](docs/v3/architecture/overview.md)
- [Sơ đồ hệ thống](docs/v3/architecture/diagrams)
- [BaseModule API](docs/v3/reference/base_module_api.md)
- [Workflow Schema](docs/v3/reference/workflow_schema.md)
- [Dependency Policies](docs/v3/reference/dependency_policies.md)
- [Module Registry](docs/v3/reference/module_registry.md)

---

## Bắt đầu nhanh

### Phương án A — Chạy qua Google Colab (Khuyến nghị cho người dùng không có nền tảng kỹ thuật)

Không cần cài đặt cục bộ. Mở notebook và làm theo các bước:

👉 [Mở trong Google Colab](https://colab.research.google.com/github/ThuyHaLE/OptiMoldIQ/blob/main/control_panel_notebook.ipynb)

**Yêu cầu:**
- Tài khoản Google
- Tài khoản ngrok miễn phí → lấy authtoken tại [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)

Notebook sẽ tự động:
1. Clone repository
2. Cài đặt toàn bộ dependencies
3. Build control panel UI
4. Khởi chạy ứng dụng và cung cấp URL chia sẻ

---

### Phương án B — Chạy cục bộ

```bash
git clone https://github.com/ThuyHaLE/OptiMoldIQ.git
cd OptiMoldIQ
pip install -r requirements.txt
pip install adjustText

# Build control panel (yêu cầu Node.js)
cd control_panel
npm install
npm run build
cd ..

# Khởi động server
python main.py
```

Sau đó mở [http://localhost:8000](http://localhost:8000) trên trình duyệt.

---

### Phương án C — Chạy workflow qua Python (không dùng UI)

`main.py` tự động tìm và liệt kê tất cả workflow khả dụng, sau đó chạy `update_database_strict` làm demo.

Để chạy workflow khác:

```python
result = orchestrator.execute("process_initial_planning")
```

Để buộc chạy lại mà không dùng cache:

```python
result = orchestrator.execute("update_database_strict", clear_cache=True)
```

👉 [Hướng dẫn Getting Started đầy đủ](docs/v3/guides/getting_started.md)

---

## Cấu trúc repository

```
OptiMoldIQ/
├── main.py                          # Entrypoint (API server + workflow demo)
├── configs/
│   ├── module_registry.yaml         # Registry cấu hình module trung tâm
│   ├── modules/                     # YAML config cho từng module
│   └── shared/
│       └── shared_source_config.py  # Cấu hình đường dẫn dùng chung
├── modules/                         # Các module business logic
├── optiMoldMaster/                  # Orchestrator cấp cao nhất
├── workflows/
│   ├── definitions/                 # Định nghĩa workflow JSON
│   ├── dependency_policies/         # strict / hybrid / flexible
│   ├── executor.py                  # Workflow execution engine
│   └── registry/                   # Module registry
├── api/                             # FastAPI routes & server
├── control_panel/                   # React + Vite source (npm run build)
├── control_panel_dist/              # UI đã build — được phục vụ bởi FastAPI
├── control_panel_notebook.ipynb     # Notebook khởi chạy trên Colab
└── requirements.txt
```

---

## Tài liệu

👉 [Mục lục tài liệu đầy đủ](docs/v3/README.md)

### Dành cho Developer mới
1. [Getting Started](docs/v3/guides/getting_started.md)
2. [Demo — Output Format](docs/v3/demo/output_format)
3. [Tổng quan kiến trúc](docs/v3/architecture/overview.md)

### Dành cho Module Developer
- [BaseModule API](docs/v3/reference/base_module_api.md)
- [Thêm Module mới](docs/v3/guides/adding_modules.md)
- [Cấu hình](docs/v3/guides/configuration.md)

### Dành cho Workflow Designer
- [Tạo Workflow](docs/v3/guides/creating_workflows.md)
- [Workflow Schema](docs/v3/reference/workflow_schema.md)
- [Dependency Policies](docs/v3/reference/dependency_policies.md)
- [Thêm Dependency Policy](docs/v3/guides/adding_dependency_policy.md)

---

## Bối cảnh nghiệp vụ

OptiMoldIQ giải quyết các thách thức phổ biến trong sản xuất đúc nhựa:
- Dữ liệu vận hành phân mảnh theo ca và máy
- Hiệu suất sử dụng khuôn – máy chưa được tối ưu
- Khả năng quan sát hạn chế theo các khung thời gian lập kế hoạch

👉 [Bài toán nghiệp vụ](docs/v2/OptiMoldIQ-business-problem.md) | [Giải pháp theo hướng vấn đề](docs/v2/OptiMoldIQ-problem_driven_solution.md)

---

## Các Milestone

### Milestone 01: Core Data Pipeline Agents (Hoàn thành tháng 7/2025)
> 👉 [Chi tiết](docs/v1/milestones/OptiMoldIQ-milestone_01.md)

### Milestone 02: Initial Production Planning System (Hoàn thành tháng 8/2025)
> 👉 [Chi tiết](docs/v1/milestones/OptiMoldIQ-milestone_02.md)

### Milestone 03: Enhanced Production Planning with Analytics and Dashboard System (Hoàn thành tháng 1/2026)
> 👉 [Chi tiết](docs/v2/milestones/OptiMoldIQ-milestone_03.md)

### Milestone 04: Framework Release (Hoàn thành tháng 2/2026)
> 👉 [Chi tiết](docs/v3/milestones/OptiMoldIQ-milestone_04.md)

### Milestone 05: UI Release (Hoàn thành tháng 2/2026)
> Control panel chạy trên trình duyệt, cho phép người dùng không có nền tảng kỹ thuật tương tác với workflow của OptiMoldIQ mà không cần viết code. Xây dựng bằng React + Vite, phục vụ qua FastAPI, và có thể triển khai ngay lập tức qua Google Colab + ngrok.
>
> **Điểm mới:**
> - Control panel React + Vite (`control_panel/`)
> - FastAPI phục vụ static file từ `control_panel_dist/`
> - Notebook khởi chạy trên Google Colab (`control_panel_notebook.ipynb`)
> - Giao diện kích hoạt workflow, theo dõi thực thi và xem analytics
>
> 👉 [Chi tiết](docs/v4/milestones/OptiMoldIQ-milestone_05.md)

---

## Demo & Trực quan hóa

**🌐 OptiMoldIQ Lite (Demo tương tác)**

Khám phá các giai đoạn workflow và dashboard mà không cần chạy toàn bộ hệ thống.

> 👉 [Xem demo](https://thuyhale.github.io/OptiMoldIQ/)

**▶️ Demo Control Panel**

Tất cả workflow đều ghi kết quả vào shared database. Với các workflow có module trực quan hóa (`ProgressTrackingModule`, `AnalyticsModule`, `InitialPlanningModule`), control panel hiển thị thêm một panel output tương tác để khám phá nhanh — ngay trong giao diện, không cần rời khỏi ứng dụng.

> **track_order_progress** — theo dõi tiến độ thời gian thực theo đơn hàng và máy
> ![Workflow: track_order_progress](docs/v4/demo/track_order_progress.gif)

> **process_initial_planning** — tạo và xem xét kế hoạch sản xuất ban đầu
> ![Workflow: process_initial_planning](docs/v4/demo/process_initial_planning.gif)

> **analyze_production_records (tổng quan)** — dashboard phân tích thay đổi layout machine và các cặp mold-machine
> ![Workflow: analyze_production_records (1)](docs/v4/demo/analyze_production_records_1.gif)

> **analyze_production_records (chi tiết)** — dashboard phân tích sản xuất theo ngày/tháng/năm
> ![Workflow: analyze_production_records (2)](docs/v4/demo/analyze_production_records_2.gif)

---

## Đóng góp

Mọi đóng góp đều được chào đón!
1. Fork repository
2. Tạo feature branch
3. Gửi pull request

---

## Giấy phép

Dự án được cấp phép theo MIT License. Xem [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE) để biết thêm chi tiết.

---

## Liên hệ

- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*OptiMoldIQ đang được phát triển liên tục — tài liệu và tính năng sẽ được mở rộng theo từng milestone.*
