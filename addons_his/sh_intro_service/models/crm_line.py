from odoo import fields, models, api, _
import logging
from odoo.exceptions import ValidationError
from lxml import etree
import json

_logger = logging.getLogger(__name__)


class CrmLine(models.Model):
    _inherit = 'crm.line'

    x_company_do_service_id = fields.Many2one('res.company', string='Công ty thực hiện dịch vụ')