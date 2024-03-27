# -*- coding: utf-8 -*-

from odoo import fields, models, _


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"

    cbcnv = fields.Boolean("CBCNV", help="Đối tác là CBCNV")

    def pre_print_report(self, data):
        data = super(AccountPartnerLedger, self).pre_print_report(data)
        data['form'].update({'cbcnv': self.cbcnv})
        return data
