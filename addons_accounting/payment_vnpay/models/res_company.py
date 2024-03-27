from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    terminal_id = fields.Char(help="Mã điểm thu")
