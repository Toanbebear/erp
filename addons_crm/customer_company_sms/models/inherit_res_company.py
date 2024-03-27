from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    health_declaration = fields.Char('Khai báo y tế')