# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class VatTuChuyenKhoa(models.Model):
    _inherit = 'sh.medical.specialty.supply'

    name = fields.Many2one(index=True)
