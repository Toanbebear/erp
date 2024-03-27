import json
import logging
from datetime import datetime

import requests

from odoo import fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'utm.source'

    check_sync_seeding = fields.Boolean('Check đồng bộ nguồn seeding')
    check_sync_ctv = fields.Boolean('Check đồng bộ nguồn CTV')