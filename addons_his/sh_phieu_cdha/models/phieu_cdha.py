# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DonThuoc(models.Model):
    _inherit = 'sh.medical.imaging'

    company_id = fields.Many2one('res.company', string='Công ty chính',
                                 related="walkin.company_id",
                                 store=True,
                                 ondelete='cascade')

    company2_id = fields.Many2many('res.company', 'sh_medical_imaging_company_related_rel',
                                   'imaging_id', 'company_id',
                                   string='Công ty share',
                                   related="walkin.company2_id",
                                   store=True,
                                   readonly=True,
                                   ondelete='cascade')
