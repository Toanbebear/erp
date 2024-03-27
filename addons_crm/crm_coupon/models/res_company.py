from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    roi_rate = fields.Float('Tỷ lệ ROI')
