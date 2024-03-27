# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    lydo = fields.Char(related='move_id.lydo')

    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        for line in self:
            if not line.currency_id:
                continue
            company = line.move_id.company_id
            balance = line.currency_id._convert(line.amount_currency, company.currency_id, company,
                                                line.move_id.date or fields.Date.context_today(line))
            line.debit = balance if balance > 0.0 else 0.0
            line.credit = -balance if balance < 0.0 else 0.0

            line.update(line._get_fields_onchange_balance(
                balance=line.amount_currency,
            ))
            line.update(line._get_price_total_and_subtotal())
