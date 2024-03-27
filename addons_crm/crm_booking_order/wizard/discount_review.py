from odoo import fields, api, models
from lxml import etree
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import datetime, date, timedelta
import json
from dateutil.relativedelta import relativedelta
import pytz


class DiscountReview(models.TransientModel):
    _inherit = 'discount.review'

    line_product = fields.Many2one('crm.line.product', string='Dòng sản phẩm',
                                   domain="[('booking_id','=',booking_id),"
                                          " ('stage_line_product', '=', 'new'),"
                                          " ('crm_discount_review', '=', False)]")

    def _get_rv_data(self):
        res = super(DiscountReview, self)._get_rv_data()
        if self.type == 'so':
            res['line_product'] = self.line_product.id
            res['type'] = 'so'
            res['total_amount_before_deep_discount'] = self.line_product.total
        return res

    def offer(self):
        res = super(DiscountReview, self).offer()
        if self.line_product:
            self.line_product.stage_line_product = 'waiting'

    @api.constrains('type', 'discount', 'type_discount')
    def error_discount_product(self):
        for record in self:
            if record.type == 'so' and record.line_product:
                if (record.type_discount == 'discount_pr') and (record.discount <= 0 or record.discount > 100):
                    raise ValidationError('Chỉ nhận giảm giá trong khoảng từ 0 đến 100 !!!')
                elif (record.type_discount == 'discount_pr') and ((record.discount > record.rule_discount_id.discount2) or (record.discount < record.rule_discount_id.discount)):
                    raise ValidationError('Giảm giá đề xuất không thỏa mãn quy tắc giảm giá bạn chọn !!!')
                elif (record.type_discount == 'discount_cash') and (record.line_product.total < record.discount):
                    raise ValidationError(
                        'Số tiền xin duyệt giảm giá đang lớn hơn tổng tiền phải thu của line dịch vụ !!!')
                elif (record.type_discount == 'discount_cash') and ((
                        round((record.discount / record.line_product.total_before_discount) * 100,
                              6) > record.rule_discount_id.discount2) or (
                        round((record.discount / record.line_product.total_before_discount) * 100,
                              6) < record.rule_discount_id.discount)):
                    raise ValidationError('Tổng giảm giá xin duyệt của line dịch vụ này '
                                          'không thỏa mãn quy tắc giảm giá bạn chọn !!!')

