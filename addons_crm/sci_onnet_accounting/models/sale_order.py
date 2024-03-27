from odoo import models, fields, api
from datetime import datetime
import pytz
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_date = fields.Datetime('Ngày xác nhận')

    def create_invoice_product(self):
        order_done = self.env['sale.order'].sudo().search([('pricelist_type', '=', 'product'), ('state', 'in', ['sale', 'done']), ('date_order', '>=', '2023/04/01'), ('invoice_status', '!=', 'invoiced')])
        for order in order_done:
            id = order.company_id.id
            a = order.partner_id.with_context(force_company=id).property_account_receivable_id.company_id.id
            if a and a == id:
                if not order.invoice_ids or (('cancel' in order.invoice_ids.mapped('state')) and (len(set(order.invoice_ids.mapped('state'))) == 1)):
                    journal_id = self.env['account.journal'].sudo().search([('company_id', '=', order.company_id.id), ('type', '=', 'sale')])
                    if journal_id:
                        invoice_date = order.date_order
                        if order.invoice_date:
                            invoice_date = order.invoice_date
                        invoice = order.with_context(force_company=order.company_id.id)._create_invoices(journal_id=journal_id.id, invoice_date=invoice_date)
                        invoice.invoice_origin = invoice.invoice_origin + '(SP)'
                        invoice.order_id = order.id
                        invoice.with_context(force_company=invoice.company_id.id).action_post()