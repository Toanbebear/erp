from odoo import models, fields, api


class ShService(models.Model):
    _inherit = "sh.medical.health.center.service"

    khong_tinh_doanh_so = fields.Boolean('Không tính vào BC doanh số?')


class CrmSalePayment(models.Model):
    _inherit = "crm.sale.payment"

    payment_method = fields.Selection(related='account_payment_id.payment_method', store=True)
    category_source_id = fields.Many2one(related='booking_id.category_source_id', string="Nhóm nguồn", store=True)
    # source_id = fields.Many2one(related='booking_id.source_id', string="Nguồn", store=True)
    # partner_type = fields.Selection(related='account_payment_id.partner_type', store=True)
    khong_tinh_doanh_so = fields.Boolean('Không tính doanh số?', related='service_id.khong_tinh_doanh_so', store=True)


class AccountMove(models.Model):
    _inherit = "account.move"

    nop_quy = fields.Boolean('Nộp/chuyển quỹ',
                             help="Vui lòng tick vào trường này nếu đây là phiếu nộp/chuyển quỹ đi các chi nhánh khác")
    thu_quy = fields.Boolean('Thu/nhận quỹ',
                             help="Vui lòng tick vào trường này nếu đây là phiếu thu/nhận quỹ từ các chi nhánh khác")
