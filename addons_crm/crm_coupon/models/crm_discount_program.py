from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class InheritCRMDiscountProgram(models.Model):
    _inherit = 'crm.discount.program'

    coupon_bill_ids = fields.One2many('crm.coupon.bill', 'coupon_id')
    product_cate_ids = fields.Many2many('sh.medical.health.center.service.category', 'service_cate_discount_program_rel',
                                        'service_cate_ids', 'discount_program_ids', 'Nhóm dịch vụ')
    country_id = fields.Many2one('res.country', default=241)
    state_ids = fields.Many2many('res.country.state', 'country_state_discount_program_rel', 'country_state_ids',
                                 'discount_program_ids', 'Thành phố áp dụng')
    rank_id = fields.Many2one('crm.loyalty.rank', string='Hạng thẻ')
    type_data_partner = fields.Selection([('old', 'Khách hàng cũ'), ('new', 'Khách hàng mới')], string='Loại khách hàng')

