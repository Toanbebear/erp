from odoo import fields, models, api
from datetime import date


class CustomerPersona(models.Model):
    _name = 'customer.persona'
    _description = 'Chân dung khách hàng'

    TYPE = [('3', 'Tính cách'), ('4', 'Gia đình/Tình trạng hôn nhân'),
            ('5', 'Tài chính'), ('6', 'Sở thích'), ('7', 'Mục tiêu và nỗi lo cuộc sống'), ('8', 'Thương hiệu yêu thích'),
            ('9', 'Bị ảnh hưởng bởi'), ('10', 'Hành vi trên Internet'), ('11', 'Hoạt động hàng ngày'),
            ('12', 'Thông tin khác')]
    create_on = fields.Date('Ngày khai thác', default=fields.Date.today())
    type = fields.Selection(TYPE, string='Loại')
    description = fields.Text('Mô tả')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')