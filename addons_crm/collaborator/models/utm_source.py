from odoo import fields, models


class UtmSource(models.Model):
    _inherit = 'utm.source'
    _order = 'sequence asc'

    is_collaborator = fields.Boolean(string='Áp dụng cho cộng tác viên',
                                     default=False,
                                     help='Nguồn dùng cho cộng tác viên')
    tag = fields.Char(string='Tag', help='Sử dụng để tạo mã sinh tự dộng cho CTV')
    note = fields.Char(string='Ghi chú', help='Ghi chú nguồn cho dễ hiểu')
    sequence = fields.Integer(string='Thứ tự', default=10)
