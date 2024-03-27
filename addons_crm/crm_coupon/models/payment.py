from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Payment(models.Model):
    _inherit = 'account.payment'

    deposit = fields.Boolean(string='Đặt cọc')
    coupon_deposit_id = fields.Many2one('crm.discount.program', string='Coupon')
