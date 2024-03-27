# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class StockValuationLayerInherit(models.Model):
    _inherit = 'stock.valuation.layer'

    date = fields.Datetime('Ngày', readonly=True)

