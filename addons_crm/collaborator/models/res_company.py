from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    short_name = fields.Char(string='Tên rút gọn', help='Tên để hiển thị ngắn ngọn của công ty')

    short_code = fields.Char(string='Mã viết tắt', help='Cấu hình dùng để tạo mã các bản ghi liên quan tới công ty')

    collaborator_legal_name = fields.Char('Tên pháp lý', help='Tên pháp lý')
    collaborator_legal_name_company = fields.Char('Tên pháp lý chi nhánh', help='Tên pháp lý của chi nhánh')
    collaborator_legal = fields.Char('Người Đại Diện', help='Người đại diện chi nhánh ký hợp đồng')
    collaborator_registry = fields.Char('Mã số doanh nghiệp')
    collaborator_street = fields.Char('Địa chỉ')
    collaborator_state_id = fields.Char("Tỉnh/TP trong hợp đồng")

    collaborator_passport = fields.Char('Số CCCD')
    collaborator_passport_date = fields.Date('Ngày cấp')
    collaborator_passport_issue_by = fields.Char('Nơi cấp')
    collaborator_position = fields.Char('Chức vụ')
    collaborator_date_of_birth = fields.Date('Ngày sinh')
    collaborator_phone = fields.Char('Điện thoại')
    check_collaborator = fields.Selection([('1', 'Cá nhân'), ('2', 'Pháp nhân')], string='Loại hợp đồng', default='2')
