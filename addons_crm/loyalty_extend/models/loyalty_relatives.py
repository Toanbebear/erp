from odoo import fields, models


class LoyaltyRelatives(models.Model):
    _name = 'loyalty.relatives'
    _description = 'Sử dụng thẻ thành viên của người thân'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    line_id = fields.Many2one('crm.line', string='Dịch vụ')
    loyalty_id = fields.Many2one('crm.loyalty.card', string='Thẻ thành viên')
