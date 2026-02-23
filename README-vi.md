🌐 [English](README.md) | [Tiếng Việt](README-vi.md)

# OptiMoldIQ
**Hệ thống lập kế hoạch sản xuất, phân tích và giám sát vận hành dựa trên workflow cho ngành ép nhựa.**

---

## Trạng thái dự án

- **Milestone ổn định hiện tại:** **Milestone 04 – Framework Release**
- **Milestone tiếp theo:** Milestone 05 – UI Release & Task Orchestration

Chú thích: ✅ Hoàn thành | 🔄 Đang thực hiện | 📝 Đã lên kế hoạch

---

## Tổng quan

**OptiMoldIQ** là hệ thống điều phối workflow dựa trên module, phục vụ tối ưu hóa sản xuất. Hệ thống đóng gói các business agent thành các module chuẩn hóa, kết hợp chúng thành các workflow khai báo, và điều phối thực thi với cơ chế kiểm tra dependency có thể cấu hình — được thiết kế cho ngành ép phun nhựa.

Hệ thống phát triển qua các milestone được định nghĩa rõ ràng, ưu tiên:
- Business logic xác định (deterministic)
- Khả năng quan sát trước khi tối ưu hóa
- Phát triển tương thích ngược

Milestone 04 hình thức hóa các hợp đồng framework được thiết lập từ Milestone 03, phát hành một execution runtime ổn định với các hợp đồng công khai cho module, workflow và dependency policy.

---

## Lộ trình phát triển

```
M01: Core Data Pipeline
↓
M02: Production Planning Workflow
↓
M03: Analytics & Dashboards (Framework-ready)
↓
M04: Framework Release ← hiện tại
↓
M05: UI Release & Task Orchestration
```

---

## Tổng quan kiến trúc

OptiMoldIQ theo kiến trúc **workflow-driven, module-based**:

- **Modules** đóng gói business agent theo hợp đồng `BaseModule` chung
- **Workflows** là các định nghĩa JSON khai báo — không cần thay đổi code để cấu hình lại pipeline
- **Dependency policies** (`strict` / `hybrid` / `flexible`) kiểm soát cách mỗi module phân giải đầu vào
- **ModuleRegistry** kết hợp đăng ký Python class và YAML config thành nguồn thông tin duy nhất

```
OptiMoldIQ (Orchestration)
    └── WorkflowExecutor (Execution Engine)
            └── Modules (Business Logic) ← tất cả kế thừa BaseModule
                    └── Shared Database / Filesystem
```

👉 Tài liệu kiến trúc đầy đủ:
- [Tổng quan kiến trúc](docs/v3/architecture/overview.md)
- [Sơ đồ hệ thống](docs/v3/architecture/diagrams)
- [BaseModule API](docs/v3/reference/base_module_api.md)
- [Workflow Schema](docs/v3/reference/workflow_schema.md)
- [Dependency Policies](docs/v3/reference/dependency_policies.md)
- [Module Registry](docs/v3/reference/module_registry.md)

---

## Quickstart

```bash
git clone https://github.com/ThuyHaLE/OptiMoldIQ.git
cd OptiMoldIQ
pip install -r requirements.txt
python main.py
```

`main.py` tự động phát hiện và liệt kê tất cả workflow hiện có, sau đó chạy `update_database_strict` làm demo.

Để chạy một workflow khác:

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
├── main.py                          # Điểm vào demo
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
- [Thêm một Module mới](docs/v3/guides/adding_modules.md)
- [Cấu hình](docs/v3/guides/configuration.md)

### Dành cho Workflow Designer
- [Tạo Workflow](docs/v3/guides/creating_workflows.md)
- [Workflow Schema](docs/v3/reference/workflow_schema.md)
- [Dependency Policies](docs/v3/reference/dependency_policies.md)
- [Thêm một Dependency Policy mới](docs/v3/guides/adding_dependency_policy.md)

---

## Bối cảnh nghiệp vụ

OptiMoldIQ giải quyết các thách thức phổ biến trong sản xuất ép nhựa:
- Dữ liệu vận hành phân mảnh giữa các ca và máy
- Hiệu quả sử dụng khuôn–máy chưa tối ưu
- Khả năng quan sát hạn chế theo các khung thời gian kế hoạch

👉 [Vấn đề nghiệp vụ](docs/v2/OptiMoldIQ-business-problem.md) | [Giải pháp theo vấn đề](docs/v2/OptiMoldIQ-problem_driven_solution.md)

---

## Milestones

### Milestone 01: Core Data Pipeline Agents (Hoàn thành tháng 7/2025)
> 👉 [Chi tiết](docs/v1/milestones/OptiMoldIQ-milestone_01.md)

### Milestone 02: Initial Production Planning System (Hoàn thành tháng 8/2025)
> 👉 [Chi tiết](docs/v1/milestones/OptiMoldIQ-milestone_02.md)

### Milestone 03: Enhanced Production Planning with Analytics and Dashboard System (Hoàn thành tháng 1/2026)
> 👉 [Chi tiết](docs/v2/milestones/OptiMoldIQ-milestone_03.md)

### Milestone 04: Framework Release (Hoàn thành tháng 2/2026)
> 👉 [Chi tiết](docs/v3/milestones/OptiMoldIQ-milestone_04.md)

---

## Demo & Trực quan hóa

**🌐 OptiMoldIQ Lite (Demo tương tác)**

Khám phá các giai đoạn workflow và dashboard mà không cần chạy hệ thống đầy đủ.

> 👉 [Xem demo](https://thuyhale.github.io/OptiMoldIQ/)

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