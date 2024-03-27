from odoo import models, fields, api
from datetime import date

class CrmDebtWarning(models.TransientModel):
    _name = 'crm.debt.warning'
    _description = 'Cảnh báo ấn đã trả trong duyệt nợ'

    crm_debt_id = fields.Many2one('crm.debt.review')
    collaborator_name = fields.Char('Tên CTV')
    crm_name = fields.Char('Mã Booking')
    warning = fields.Char('Cảnh báo', compute='compute_warning')

    @api.depends('collaborator_name','crm_name')
    def compute_warning(self):
        for rec in self:
            rec.warning = "Lưu ý: Khi ấn nút 'XÁC NHẬN' hệ thống sẽ tạo hoa hồng của dịch vụ cho " + rec.collaborator_name + " của " + rec.crm_name

    def confirm(self):
        order_line_id = self.env['sale.order.line'].sudo().search([('crm_line_id', '=', self.crm_debt_id.crm_line.id)], limit=1)
        self.crm_debt_id.paid = True
        order_line_id.order_id.amount_owed -= self.crm_debt_id.amount_owed
        order_line_id.amount_owed = 0
        self.crm_debt_id.color = 0
        if self.crm_debt_id.crm_line:
            self.crm_debt_id.crm_line.amount_owed = 0
        elif self.crm_debt_id.line_product:
            self.crm_debt_id.line_product.amount_owed = 0
        self.env['sale.order.debt'].sudo().create({
            'product_id': self.crm_debt_id.crm_line.product_id.id,
            'uom_price': self.crm_debt_id.crm_line.uom_price,
            'product_uom_qty': self.crm_debt_id.crm_line.quantity,
            'price_subtotal': self.crm_debt_id.crm_line.total,
            'amount_owned': self.crm_debt_id.crm_line.amount_owed,
            'amount_paid': self.crm_debt_id.amount_owed,
            'record_date': date.today(),
            'sale_order_id': order_line_id.order_id.id,
            'sale_order_line_id': order_line_id.id,
        }).confirm_debt_ctv()
