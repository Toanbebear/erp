import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class InheritScriptSMS(models.Model):
    _inherit = 'script.sms'

    has_zns = fields.Boolean(string='ZNS', default=False, help='Tạo tin nhắn zns')
    zns_template_id = fields.Integer(string='ZNS template ID CS')
