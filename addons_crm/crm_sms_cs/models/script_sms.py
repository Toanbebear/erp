import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class InheritScriptSMS(models.Model):
    _inherit = 'script.sms'

    # type = fields.Selection(selection_add=[('NLTK', 'Nhắc lịch tái khám'),
    #                                        ('CSKHDTCOVID', 'Chăm sóc khách hàng mắc Covid')])

    has_sms = fields.Boolean(string='SMS', default=True, help='Tạo tin nhắn sms')
    has_zns = fields.Boolean(string='ZNS', default=False, help='Tạo tin nhắn zns')
