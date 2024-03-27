# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    balance = fields.Monetary('Số dư', compute="get_balance_line")
    is_sci_lock = fields.Boolean(string='Khóa dòng', default=False)

    @api.depends('debit', 'credit')
    def get_balance_line(self):
        for record in self:
            record.balance = record.debit - record.credit
