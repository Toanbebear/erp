# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    company_id = fields.Many2one(index=True)
    product_id = fields.Many2one(check_company=False, index=True)
    account_move_id = fields.Many2one(index=True)
