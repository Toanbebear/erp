# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from odoo import fields, models

email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
_logger = logging.getLogger(__name__)


def dict_keys_startswith(dictionary, string):
    """Returns a dictionary containing the elements of <dict> whose keys start with <string>.
        .. note::
            This function uses dictionary comprehensions (Python >= 2.7)
    """
    return {k: v for k, v in dictionary.items() if k.startswith(string)}


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    survey_creator = fields.Many2one('res.users', 'Creator')
    crm_lead = fields.Many2many('crm.lead', string='CRM Lead')
    company = fields.Many2one(related='survey_id.company_id')


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'
