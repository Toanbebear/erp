# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PhieuChuyenKhoa(models.Model):
    _inherit = 'sh.medical.specialty'

    walkin = fields.Many2one(index=True)