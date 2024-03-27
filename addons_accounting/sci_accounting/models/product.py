# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_asset_accounts(self):
        res = super(ProductTemplate, self)._get_asset_accounts()
        Account = self.env['account.account']
        res['stock_input'], res['stock_output'] = Account.browse(self.env.context.get('stock_input')), Account.browse(self.env.context.get('stock_output'))
        return res
