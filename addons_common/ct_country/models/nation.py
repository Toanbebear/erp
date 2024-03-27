from odoo import fields, models


class Nation(models.Model):
    _inherit = 'nation'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=10, index=True)
    active = fields.Boolean('Active', default=True)
