from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'
    # use auto_join to speed up name_search call
    account_equivalent_id = fields.Many2one('account.account.equivalent', string='Tài khoản tương đương', auto_join=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")


class AccountAccountEquivalent(models.Model):
    _name = 'account.account.equivalent'
    _description = 'Account equivalent'

    account_sci_id = fields.Many2one('account.account', string="Tài khoản SCIGROUP")
    account_equivalent_ids = fields.One2many('account.account', 'account_equivalent_id', string="Tài khoản tương đương", ondelete='cascade')
