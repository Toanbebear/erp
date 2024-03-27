# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockValuationLayer(models.Model):
    """Stock Valuation Layer overwrite to import data"""
    _inherit = 'stock.valuation.layer'
    _description = 'Stock Valuation Layer'

    company_id = fields.Many2one('res.company', 'Company', readonly=False, required=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=False, required=True, check_company=True)
    quantity = fields.Float('Quantity', digits=0, help='Quantity', readonly=False)
    uom_id = fields.Many2one(related='product_id.uom_id', readonly=False, required=True)
    unit_cost = fields.Monetary('Unit Value', readonly=False)
    value = fields.Monetary('Total Value', readonly=False)
    remaining_qty = fields.Float(digits=0, readonly=False)
    remaining_value = fields.Monetary('Remaining Value', readonly=False)
    description = fields.Char('Description', readonly=False)
    stock_valuation_layer_id = fields.Many2one('stock.valuation.layer', 'Linked To', readonly=False, check_company=True)
    stock_valuation_layer_ids = fields.One2many('stock.valuation.layer', 'stock_valuation_layer_id')
    stock_move_id = fields.Many2one('stock.move', 'Stock Move', readonly=False, check_company=True)
    account_move_id = fields.Many2one('account.move', 'Journal Entry', readonly=False, check_company=True)
    date = fields.Datetime('Ngày', readonly=False)


