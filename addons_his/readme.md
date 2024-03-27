#Cài đặt
Cài module:

1. SCI HRMS ALL IN ONE
2. CRM BASE
3. SCI Health All In One (shealth_all_in_one)
4. CRM HIS
4. Standard Accounting Report, SCI ACCOUTING, Inter Company Stock Transfer
5. OPTION CÓ THỂ CÀI HOẶC KO
+ report_pdf_print (gọi lệnh in trực tiếp)
+ base_export_manager (quản lý quyền xuất dữ liệu)
+ permit_export_module (quản lý quyền ẩn hiển nút xuất dữ liệu)
config trong cấu hình kỹ thuật: Export Button Permission

Option: (Có thể cài hoặc ko)
1. Report Pdf Preview (Để preview các phiếu trước khi in) hoặc Report Pdf Print (in phiếu)
2. web_groupby_expand: expand all group tree view
3. odoo_web_login: chỉnh sửa trang đăng nhập

#Cấu hình: Thiết lập -> Thiết tập chung
SET ALLOWS COMPANY TẤT CẢ CÁC CTY CHO TK ADMIN
1. Người dùng -> Quyền truy cập: để mặc định là ko có quyền gì (ngoài excel template), set Múi giờ, set default partner
2. CRM: -> Tiềm năng
3. Sale: -> Biến thể, đơn vị tính, chiết khấu, bảng giá
4. Sản phẩm -> Đơn vị sản phẩm
5. Kho hàng -> Đa nhà kho; Các tuyến nhiều bước
                Tắt tính năng SMS khi điều chuyển kho (TẮT THEO TỪNG CÔNG TY)
6. Kỹ thuật:	Độ chính xác thập phân => Product Unit of Measure => 2

#SỬA ĐỊNH DANH PHIẾU KHO
Thiết lập -> Kỹ thuật -> Các loại mã 
                
#Cấu hình 
Nhóm sản phẩm kho:
(KHO VẬN/CẤU HÌNH/NHÓM SẢN PHẨM)
- Định giá tồn kho: 
Phương pháp giá vốn: Giá trung bình AVCO
Định giá tồn kho: Tự động 

Phương pháp giá vốn: 
- Nếu chốt chạy phương thức xuất kho theo FEFO thì cấu hình các nhóm sản phẩm của bệnh viện (vật tư/thuốc) là FEFO, không thì chọn là FIFO 
- Cấu hình các tài khoản định khoản cho kho:
Tài khoản doanh thu : 5111
Tài khoản chi phí: 1561
Tài khoản nhập kho: 1561
Tài khoản xuất kho: 621
Tài khoản Định giá Tồn kho: 152

- Tắt tuyến cung ứng Nội bộ

#CHẠY RPC 
- Sinh data phòng và tủ liên quan đến khoa của các bệnh viện

#Import data (FILE EXCEL)
- Import route rule kho để điều chuyển hàng
- Import Đơn vị Đo lường sản phẩm (đơn vị, thể tích, khối lượng): (Kho -> Cấu hình)
- Import bác sĩ
- Import data dân tộc, ngoại kiều, đường dùng, mã icd10 (Bệnh viện -> Cấu hình)
- Import thuốc, vật tư(Bệnh viện -> Kho Dược -> Thuốc, vật tư)
- Import danh sách dịch vụ (Bệnh viện -> Cấu hình -> Dịch vụ)
- Import bảng giá theo thương hiệu
- Cấu hình các xn, cđha, bom, đơn thuốc cho từng dịch vụ (Bệnh viện -> Cấu hình -> Dịch vụ)
- Cấu hình hướng dẫn sau dịch vụ
- Import cơ số theo công ty (chi nhánh)

#Dịch lại text
- Ngày loại bỏ (removal_date) -> Ngày hết hạn
- Đơn mua hàng -> Hóa đơn nhà cung cấp (module purchase)
- You cannot delete a payment that is already posted. -> Bạn không thể xóa các phiếu thu đã được xác nhận. (Tạo các từ còn thiếu -> module account)
- You have not recorded done quantities yet, by clicking on apply Odoo will process all the reserved quantities. => Bạn chưa ghi nhận số lượng hoàn thành!<br/> Bạn có muốn hệ thống tự động xử lý để ghi nhận số lượng giữ trước cho đơn hàng của bạn?<br> Áp dụng ngay!
- Create Backorder? -> Áp dụng ngay!
- Immediate Transfer? => Thông báo
- Theorical Cost Price => Giá theo sổ sách
- Điều chỉnh tồn kho => Kiểm kho
- Quy tắc tái cung ứng => Cấu hình Cơ số tủ trực
- Chạy trình điều độ => Chạy cơ số tủ trực
- Ngày Loại bỏ => Ngày hết hạn
- State (base 887) => Thành phố
- Địa điểm đích => Kho nhập
- Xí trước => Giữ trước
- Thôi xí => Bỏ giữ trước
- Create a new inventory adjustment =>Tạo phiếu kiểm kê kho mới
- This is used to correct the product quantities you have in stock. =>Điều này được sử dụng để điều chỉnh số lượng sản phẩm bạn có trong kho.
- You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities. => Bạn không thể xác nhận phiếu vì không còn hàng khả dụng trong kho.
- Define a new transfer in stock => Thông tin phiếu kho
- Bizapps -> Hệ thống
- The stock will be reserved for operations waiting for availability and the reordering rules will be triggered. => Chạy trình tổng hợp nhu cầu ở các tất cả các Tủ 
- <span class="o_stat_text">Purchase Orders</span> => <span class="o_stat_text">HĐ mua hàng</span>
- Expiration Alert -> Cảnh báo hết hạn
- Date to determine the expired lots and serial numbers using the filter "Expiration Alerts". -> Ngày để xác định lô đã hết hạn và số sê-ri bằng bộ lọc "Cảnh báo hết hạn". 
- Accounting hoặc Invoicing -> Kế toán
- Journal Items (255,367) -> Bút toán phát sinh chi tiết
- Demand(module Stock) => Yêu cầu
- Send receipt by email -> Gửi biên nhận thanh toán qua email
#Hướng dẫn 