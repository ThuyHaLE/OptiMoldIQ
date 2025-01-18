[English](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/README.md) | Tiếng Việt

# OptiMoldIQ: Hệ Thống Lập Kế Hoạch Molding Nhựa Thông Minh

OptiMoldIQ là một hệ thống sản xuất thông minh được thiết kế để tối ưu hóa và đơn giản hóa quy trình ép nhựa. Hệ thống này tích hợp kiến trúc đa tác nhân để tự động hóa lập kế hoạch sản xuất, theo dõi tài nguyên và cung cấp các thông tin có thể hành động để cải thiện hiệu quả và chất lượng.

---
## Giai Đoạn Hiện Tại
OptiMoldIQ hiện đang ở **giai đoạn thiết kế hệ thống**, tập trung vào việc xác định cấu trúc cơ sở dữ liệu, quy trình làm việc của các tác nhân và kiến trúc hệ thống.

---

## Vấn Đề Kinh Doanh
### Bối Cảnh
Trong lĩnh vực đúc nhựa, việc đạt được hiệu quả tối ưu đồng thời duy trì chất lượng sản phẩm cao là một thách thức do sự phức tạp của các yếu tố liên quan như:
- Sử dụng khuôn và bảo trì máy móc.
- Quản lý tồn kho nhựa.
- Lập kế hoạch sản xuất và tối ưu hóa năng suất.

### Thách Thức
Quản lý kém hoặc thiếu sự tích hợp giữa các thành phần có thể dẫn đến:
- Thời gian không sản xuất tăng.
- Lãng phí nguyên liệu hoặc dư thừa/thiếu hụt tồn kho.
- Sử dụng máy móc và khuôn không phù hợp.
- Chất lượng sản phẩm không đồng nhất hoặc tỷ lệ sản phẩm lỗi (NG) cao.
- Năng suất và hiệu quả sản xuất giảm.

### Nhận Diện Vấn Đề
Các hệ thống hiện tại:
- Thường là thủ công hoặc tĩnh, thiếu thông tin thời gian thực.
- Dễ bị thiếu hiệu quả trong lập kế hoạch, theo dõi tài nguyên và quản lý chất lượng.

## Mục Tiêu Chính
- **Lập Kế Hoạch và Giám Sát Tích Hợp**: Tự động hóa việc lập kế hoạch sản xuất và theo dõi tài nguyên.
- **Thông Tin Chất Lượng và Năng Suất**: Tối ưu hóa thời gian chu kỳ đồng thời duy trì chất lượng.
- **Bảo Trì và Đặt Hàng Nhựa Chủ Động**: Ngăn ngừa thời gian dừng sản xuất và tình trạng dư thừa/thiếu hụt nguyên liệu.
- **Hình Ảnh và Hỗ Trợ Quyết Định**: Xây dựng một bảng điều khiển trung tâm để nhận diện ra các hiểu biết sâu sắc từ dữ liệu trong việc hỗ trợ ra quyết định.

## Giải Pháp Dự Kiến
Hệ thống OptiMoldIQ sử dụng kiến trúc đa đại lý để giải quyết các thách thức này:
- **AutoStatus Agent**: Theo dõi tiến độ sản xuất thời gian thực.
- **InitialSched Agent**: Tạo ra kế hoạch sản xuất sơ khởi.
- **FinalSched Agent**: Hoàn thiện kế hoạch sản xuất sơ khởi dựa trên các báo cáo theo dõi có liên quan.
- **Resin Tracking Agent**: Theo dõi tồn kho và mức tiêu thụ nhựa.
- **Mold Tracking Agent**: Theo dõi sử dụng khuôn, bảo trì.
- **Machine Tracking Agent**: Quản lý tình trạng máy móc và thời gian dẫn.
- **MaintenanceScheduler Agent**: Lên lịch bảo trì dự báo để giảm thời gian dừng sản xuất.
- **Quality Control Agent**: Theo dõi sản lượng và tỷ lệ NG
- **YieldOptimization Agent**: Theo dõi mối quan hệ giữa chu kỳ sản xuất, sản lượng và tỷ lệ NG để tối ưu sản lượng.
- **DashBoardBuilderAgent**: Tạo ra bảng điều khiển tương tác với người dùng để biểu diễn dữ liệu.

## Tình Trạng Hiện Tại
- Tài liệu về vấn đề kinh doanh và thiết kế giải pháp đã hoàn thành.
- Cơ sở dữ liệu tĩnh đã được xác định cho khuôn, máy móc và nhựa.
- Quy trình làm việc của các đại lý đã được phác thảo (ví dụ: AutoStatus Agent, InitialSched Agent).

### Các Bước Tiếp Theo
- Phát triển và kiểm thử các nguyên mẫu đại lý.
- Tích hợp học tăng cường để tối ưu hóa năng suất.
- Thiết kế và triển khai cơ sở dữ liệu chia sẻ giữa các đại lý.

## Lộ Trình
- **Giai đoạn 1**: Xác định cơ sở dữ liệu tĩnh và động.
- **Giai đoạn 2**: Phát triển các đại lý lõi và tích hợp các hệ thống tĩnh.
- **Giai đoạn 3**: Thêm học tăng cường để tối ưu hóa.
- **Giai đoạn 4**: Xây dựng và kiểm thử bảng điều khiển cho việc biểu hiện dữ liệu.

## Đóng Góp
Chúng tôi hoan nghênh đóng góp! Để đóng góp:
- Fork repository.
- Tạo một branch cho tính năng của bạn.
- Gửi pull request để được xem xét.

## Giấy Phép
Dự án này được cấp phép theo Giấy phép MIT. Xem chi tiết tại [LICENSE](https://github.com/ThuyHaLE/OptiMoldIQ/blob/main/LICENSE).

## Liên Hệ
Để hỏi hoặc hợp tác, vui lòng liên hệ qua:
- [Email](mailto:thuyha.le0590@gmail.com)
- [GitHub](https://github.com/ThuyHaLE)

*Bản README này sẽ được cập nhật thường xuyên khi hệ thống OptiMoldIQ phát triển qua các giai đoạn.*
