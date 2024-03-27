# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
import re

import requests

from odoo import api, fields, models, _

email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
phone_number_validator = re.compile(r'(^[+0-9]{1,3})*([0-9]{9,11}$)')
_logger = logging.getLogger(__name__)


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    # Conditional display
    is_conditional = fields.Boolean(
        string='Conditional Display', copy=False, help="""If checked, this question will be displayed only 
        if the specified conditional answer have been selected in a previous question""")
    triggering_question_id = fields.Many2one(
        'survey.question', string="Triggering Question", copy=False, compute="_compute_triggering_question_id",
        store=True, readonly=False, help="Question containing the triggering answer to display the current question.",
        domain="""[('survey_id', '=', survey_id),
                 '&', ('question_type', 'in', ['simple_choice', 'multiple_choice']),
                 '|',
                     ('sequence', '<', sequence),
                     '&', ('sequence', '=', sequence), ('id', '<', id)]""")
    triggering_answer_id = fields.Many2one(
        'survey.label', string="Triggering Answer", copy=False, compute="_compute_triggering_answer_id",
        store=True, readonly=False, help="Answer that will trigger the display of the current question.",
        domain="[('question_id', '=', triggering_question_id)]")

    triggering_answer_ids = fields.Many2many('survey.label', 'survey_question_label_rel', 'question_id', 'label_id',
                                             string='Triggering answers',
                                             compute="_compute_triggering_answer_ids",
                                             store=True,
                                             readonly=False,
                                             domain="[('question_id', '=', triggering_question_id)]",
                                             help="Những câu trả lời")
    has_description = fields.Boolean(string='Định nghĩa cho đáp án')
    has_note = fields.Boolean(string='Giải thích lựa chọn')
    active = fields.Boolean(string='Có hiệu lực', default='True')
    has_icon = fields.Boolean(string='Hiển thị icon')

    @api.depends('is_conditional')
    def _compute_triggering_question_id(self):
        """ Used as an 'onchange' : Reset the triggering question if user uncheck 'Conditional Display'
            Avoid CacheMiss : set the value to False if the value is not set yet."""
        for question in self:
            if not question.is_conditional or question.triggering_question_id is None:
                question.triggering_question_id = False

    @api.depends('triggering_question_id')
    def _compute_triggering_answer_id(self):
        """ Used as an 'onchange' : Reset the triggering answer if user unset or change the triggering question
            or uncheck 'Conditional Display'.
            Avoid CacheMiss : set the value to False if the value is not set yet."""
        for question in self:
            if not question.triggering_question_id \
                    or question.triggering_question_id != question.triggering_answer_id.question_id\
                    or question.triggering_answer_id is None:
                question.triggering_answer_id = False

    @api.depends('triggering_question_id')
    def _compute_triggering_answer_ids(self):
        """ Used as an 'onchange' : Reset the triggering answer if user unset or change the triggering question
            or uncheck 'Conditional Display'.
            Avoid CacheMiss : set the value to False if the value is not set yet."""
        for question in self:
            if not question.triggering_question_id \
                    or question.triggering_question_id != question.triggering_answer_id.question_id\
                    or question.triggering_answer_id is None:
                question.triggering_answer_id = False

    def write(self, vals):
        result = super(SurveyQuestion, self).write(vals)
        if result and 'active' in vals:
            self.inactive_question()
        return result

    def inactive_question(self):
        survey = self.env['survey.survey'].sudo().browse(int(self.survey_id.id))
        brand = self.env['survey.brand.config'].search([('brand_id', '=', survey.brand_id.id)])
        url_base = brand.survey_brand_url
        token = brand.survey_brand_token
        url = url_base + "api/v1/inactive-question"
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
        }
        data = {
            'active': self.active,
            'id': self.id
        }
        response = requests.post(url, data=json.dumps(data), headers=headers)