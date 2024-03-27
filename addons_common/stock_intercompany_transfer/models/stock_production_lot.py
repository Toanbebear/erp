# -*- coding: utf-8 -*-
###################################################################################
# SCI
###################################################################################

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class StockProductionLotInherit(models.Model):
    _inherit = 'stock.production.lot'

    synced_lots = fields.Many2many('stock.production.lot', 'stock_production_lot_lot_rel', 'original_id', 'other_id', string='Synced lots')
    production_date = fields.Datetime('Ngày sản xuất')

    @api.model
    def create(self, vals):
        # Khi tạo 1 lô, check xem có lô khác cùng tên và sản phẩm tồn tại không, nếu khác các ngày hạn thì chặn, trùng thì liên kết
        if not vals.get('synced_lots') or not vals.get('synced_lots')[0][2]:
            similar_lots = self.sudo().search([('name', '=', vals.get('name')), ('product_id', '=', vals.get('product_id'))])
            if similar_lots:
                def to_dt(dt_str):
                    # Quy đổi str / datetime sang datetime để so sánh
                    return fields.Datetime.to_datetime(vals.get(dt_str)) or False  # trường hợp None sẽ đổi thành False để so sánh
                if to_dt('use_date') != similar_lots[0].use_date or \
                        to_dt('removal_date') != similar_lots[0].removal_date or \
                        to_dt('life_date') != similar_lots[0].life_date or \
                        to_dt('alert_date') != similar_lots[0].alert_date or \
                        to_dt('production_date') != similar_lots[0].production_date:
                    raise UserError('Đã có Lô sản phẩm cùng tên được tạo với ngày khác - %s.' % (vals.get('name')))
                else:
                    vals['synced_lots'] = [(6, 0, similar_lots.ids)]
            res = super(StockProductionLotInherit, self).create(vals)
            similar_lots.write({'synced_lots': [(4, res.id)]})
            return res
        return super(StockProductionLotInherit, self).create(vals)

    def write(self, vals):
        # Check khi write xem có trùng lô và sản phẩm với lô nào khác không
        if vals.get('name') or vals.get('product_id'):
            for record in self:
                name = vals.get('name') or record.name
                product_id = vals.get('product_id') or record.product_id.id
                if self.env['stock.production.lot'].search([('name', '=', name), ('product_id', '=', product_id)]):
                    raise UserError('Đã có Lô sản phẩm cùng tên được tạo.')
        # Write các trường ngày, tên và sản phẩm đến các lô liên kết khi write ở một lô
        res = super(StockProductionLotInherit, self).write(vals)
        synced_fields = ['use_date', 'removal_date', 'life_date', 'alert_date', 'production_date', 'name', 'product_id']
        synced_vals = {field: vals.get(field) for field in synced_fields if vals.get(field)}
        for record in self:
            if synced_vals and not self.env.context.get('synced_lots'):
                record.synced_lots.sudo().with_context(synced_lots=True).write(synced_vals)
        return res
