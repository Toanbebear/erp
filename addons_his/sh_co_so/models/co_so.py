# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CoSo(models.Model):
    _inherit = 'sh.medical.health.center'

    his_company = fields.Many2one(index=True)
    brand = fields.Many2one(index=True)