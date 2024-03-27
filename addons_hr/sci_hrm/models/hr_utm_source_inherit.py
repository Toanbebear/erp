from odoo import fields, models, api


class UTMSource(models.Model):
    _inherit = 'utm.source'
    _description = 'Description'

    flag = fields.Boolean(string="Is source job", default=False)
