from odoo import api, fields, models


class CrmGuaranteeReason(models.Model):
    _name = 'crm.guarantee.reason'
    _description = 'Lí do bảo hành'

    default_code = fields.Char('Mã code')
    name = fields.Char('Lí do bảo hành')
    perc = fields.Float('Mức trừ KPI')
    not_totality = fields.Boolean('Tùy chọn bảo hành một phần')
    totality = fields.Boolean('Tùy chọn bảo hành toàn phần')
    # general = fields.Boolean('Bảo hành chung')