from odoo import fields, models


class ResCountry(models.Model):
    _inherit = 'res.country'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=10, index=True)
    active = fields.Boolean('Active', default=True)
