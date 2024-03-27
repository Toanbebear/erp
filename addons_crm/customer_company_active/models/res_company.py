from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    active = fields.Boolean('Active', default=True)
