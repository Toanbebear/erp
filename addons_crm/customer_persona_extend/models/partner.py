from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    persona = fields.One2many('customer.persona', 'partner_id', 'Chân dung khách hàng')
    # ward_id = fields.Many2one('res.country.ward', string='Phường/xã', tracking=True)
