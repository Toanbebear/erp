# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from odoo import models, api, fields

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None

email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
phone_number_validator = re.compile("^[0-9/]*$")
_logger = logging.getLogger(__name__)


class LoyaltyCard(models.Model):
    _inherit = "crm.loyalty.card"

    survey_id = fields.Many2one('survey.survey', compute='generate_survey')

    @api.constrains('brand_id', 'company_id')
    def generate_survey(self):
        if self.brand_id.survey_id:
            self.survey_id = self.brand_id.survey_id
        else:
            if self.company_id.survey_kn_id:
                self.survey_id = self.company_id.survey_kn_id





