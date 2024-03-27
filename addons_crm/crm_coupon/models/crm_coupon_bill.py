from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
TYPE_DISCOUNT = [('percent', 'Phần trăm'), ('cash', 'Tiền mặt')]


class CRMCouponBill(models.Model):
    _name = 'crm.coupon.bill'
    _description = 'CRM coupon bill'

    coupon_id = fields.Many2one('crm.discount.program', string='Coupon')
    total_min = fields.Integer(string='Giá trị hóa đơn tối thiểu')
    type_discount = fields.Selection(TYPE_DISCOUNT, string='Loại giảm giá')
    discount = fields.Integer(string='Giảm')
    description = fields.Char(string='Mô tả')

