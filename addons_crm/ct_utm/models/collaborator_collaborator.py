import logging

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class Collaborator(models.Model):
    _inherit = 'collaborator.collaborator'

    source_id = fields.Many2one('utm.source', string='Nguồn cho Lead/Booking',
                                domain="[('is_collaborator', '=', True), ('brand_id', '=', brand_id)]",
                                help='Nguồn của lead/booking khi lead/booking phát sinh từ cộng tác viên',
                                tracking=True)
