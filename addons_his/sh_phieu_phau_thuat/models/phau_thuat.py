# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PhauThuat(models.Model):
    _inherit = 'sh.medical.surgery'

    name = fields.Char(index=True)
    patient = fields.Many2one(index=True)
    booking_id = fields.Many2one(index=True)
    walkin = fields.Many2one(index=True)
    institution = fields.Many2one(index=True)
