# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_partnerledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super(ReportPartnerLedger, self)._get_report_values(docids, data)
        if data['form'].get('cbcnv', False):
            partners = self.env['res.partner'].browse(res['doc_ids']).filtered('employee')
            res.update({
                'docs': sorted(partners, key=lambda x: (x.ref or '', x.name or '')),
                'doc_ids': partners.ids,
            })
        return res
