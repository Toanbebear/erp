from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    # use auto_join to speed up name_search call
    account_journal_equivalent_id = fields.Many2one('account.journal.equivalent', string='Nhật ký tương đương', auto_join=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")


class AccountJournalEquivalent(models.Model):
    _name = 'account.journal.equivalent'
    _description = 'Account journal equivalent'

    account_sci_id = fields.Many2one('account.journal', string="Nhật ký SCIGROUP")
    account_equivalent_ids = fields.One2many('account.journal', 'account_journal_equivalent_id', string="Nhật ký tương đương", ondelete='cascade')
