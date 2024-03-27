from odoo import models, fields

pwd_level = [('safe', 'An toàn'), ('not_safe', 'Không an toàn'), ('expired', 'Hết hạn')]


class InheritResUsers(models.Model):
    _inherit = 'res.users'

    pwd_level = fields.Selection(pwd_level, string='Mức độ bảo mật')
    pwd = fields.Char('Mật khẩu')
    pwd_date = fields.Date('Ngày đổi mật khẩu')
