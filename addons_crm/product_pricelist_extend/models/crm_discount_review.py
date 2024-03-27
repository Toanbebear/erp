from odoo import fields, api, models, _
from lxml import etree
from odoo.exceptions import ValidationError


class DiscountReviewManager(models.Model):
    _inherit = 'crm.discount.review'

    def approve(self):
        if self.crm_line_id and self.crm_line_id.voucher_id:
            voucher_id = self.crm_line_id.voucher_id.filtered(lambda v: v.stage_voucher == 'active')
            if voucher_id:
                raise ValidationError(
                    'Tạo giảm giá sâu không thành công do dịch vụ bạn chọn có voucher đang ở trạng thái Có hiệu lực')
        user_access = self.env['res.users']
        if self.rule_discount_id:
            user_access += self.rule_discount_id.user_ids
        if self.env.user not in user_access:
            raise ValidationError('Bạn không có quyền duyệt phiếu cho mức giảm giá này!!! \n'
                                  'Để tìm hiểu chi tiết về danh sách user được duyệt, vui lòng truy cập vào mục:\n QUY TẮC GIẢM GIÁ SÂU!!!')

        if self.rule_discount_id and (self.env.user in user_access) and self.type == 'booking':
            for rec in self.crm_line_id:
                rec.total_discount_review += self.total_discount_cash
                order_id = self.env['sale.order'].search(
                    [('booking_id', '=', self.booking_id.id), ('state', '=', 'draft')])
                order_line_id = self.env['sale.order.line']
                if order_id:
                    order_line_ids = order_id.mapped('order_line')
                    order_line_id += order_line_ids.filtered(lambda l: l.crm_line_id == rec)
                    if order_line_id and ((rec.uom_price * rec.quantity) != 0):
                        order_line_id.total_discount_review = (rec.total_discount_review / (
                                    rec.quantity * rec.uom_price)) * order_line_id.uom_price
                    rec.stage = 'processing'
            self.stage_id = 'approve'
            self.color = 4
            self.user_approve = self.env.user.id
            self.crm_line_id.discount_review_id = self.id
            self.crm_line_id.stage = 'new'
        elif self.rule_discount_id and (self.env.user in user_access) and self.type == 'so' and self.order_line_id:
            if self.type_discount == 'discount_pr':
                self.order_line_id.discount += self.discount
            elif self.type_discount == 'discount_cash':
                self.order_line_id.discount_cash += self.discount
            self.stage_id = 'approve'
            self.user_approve = self.env.user.id
            self.crm_line_id.discount_review_id = self.id
        elif not self.rule_discount_id:
            raise ValidationError('Không thể duyệt giảm giá khi không có quy tắc giảm giá !!!')
        if self.rule_discount_id and self.type == 'so' and self.line_product:
            self.line_product.total_discount_review += self.total_discount_cash
            self.stage_id = 'approve'
            self.color = 4
            self.user_approve = self.env.user.id
            self.line_product.crm_discount_review = self.id
            self.line_product.stage_line_product = 'new'
