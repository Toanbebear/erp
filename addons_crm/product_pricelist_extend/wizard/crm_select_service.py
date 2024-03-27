from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CrmSelectService(models.TransientModel):
    _inherit = 'crm.select.service'

    def create_quotation(self):
        if self.select_line_ids:
            voucher_ids = self.select_line_ids.crm_line_id.voucher_id.filtered(lambda l: l.stage_voucher == 'active')
            if voucher_ids:
                raise ValidationError('Bạn không thể tạo phiếu khám do dịch vụ bạn chọn có voucher chưa được áp dụng')
        return super(CrmSelectService, self).create_quotation()