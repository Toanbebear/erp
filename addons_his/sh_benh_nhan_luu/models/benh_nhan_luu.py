# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class BenhNhanLuu(models.Model):
    _inherit = 'sh.medical.inpatient'

    patient = fields.Many2one(index=True)
    state = fields.Selection(index=True)
    walkin = fields.Many2one(index=True)

    walkin_company_id = fields.Many2one('res.company', string='Công ty chính',
                                        related="walkin.company_id",
                                        store=True,
                                        ondelete='cascade')

    walkin_company2_id = fields.Many2many('res.company', 'sh_medical_inpatient_company_related_rel',
                                          'inpatient_id', 'company_id',
                                          string='Công ty share',
                                          related="walkin.company2_id",
                                          store=True,
                                          readonly=True,
                                          ondelete='cascade')
