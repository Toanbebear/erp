from odoo import fields, models


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'
    _order = 'sequence'

    sequence = fields.Integer('Sequence', default=10, index=True,required=True)

