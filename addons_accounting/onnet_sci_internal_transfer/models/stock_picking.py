# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    intercompany_transfer = fields.Boolean(string=_('Intercompany transfer'))
    receiving_company = fields.Many2one('res.company', string=_('Receiving company'))
    transfer_company = fields.Many2one('res.company', string=_('Transfer company'))
    transfer_picking = fields.Many2one('stock.picking', string=_('Transfer picking'))
    intercompany_transfer_inbound = fields.Boolean(string=_('Intercompany transfer/Inbound'), default=False)
    status_processed = fields.Char(string=_('Trạng thái xử lý chênh lệch'), compute="_compute_status_processed", default=_('Đang xử lý'), store=True)
    other_company_location_dest_id = fields.Many2one('stock.location', _("Destination Location"), states={'draft': [('readonly', False)]})

    @api.depends('move_ids_without_package')
    def _compute_status_processed(self):
        self.set_status_processed()
    @api.onchange('move_ids_without_package')
    def _onchange_move_ids_without_package(self):
        self.set_status_processed()

    @api.onchange('intercompany_transfer')
    def _onchange_intercompany_transfer(self):
        for rec in self:
            if rec.intercompany_transfer:
                customer_location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
                rec.location_dest_id = customer_location

    def set_status_processed(self):
        for rec in self:
            status_processed_done = 0
            for mi in rec.move_ids_without_package:
                if mi.is_processed:
                    status_processed_done += 1
            if status_processed_done > 0:
                rec.status_processed = _('Đã xử lý')
            else:
                rec.status_processed = _('Đang xử lý')

    def action_done(self):
        res = super(StockPickingInherit, self).action_done()
        for item in self:
            picking = self.sudo().search([('transfer_picking', '=', item.id)])
            journal = self.sudo().company_id.journal_internal_transfer_product_id
            if item.intercompany_transfer and item.receiving_company.sudo() and not picking and item.state == "done":
                if not journal.id:
                    raise ValidationError(_('Không có sổ nhật ký điều chuyển nội bộ'))
                company_id = item.receiving_company.id
                picking_type = item.env['stock.picking.type'].sudo().search(
                    [('company_id', '=', company_id), ('code', '=', 'incoming')], limit=1)
                vendor_location = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
                picking = self.sudo().create({
                    'company_id': item.receiving_company.id,
                    'picking_type_id': picking_type.id,
                    'intercompany_transfer': False,
                    'transfer_company': item.company_id.id,
                    'location_id': vendor_location.id,
                    'location_dest_id': item.other_company_location_dest_id.id,
                    'state': 'assigned',
                    'transfer_picking': item.id,
                    'intercompany_transfer_inbound': True,
                    'origin': f'{item.company_id.name}: {item.name}'
                })

                for move in item.move_ids_without_package:
                    standard_price = move.product_id.sudo().with_context(allowed_company_ids=[move.company_id.id]).standard_price
                    # fill standard price from tranfer company when create INT receipt to IN receipt received company
                    stock_move = move.sudo().copy({
                        'company_id': item.receiving_company.id,
                        'location_id': vendor_location.id,
                        'location_dest_id': item.other_company_location_dest_id.id,
                        'picking_id': picking.id,
                        'state': 'assigned',
                        'price_unit': standard_price

                    })
                    for move_line in move.move_line_ids:
                        stock_move_line = move.move_line_ids.sudo().copy({
                            'company_id': item.receiving_company.id,
                            'picking_id': picking.id,
                            'state': 'assigned',
                            'move_id': stock_move.id,
                            'qty_done': move_line.qty_done,
                            'location_id': vendor_location.id,
                            'location_dest_id': item.other_company_location_dest_id.id,
                        })
                        # Nợ TK output, có TK valuation lấy từ product category
                        vals = [[0,6,{
                                "account_id": move_line.product_id.categ_id.with_context(allowed_company_ids=[item.company_id.id]).property_stock_account_output_categ_id.id,
                                "product_id": move_line.product_id.id,
                                "debit": move_line.product_id.standard_price * move_line.qty_done,
                            }

                        ],[
                            0,6,{
                                "account_id": move_line.product_id.categ_id.with_context(allowed_company_ids=[item.company_id.id]).property_stock_valuation_account_id.id,
                                "product_id": move_line.product_id.id,
                                "credit": move_line.product_id.standard_price * move_line.qty_done,
                            }
                        ]]

                        account_move = self.env['account.move'].with_context(default_journal_id=journal.id).sudo().create({
                            "ref": 'Điều chuyển nội bộ ' + item.company_id.name + ' tới ' + item.receiving_company.name + ' - ' + picking.name,
                            "company_id": item.company_id.id,
                            "journal_id": journal.id,
                            "line_ids": vals,
                            "stock_picking_id": item.id
                        })
            elif item.transfer_picking.sudo() and item.state == "done":
                if not journal.id:
                    raise ValidationError(_('Không có sổ nhật ký điều chuyển nội bộ'))
                transfer_company = item.transfer_picking.sudo().company_id
                for stock_mone_line in item.move_line_ids_without_package:
                    # get price from stock move when the delivery receipt (INT) is confirmed
                    price_product = stock_mone_line.move_id.price_unit
                    # Nợ TK valuation, Có TK phải trả trung gian
                    vals = [[0,6,{
                            "account_id": stock_mone_line.product_id.categ_id.with_context(allowed_company_ids=[item.company_id.id]).property_stock_valuation_account_id.id,
                            "product_id": stock_mone_line.product_id.id,
                            "debit": price_product * stock_mone_line.qty_done,
                        }],[0,6,{
                            "account_id": item.company_id.x_internal_payable_account_id.id,
                            "product_id": stock_mone_line.product_id.id,
                            "credit": price_product * stock_mone_line.qty_done,
                            "partner_id": transfer_company.partner_id.id
                        }
                    ]]
                    account_move = self.env['account.move'].sudo().create({
                        "ref": 'Điều chuyển nội bộ ' + transfer_company.name + ' tới ' + item.company_id.name + ' - ' + item.name,
                        "company_id": item.company_id.id,
                        "journal_id": journal.id,
                        "stock_picking_id": item.id,
                        "line_ids": vals
                    })

        # reason comment: Price from the delivery company added to stock_move in IN receipt and price will recompute follow base Odoo flow when confirming IN receipt

                # product_B = stock_mone_line.product_id.with_context(allowed_company_ids=[item.company_id.id])
                # product_A = stock_mone_line.product_id.sudo().with_context(allowed_company_ids=[transfer_company.id])
                # old_standard_price = product_B.standard_price
                # standard_price = (product_B.standard_price*(product_B.qty_available - stock_mone_line.qty_done) + product_A.standard_price * stock_mone_line.qty_done)/product_B.qty_available

                # product_B.sudo().write({
                #     "standard_price": standard_price
                # })

                # Handle stock valuation layers.
                # svl_vals_list = []
                # company_id = self.env.company
                # if product_B.cost_method not in ('standard', 'average'):
                #     return res
                # quantity_svl = product_B.sudo().quantity_svl
                # if float_is_zero(quantity_svl, precision_rounding=product_B.uom_id.rounding):
                #     return res
                # diff = standard_price - old_standard_price
                # value = company_id.currency_id.round(quantity_svl * diff)
                # if company_id.currency_id.is_zero(value):
                #     return res

                # svl_vals = {
                #     'company_id': company_id.id,
                #     'date': fields.Datetime.now(),
                #     'product_id': product_B.id,
                #     'description': _('Product value modified due to internal transfer (from %s to %s)') % (
                #     old_standard_price, standard_price),
                #     'value': value,
                #     'quantity': 0,
                # }
                # svl_vals_list.append(svl_vals)
                # stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)
        return res



    def action_journal_entries(self):

        return {
            'name': _('Journal entries'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': ['|', ('stock_picking_id', 'in', self.ids), ('stock_move_id.picking_id', 'in', self.ids)],
        }

    @api.onchange('intercompany_transfer', 'receiving_company')
    def _onchange_receiving_company(self):
        res = {'domain': {'other_company_location_dest_id': []}, 'context': {'other_company_location_dest_id': {}}}
        if self.intercompany_transfer and self.receiving_company:
            res['domain']['other_company_location_dest_id'] = [
                ('company_id', '=', self.receiving_company.id)]
            self.with_context(default_company_id=self.receiving_company.id).other_company_location_dest_id = True
        else:
            res['domain']['other_company_location_dest_id'] = [
                ('company_id', '=', self.company_id.id)]
        return res

    def _check_company(self, fnames=None):
        if not (self.intercompany_transfer or self.transfer_picking):
            super(StockPickingInherit, self)._check_company(fnames)

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    the_difference = fields.Boolean('Chênh lệch', compute='_compute_the_difference', store=True, default=False)
    is_processed = fields.Boolean('Đã xử lý', compute='_compute_the_difference', default=False, store=True)

    # @api.model
    # def get_values(self):
    #     res = super(StockMoveInherit, self).get_values()
    #     return res
    #
    # def set_values(self):
    #     super(StockMoveInherit, self).set_values()
    #
    #     stock_move = self.env['stock.move'].search([])
    #     for rec in stock_move:
    #         if rec.product_uom_qty == rec.quantity_done:
    #             the_difference = False
    #             is_processed = True
    #         else:
    #             the_difference = True
    #             is_processed = False
    #         rec.write({'the_difference': the_difference, 'is_processed': is_processed})

    @api.depends('product_uom_qty', 'quantity_done')
    def _compute_the_difference(self):
        self.set_the_difference()

    @api.onchange('product_uom_qty', 'quantity_done')
    def _onchange_the_difference(self):
        self.set_the_difference()

    def set_the_difference(self):
        for rec in self:
            if rec.product_uom_qty == rec.quantity_done:
                rec.the_difference = False
                rec.is_processed = True
            else:
                rec.the_difference = True
                rec.is_processed = False

    def _check_company(self, fnames=None):
        v = False
        for picking in self.picking_id:
            if not (picking.intercompany_transfer or picking.transfer_picking):
                v = True
        if v:
            super(StockMoveInherit, self)._check_company(fnames)

    def _sanity_check_for_valuation(self):
        v = False
        for move in self:
            if not (move.picking_id.intercompany_transfer or move.picking_id.transfer_picking):
                v = True
        if v:
            super(StockMoveInherit, self)._sanity_check_for_valuation()

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        v = True
        for move in self:
            if not (move.picking_id.intercompany_transfer or move.picking_id.transfer_picking):
                v = False
        if v:
            self = self.sudo()
        return super(StockMoveInherit, self)._prepare_move_line_vals(quantity, reserved_quant)

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        if not (self.picking_id.intercompany_transfer or self.picking_id.transfer_picking):
            super(StockMoveInherit, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)

class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    def write(self, vals):
        v = True
        for line in self:
            if not (line.picking_id.intercompany_transfer or line.picking_id.transfer_picking):
                v = False
        if v:
            self = self.sudo()
        return super(StockMoveLineInherit, self).write(vals)
