from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DebtReviewInherit(models.Model):
    _inherit = 'crm.debt.review'

    debt_type = fields.Selection([('product', 'Sản phẩm'), ('service', 'Dịch vụ')], string='Duyệt nợ cho ...')
    crm_line = fields.Many2one('crm.line', string='Dịch vụ',
                               domain="[('crm_id', '=', booking_id), ('stage', 'in', ['new', 'processing'])]")
    line_product = fields.Many2one('crm.line.product', string='Sản phẩm',
                                   domain="[('booking_id', '=', booking_id),('stage_line_product', 'in', ['new', 'processing'])]")
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', related='booking_id.currency_id')
    total = fields.Monetary('Tổng tiền phải thu')
    amount_remain = fields.Monetary('Tổng tiền chưa sử dụng')

    @api.onchange('crm_line', 'line_product')
    def get_total_and_amount_remain(self):
        self.total = 0
        self.amount_remain = 0
        if (self.debt_type == 'product') and self.line_product:
            if self.line_product.amount_owed != 0:
                raise ValidationError('Sản phẩm này đã được duyệt nợ trước đó rồi')
            else:
                self.total = self.line_product.total
                self.amount_remain = self.line_product.remaining_amount
        elif (self.debt_type == 'service') and self.crm_line:
            if self.crm_line.amount_owed != 0:
                raise ValidationError('Không thể tạo duyệt nợ cho dịch vụ này! \n Lí do: Dịch vụ đã được duyệt nợ trước đó rồi!')
            else:
                self.total = self.crm_line.total
                self.amount_remain = self.crm_line.remaining_amount

    def set_approve(self):
        res = super(DebtReviewInherit, self).set_approve()
        if self.booking_id and (self.crm_line or self.line_product):
            self.crm_line.amount_owed = self.amount_owed if self.crm_line else False
            self.line_product.amount_owed = self.amount_owed if self.line_product else False
        return res

    def action_paid(self):
        res = super(DebtReviewInherit, self).action_paid()
        if self.crm_line:
            self.crm_line.amount_owed = False
        elif self.line_product:
            self.line_product.amount_owed = False

    def set_refuse(self):
        res = super(DebtReviewInherit, self).set_refuse()
        if self.stage == 'refuse' and self.crm_line:
            self.crm_line.amount_owed = False

