from odoo import models, fields
from odoo.exceptions import ValidationError
import datetime
from datetime import timedelta


class InheritSaleOrders(models.Model):
    _inherit = "sale.order"
    _description = 'Xử lý case thuê phòng mổ'

    partner_company = fields.Boolean(related="partner_id.is_company")
    
    def check_order_missing_money(self):
        if self.partner_company:
            return False
        return super(InheritSaleOrders, self).check_order_missing_money()

    def hai_create_invoice(self):
        now = datetime.datetime.now() - timedelta(days=8)
        datetime_start = datetime.datetime(now.year, now.month, now.day - 1, 17, 00, 00, 00)
        datetime_end = datetime.datetime(now.year, now.month, now.day, 16, 59, 59, 00)
        list = self.env['sale.order'].sudo().search([('state', 'in', ['sale','done']), ('date_order', '>=', datetime_start), ('date_order', '<=', datetime_end), ('pricelist_type', '!=', 'product')])
        i = 0
        if list:
            for line in list:
                i += 1
                if not line.invoice_ids or (('cancel' in line.invoice_ids.mapped('state')) and (len(set(line.invoice_ids.mapped('state'))) == 1)):
                    journal_id = self.env['account.journal'].sudo().search(
                        [('company_id', '=', line.company_id.id), ('type', '=', 'sale')])
                    if journal_id:
                        invoice = line.with_context(force_company=line.company_id.id)._create_invoices(journal_id=journal_id.id)
                        invoice.action_post()
                        invoice.ref = 'Hải'
