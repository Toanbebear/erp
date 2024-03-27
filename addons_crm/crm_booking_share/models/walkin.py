
from datetime import datetime

from odoo import models, fields, api, SUPERUSER_ID


class WalkinShare(models.Model):
    _inherit = "sh.medical.appointment.register.walkin"
    _description = "Phiếu khám thuê phòng mổ"

    @api.depends('sale_order_id.amount_total', 'sale_order_id.amount_remain', 'sale_order_id.amount_owed', 'sale_order_id.partner_company')
    def _check_missing_money(self):
        for record in self.with_env(self.env(su=True)):
            record.is_missing_money = True
            if record.sale_order_id.partner_company and record.state not in ['Completed', 'Cancelled']:
                record.is_missing_money = False
                record.set_to_progress()
            elif (record.state not in ['Completed']) and (
                    record.sale_order_id.state in ['draft', 'sent']) and (record.sale_order_id.amount_total > 0) \
                    and (record.sale_order_id.amount_total > (
                    record.sale_order_id.amount_remain + record.sale_order_id.amount_owed)):
                record.is_missing_money = True
            else:
                if record.state in ['WaitPayment', 'Scheduled']:
                    record.set_to_progress()
                record.is_missing_money = False

    # Tạm thời ẩn để phục vụ test 25032023
    # A Thach fix sau
    # def set_to_completed(self):
    #     res = super(WalkinShare, self).set_to_completed()
    #
    #     print("###############################################")
    #     print(self.sale_order_id)
    #     print("###############################################")
    #
    #     # Get Purchase res.partner company
    #     po_res_partner_company_id = self.sale_order_id.partner_id
    #
    #     # Get Purchase res.company company
    #
    #     po_res_company_id = self.env['res.company'].search([
    #         ('partner_id', '=', po_res_partner_company_id.id)], limit=1)
    #     # Get Partner company
    #     po_partner_id = self.sale_order_id.company_id.partner_id
    #     print(po_res_partner_company_id)
    #     print(po_res_partner_company_id.name)
    #     print(po_res_company_id)
    #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    #     print(po_partner_id)
    #     print(po_partner_id.name)
    #     # book_share_product_id = self.with_user(SUPERUSER_ID).env['product.product'].search([
    #     #     ('default_booking_share', '=', True)
    #     # ], limit=1)
    #     #
    #     # print(book_share_product_id)
    #     # print(book_share_product_id.name)
    #
    #     po_order_line = []
    #     for line_id in self.sale_order_id.order_line:
    #         po_order_line.append(
    #             (0, 0, {
    #                 'name': line_id.product_id.name,
    #                 'product_id': line_id.product_id.id,
    #                 'product_qty': line_id.product_uom_qty,
    #                 'product_uom': line_id.product_uom.id,
    #                 'price_unit': line_id.price_unit,
    #                 'date_planned': datetime.today()
    #             })
    #         )
    #
    #     po_id = self.with_user(SUPERUSER_ID).env['purchase.order'].create({
    #         'company_id': po_res_company_id.id,
    #         'partner_id': po_partner_id.id,
    #         'origin': self.sale_order_id.name + ' ' + self.name + ' ' + self.booking_id.name,
    #         'date_order': self.sale_order_id.date_order,
    #         'order_line': po_order_line
    #     })
    #
    #     # Confirm Purchase order
    #     po_id.button_confirm()
    #
    #     print(po_id)
    #     print(po_id.name)
    #
    #     print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
    #
    #     return res
