from odoo import fields, models, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    partner_type = fields.Selection(selection_add=[('employee', 'CBCNV')])

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        if self.partner_type == 'employee':
            return {'domain': {'partner_id': [('employee', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('company_id', 'in', [self.company_id.id, False])]}}
