from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    emergency_phone = fields.Char('Số điện thoại khẩn cấp')