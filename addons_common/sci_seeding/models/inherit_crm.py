import json
import logging
from datetime import datetime

import requests

from odoo import fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    user_seeding = fields.Many2one('seeding.user', string='Nhân viên seeding')