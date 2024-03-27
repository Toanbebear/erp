from odoo import fields, api, models


class InheritResUsers(models.Model):
    _inherit = 'res.users'

    brand_ip_phone_ids = fields.One2many('brand.ip.phone', 'user_id', string='IP phone')
