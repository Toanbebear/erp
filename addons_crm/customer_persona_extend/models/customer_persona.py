from odoo import fields, models, api
from datetime import date
import logging
_logger = logging.getLogger(__name__)

TYPE = [('3', 'Đặc điểm cá nhân (Tính cách/Sở thích)'), ('4', 'Gia đình/Tình trạng hôn nhân'),
        ('5', 'Tài chính'),
        # ('6', 'Sở thích'),
        # ('7', 'Mục tiêu và nỗi lo cuộc sống'),
        ('8', 'Lịch sử làm đẹp'),
        # ('9', 'Bị ảnh hưởng bởi'),
        ('10', 'Hành vi trên Internet'),
        # ('11', 'Hoạt động hàng ngày'),
        ('12', 'Thông tin khác')]


class CustomerPersona(models.Model):

    _inherit = 'customer.persona'
    _description = 'Chân dung khách hàng'

    create_on = fields.Date('Ngày khai thác', default=fields.Date.today())
    type = fields.Selection(TYPE, string='Loại')
    description = fields.Text('Mô tả')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    type_2 = fields.Selection(TYPE, string='Loại')