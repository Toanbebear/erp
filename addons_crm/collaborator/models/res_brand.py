from odoo import fields, models


class ResBrand(models.Model):
    _inherit = 'res.brand'

    short_code = fields.Char(string='Mã viết tắt CTV', help='Cấu hình dùng để tạo mã các bản ghi liên quan tới thương hiệu')
    #short_code_contract = fields.Char(string='Mã viết tắt hợp đồng CTV', help='Cấu hình dùng để tạo mã các bản ghi liên quan tới thương hiệu')
    active = fields.Boolean(string='Có hiệu lực', default=True)
    is_collaborator = fields.Boolean(string='Áp dụng cho cộng tác viên',
                                     default=False,
                                     help='Thương hiệu áp dụng CTV')
