from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_domain_account_payable(self):
        domain = [('deprecated', '=', False), '|', ('code', '=ilike', '33%'), '|', ('code', '=ilike', '14%'), '|', ('code', '=ilike', '6%'), ('code', '=ilike', '8%')]
        account_ids = self.env['account.account'].search(domain)
        return [('id', 'in', account_ids.ids)]
    def _get_domain_account_receivable(self):
        domain = [('deprecated', '=', False), '|', ('code', '=ilike', '13%'), '|', ('code', '=ilike', '14%'), '|', ('code', '=ilike', '6%'), ('code', '=ilike', '8%')]
        account_ids = self.env['account.account'].search(domain)
        return [('id', 'in', account_ids.ids)]

    property_account_payable_id = fields.Many2one('account.account', domain=_get_domain_account_payable)
    property_account_receivable_id = fields.Many2one('account.account', domain=_get_domain_account_receivable)