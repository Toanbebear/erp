from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class DebtReviewInherit(models.Model):
    _inherit = 'crm.debt.review'

    collaborator_id = fields.Many2one(related='booking_id.collaborator_id')
    def paid_debt(self):
        # if 'ctv' in self.booking_id.source_id.name.lower():
        if self.booking_id.source_id.is_collaborator:
            return {
                'name': 'Xác nhận đã trả',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('sale_order_extend.crm_debt_warning_form_view').id,
                'res_model': 'crm.debt.warning',
                'context': {'default_crm_debt_id': self.id,
                            'default_collaborator_name': self.collaborator_id.name if self.collaborator_id else '',
                            'default_crm_name': self.booking_id.name if self.booking_id else ''},
                'target': 'new',
            }
        else:
            order_line_id = self.env['sale.order.line'].sudo().search([('crm_line_id', '=', self.crm_line.id)], limit=1)
            self.paid = True
            order_line_id.order_id.amount_owed -= self.amount_owed
            order_line_id.amount_owed = 0
            self.color = 0
            if self.crm_line:
                self.crm_line.amount_owed = 0
            elif self.line_product:
                self.line_product.amount_owed = 0
            self.env['sale.order.debt'].sudo().create({
                'product_id': self.crm_line.product_id.id,
                'uom_price': self.crm_line.uom_price,
                'product_uom_qty': self.crm_line.quantity,
                'price_subtotal': self.crm_line.total,
                'amount_owned': self.crm_line.amount_owed,
                'amount_paid': self.amount_owed,
                'record_date': date.today(),
                'sale_order_id': order_line_id.order_id.id
            })

    def roll_back(self):
        # if 'ctv' in self.booking_id.source_id.name.lower():
        if self.booking_id.source_id.is_collaborator:
            order_line_id = self.env['sale.order.line'].sudo().search([('crm_line_id', '=', self.crm_line.id)], limit=1)
            self.paid = False
            order_line_id.order_id.amount_owed += self.amount_owed
            order_line_id.amount_owed = self.amount_owed
            if self.crm_line:
                self.crm_line.amount_owed = self.amount_owed
            elif self.line_product:
                self.line_product.amount_owed = self.amount_owed
            self.env['sale.order.debt'].sudo().create({
                'product_id': self.crm_line.product_id.id,
                'uom_price': self.crm_line.uom_price,
                'product_uom_qty': self.crm_line.quantity,
                'price_subtotal': self.crm_line.total,
                'amount_owned': self.crm_line.amount_owed,
                'amount_paid': 0 - self.amount_owed,
                'record_date': date.today(),
                'sale_order_id': order_line_id.order_id.id,
                'sale_order_line_id': order_line_id.id,
            }).roll_back_debt()
        else:
            order_line_id = self.env['sale.order.line'].sudo().search([('crm_line_id', '=', self.crm_line.id)], limit=1)
            self.paid = False
            order_line_id.order_id.amount_owed += self.amount_owed
            order_line_id.amount_owed = self.amount_owed
            if self.crm_line:
                self.crm_line.amount_owed = self.amount_owed
            elif self.line_product:
                self.line_product.amount_owed = self.amount_owed
            self.env['sale.order.debt'].sudo().create({
                'product_id': self.crm_line.product_id.id,
                'uom_price': self.crm_line.uom_price,
                'product_uom_qty': self.crm_line.quantity,
                'price_subtotal': self.crm_line.total,
                'amount_owned': self.crm_line.amount_owed,
                'amount_paid': 0 - self.amount_owed,
                'record_date': date.today(),
                'sale_order_id': order_line_id.order_id.id,
                'sale_order_line_id': order_line_id.id,
            })