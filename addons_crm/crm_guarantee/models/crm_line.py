from odoo import fields, api, models


class LoyaltyCrmLine(models.Model):
    _inherit = 'crm.line'

    reason_guarantee_id = fields.Many2one('crm.guarantee.reason', string='Lí do bảo hành')
    type_guarantee_2 = fields.Selection([('not_totality', 'Một phần'), ('totality', 'Toàn phần')], string='Loại bảo hành')
    user_guarantee = fields.Many2one('sh.medical.physician', string='Nhân sự/Bác sĩ bị bảo hành')