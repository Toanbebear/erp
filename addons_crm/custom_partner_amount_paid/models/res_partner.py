from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    amount_paid = fields.Float('Tổng tiền khách trả', compute='_compute_amount_paid', store=True)

    @api.depends('payment_ids.state', 'payment_ids.payment_type')
    def _compute_amount_paid(self):
        for record in self:
            record.amount_paid = 0
            if record.payment_ids:
                for payment in record.payment_ids:
                    if payment.payment_type == 'inbound' and payment.state not in ['draft', 'cancel']:
                        record.amount_paid += payment.amount
                    elif payment.payment_type == 'outbound' and payment.state not in ['draft', 'cancel']:
                        record.amount_paid -= payment.amount
