from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Inherit partner'

    evaluation_ids = fields.One2many('sh.medical.evaluation', 'partner_id', string='Phiếu Tái khám', tracking=True)
