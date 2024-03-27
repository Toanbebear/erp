from odoo.exceptions import ValidationError
from odoo import fields, models, api, _

STAGE = {
    'new': 'Mới',
    'active': 'Có hiệu lực',
    'used': 'Đã sử dụng',
    'expire': 'Hết hạn'
}


class CrmVoucher(models.Model):
    _inherit = 'crm.voucher'

    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.stage_voucher:
                name = rec.name + ' - ' + STAGE[rec.stage_voucher]
                result.append((rec.id, name))
            else:
                name = rec.name
                result.append((rec.id, name))
        return result
