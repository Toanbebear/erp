# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from odoo import api, fields, models, _

email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
phone_number_validator = re.compile(r'(^[+0-9]{1,3})*([0-9]{9,11}$)')
_logger = logging.getLogger(__name__)


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    # Display options
    display_mode = fields.Selection([('columns', 'Radio Buttons'),
                                     ('dropdown', 'Selection Box'),
                                     ('icon', 'Icon')],
                                    string='Display Mode', default='columns',
                                    help='Display mode of simple choice questions.')
    multiple_display_mode = fields.Selection([('columns', 'Radio Buttons'),
                                              ('icon', 'Icon')],
                                             string='Multiple Display Mode', default='columns',
                                             help='Display mode of multiple choice questions.')
    matrix_display_mode = fields.Selection([('no_icon', 'Without Icon'),
                                            ('icon', 'Icon')],
                                           string='Matrix Display Mode', default='no_icon',
                                           help='Display mode of matrix questions.')
    # Validation
    validation_phone_number = fields.Boolean('Input must be a phone number')

    column_nb = fields.Selection(selection_add=[('10', "10")])

    @api.onchange('validation_phone_number')
    def _onchange_validation_phone_number(self):
        if self.validation_phone_number:
            self.validation_required = False

    @api.onchange('display_mode')
    def _onchange_multiple_display_mode(self):
        if self.display_mode == 'icon':
            self.multiple_display_mode = 'icon'

    @api.onchange('multiple_display_mode')
    def _onchange_display_mode(self):
        if self.multiple_display_mode == 'icon':
            self.display_mode = 'icon'

    @api.onchange('matrix_display_mode')
    def _onchange_multiple_display_mode(self):
        if self.matrix_display_mode == 'icon':
            self.multiple_display_mode = 'icon'
            self.display_mode = 'icon'
        else:
            self.multiple_display_mode = 'columns'
            self.display_mode = 'columns'

    def validate_textbox(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag].strip()
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        # Email format validation
        # Note: this validation is very basic:
        #     all the strings of the form
        #     <something>@<anything>.<extension>
        #     will be accepted
        if answer and self.validation_email:
            if not email_validator.match(answer):
                errors.update({answer_tag: _('This answer must be an email address')})
        # Email format validation
        # Note: this validation is very basic:
        #     all the numbers(0-9) and + at first of the form
        #     +<**(*)><*********(**)>
        #     will be accepted
        if answer and self.validation_phone_number:
            if not phone_number_validator.match(answer):
                errors.update({answer_tag: _('This answer must be an phone number')})
        # Answer validation (if properly defined)
        # Length of the answer must be in a range
        if answer and self.validation_required:
            if not (self.validation_length_min <= len(answer) <= self.validation_length_max):
                errors.update({answer_tag: self.validation_error_msg})
        return errors


class SurveyLabel(models.Model):
    _inherit = 'survey.label'

    icon = fields.Binary('Biểu tượng', attachment=False, store=True)
