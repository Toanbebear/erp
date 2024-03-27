from odoo import fields, models, api


class VNPayAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('vnpay', 'VNPay')])
