from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DiscountReview(models.TransientModel):
    _inherit = 'discount.review'

    def offer(self):
        if self.crm_line_id and self.crm_line_id.voucher_id:
            voucher_id = self.crm_line_id.voucher_id.filtered(lambda v: v.stage_voucher == 'active')
            if voucher_id:
                raise ValidationError('Tạo giảm giá sâu không thành công do dịch vụ bạn chọn có voucher đang ở trạng thái Có hiệu lực')