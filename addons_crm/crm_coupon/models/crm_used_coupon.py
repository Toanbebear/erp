from odoo import fields, models, api, _


class CRMUsedCoupon(models.Model):
    _name = 'crm.used.coupon'
    _description = 'List coupon had deposited'

    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    coupon_id = fields.Many2one('crm.discount.program', string='Coupon')
    account_payment_id = fields.Many2one('account.payment', string='Payment')
    campaign_id = fields.Many2one('utm.campaign', string='Campaign')
    booking_id = fields.Many2one('crm.lead', string='Booking')
    used = fields.Boolean(string='Đã sử dụng', default=False)
