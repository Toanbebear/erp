# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

from ast import literal_eval


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    auto_generated = fields.Boolean(string='Auto Generated Transfer', copy=False,
                                    help="Field helps to check the picking is created from an another picking or not")

    def action_done(self):
        """Creating the internal transfer if it is not created from another picking"""
        res = super(StockPickingInherit, self).action_done()
        if not self.auto_generated:
            self.create_intercompany_transfer()
        return res

    def create_intercompany_transfer(self):
        """Creating the transfer if the selected company is enabled the internal transfer option"""
        company_id = self.env['res.company'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
        operation_type_id = False
        location_id = False
        location_dest_id = False

        if company_id and company_id.enable_inter_company_transfer and self.picking_type_id.code != 'internal':
            create_transfer = False
            if self.picking_type_id.code == company_id.apply_transfer_type or company_id.apply_transfer_type == 'all':
                 create_transfer = True
            if create_transfer:
                warehouse_ids = company_id.destination_warehouse_id.sudo()
                if self.picking_type_id.code == 'incoming':
                    operation_type_id = self.env['stock.picking.type'].sudo().search(
                        [('warehouse_id', 'in', warehouse_ids.ids), ('code', '=', 'outgoing')], limit=1)

                elif self.picking_type_id.code == 'outgoing':
                    if company_id.id == 1:
                        operation_type_id = self.sudo().company_id.region_picking_type or\
                                            self.env['stock.picking.type'].sudo().search([('warehouse_id', 'in', warehouse_ids.ids), ('code', '=', 'incoming')], limit=1)
                    else:
                        operation_type_id = self.env['stock.picking.type'].sudo().search([('warehouse_id', 'in', warehouse_ids.ids), ('code', '=', 'incoming')], limit=1)
                else:
                    raise UserError(_('Internal transfer between companies are not allowed'))

                if operation_type_id:
                    if operation_type_id.default_location_src_id:
                        location_id = operation_type_id.default_location_src_id.id
                    elif self.company_id.partner_id:
                        location_id = self.partner_id.property_stock_supplier.id

                    if operation_type_id.default_location_dest_id:
                        location_dest_id = operation_type_id.default_location_dest_id.id
                    elif company_id.partner_id:
                        location_dest_id = company_id.partner_id.property_stock_customer.id
                if location_id and location_dest_id:
                    picking_vals = {
                        'partner_id': self.company_id.partner_id.id,
                        'company_id': company_id.id,
                        'picking_type_id': operation_type_id.id,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'auto_generated': True,
                        'origin': self.name,
                        'immediate_transfer': False
                    }
                    picking_id = self.env['stock.picking'].sudo().create(picking_vals)
                else:
                    raise UserError(_('Please configure appropriate locations on Operation type/Partner'))

                for move in self.move_lines:
                    lines = move.move_line_ids
                    if lines:
                        done_qty = sum(lines.mapped('qty_done'))
                        if not done_qty:
                            done_qty = sum(lines.mapped('product_uom_qty'))
                        # Truyền price unit của cty giao hàng sang pick của cty nhận hàng
                        price_unit = move.product_id.with_context(force_company=self.company_id.id).standard_price if self.picking_type_id.code == 'outgoing' else 0
                        move_vals = {
                            'picking_id': picking_id.id,
                            'picking_type_id': operation_type_id.id,
                            'name': move.name,
                            'product_id': move.product_id.id,
                            'product_uom': move.product_uom.id,
                            'product_uom_qty': done_qty,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                            'price_unit': price_unit,
                            'company_id': company_id.id
                        }
                        # SCI: Nếu trong các move_line có 1 line có lot_id, điền thêm lot liên kết với lot của từng line tại
                        # công ty nhận hàng vào origin của stock.move để phía dưới truy xuất và điền lot cho move_line ở phiếu nhận
                        if lines.mapped('lot_id'):
                            move_vals['origin'] = {}
                            for line in lines:
                                if line.lot_id:
                                    lot_id = line.sudo().lot_id.synced_lots.filtered(lambda l: l.company_id == company_id)
                                    if not lot_id:
                                        lot_id = self.env['stock.production.lot'].sudo().create({'name': line.lot_id.name,
                                                                                                 'company_id': company_id.id,
                                                                                                 'product_id': line.product_id.id,
                                                                                                 'use_date': line.lot_id.use_date,
                                                                                                 'removal_date': line.lot_id.removal_date,
                                                                                                 'life_date': line.lot_id.life_date,
                                                                                                 'alert_date': line.lot_id.alert_date,
                                                                                                 'production_date': line.lot_id.production_date,
                                                                                                 'synced_lots': [(6, 0, (line.lot_id + line.lot_id.synced_lots).ids)]})
                                        (line.lot_id + line.lot_id.synced_lots).sudo().write({'synced_lots': [(4, lot_id.id)]})
                                    move_vals['origin'][str(lot_id.id)] = line.qty_done or line.product_uom_qty
                                else:
                                    move_vals['origin']['no_lot'] = line.qty_done or line.product_uom_qty
                            move_vals['origin'] = str(move_vals['origin'])
                        # End SCI
                        self.env['stock.move'].sudo().create(move_vals)

                if picking_id:
                    picking_id.sudo().action_confirm()
                    picking_id.sudo().action_assign()
                    # SCI: Dựa vào origin của stock.move của phiếu nhận để điền lot hoặc tạo move_line mới
                    for move_line in picking_id.move_line_ids:
                        if move_line.move_id.origin and isinstance(literal_eval(move_line.move_id.origin), dict):
                            lot_dict = literal_eval(move_line.move_id.origin)
                            if len(lot_dict) == 1:
                                move_line.lot_id = int(list(lot_dict.keys())[0])
                            else:
                                for key in lot_dict.keys():
                                    if not move_line.lot_id:
                                        move_line.write({'lot_id': int(key) if key != 'no_lot' else False,
                                                         'qty_done': lot_dict[key]})
                                    else:
                                        line_vals = {'move_id': move_line.move_id.id,
                                                     'picking_id': picking_id.id,
                                                     'lot_id': int(key) if key != 'no_lot' else False,
                                                     # 'product_uom_qty': line.product_qty,
                                                     'qty_done': lot_dict[key],
                                                     'product_id': move_line.product_id.id,
                                                     'product_uom_id': move_line.product_uom_id.id,
                                                     'location_id': location_id,
                                                     'location_dest_id': location_dest_id,
                                                     'state': 'assigned',
                                                     'company_id': company_id.id}
                                        self.env['stock.move.line'].sudo().create(line_vals)


