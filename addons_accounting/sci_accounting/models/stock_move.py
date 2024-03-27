# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    def _prepare_common_svl_vals(self):
        """Inherit stock_account function and adjust stock valuation layer to match account move date
        Note that date is new field of stock valuation layer in this module."""
        res = super(StockMoveInherit, self)._prepare_common_svl_vals()
        res['date'] = self.env.context.get('force_period_date', fields.Datetime.now())
        return res

