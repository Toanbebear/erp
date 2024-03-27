from odoo import fields, models


class InheritPartner(models.Model):
    _inherit = 'res.partner'

    height = fields.Float('Chiều cao (cm)')
    weight = fields.Float('Cân nặng (kg)')
