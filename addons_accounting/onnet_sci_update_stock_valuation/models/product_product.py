from odoo import models, fields, api
from datetime import datetime


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_value = fields.Float(string='Total Value', compute='_compute_total_value')

    @api.depends('standard_price')
    def _compute_total_value(self):
        for rec in self:
            rec.stock_value = 0
            if rec.type != 'product':
                continue
            svl = rec.stock_valuation_layer_ids
            rec.stock_value = sum(svl.mapped('value'))
            return rec.stock_value

    def action_view_svl(self):
        action = self.env.ref('stock_account.stock_valuation_layer_action').read()[0]
        action['domain'] = [('product_id', 'in', self.ids)]
        action['context'] = {
            'active_id': self._context.get('active_id'),
        }
        return action

    def update_stock_valuation(self):
        stock_value_true = self.standard_price * self.qty_available
        stock_value_now = self._compute_total_value()
        if stock_value_true == stock_value_now:
            pass
        else:
            svl = self.stock_valuation_layer_ids
            value = stock_value_true - stock_value_now
            # time_data = svl.filtered(lambda x: x.value != 0).mapped('date')
            # print('Time:     ', time_data[0].replace(hour=0, minute=0, second=0))
            date = datetime(year=2023, month=3, day=31, hour=0, minute=0, second=0)
            svl.create({
                'product_id': self.id,
                'company_id': self.env.company.id,
                'value': value,
                'description': 'Bổ sung giá trị tồn kho theo giá vốn và số lượng onhand',
                'date': date
            })

    def action_update_stock_valuation_layers(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['product.product'].browse(selected_ids)
        for rec in selected_records:
            if rec.type == 'product':
                rec.update_stock_valuation()
