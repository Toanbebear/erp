# -*- coding: utf-8 -*-
import json
import logging

import requests

from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class Survey(models.Model):
    _inherit = 'survey.survey'

    company_id = fields.Many2one('res.company', string='Công ty', required=False)
    brand_logo = fields.Binary('Logo thương hiệu', required=False)

    thank_you_title = fields.Char("Tiêu đề cảm ơn", translate=True,
                                  help="This title will be displayed when survey is completed")

    brand_id = fields.Many2one('res.brand', string="Thương hiệu")
    questions_layout = fields.Selection(default='page_per_section')
    questions_selection = fields.Selection(required=False)
    is_attempts_limited = fields.Boolean(default=True)

    # Cấu hình
    group_service_ids = fields.Many2many('sh.medical.health.center.service.category',
                                         'survey_survey_group_service_rel',
                                         'survey_id',
                                         'group_id',
                                         string='Nhóm dịch vụ',
                                         # domain="[('brand_id', '=', brand_id)]",
                                         help="Khảo sát sẽ sử dụng cho các nhóm dịch vụ")

    # Tiêu chí: Thời điểm + Đối tượng
    survey_time_ids = fields.Many2many('survey.survey.type',
                                       'survey_survey_type_rel',
                                       'survey_id',
                                       'time_id',
                                       string='Tiêu chí',
                                       required=True,
                                       help="Khảo sát sẽ sử dụng cho các thời điểm hay nhóm đối tượng này")

    company_ids = fields.Many2many('res.company',
                                   'survey_survey_res_company_rel',
                                   'survey_id',
                                   'company_id',
                                   domain="[('brand_id', '=', brand_id)]",
                                   string='Cấu hình công ty',
                                   help="Khảo sát cho công ty")

    @api.onchange('brand_id')
    def onchange_brand_id(self):
        if self.brand_id:
            self.company_ids = False

    # ------------------------------------------------------------
    # CONDITIONAL QUESTIONS MANAGEMENT
    # ------------------------------------------------------------

    def _get_conditional_maps(self):
        triggering_answer_by_question = {}
        triggered_questions_by_answer = {}
        triggering_question = {}
        for question in self.question_ids:
            triggering_answer_by_question[question] = question.is_conditional and question.triggering_answer_id
            if question.triggering_question_id:
                triggering_question[question.id] = question.triggering_question_id.id
            if question.is_conditional:
                for answer_id in question.triggering_answer_ids:
                    if answer_id in triggered_questions_by_answer:
                        triggered_questions_by_answer[answer_id] |= question
                    else:
                        triggered_questions_by_answer[answer_id] = question

                # if question.triggering_answer_id in triggered_questions_by_answer:
                #     triggered_questions_by_answer[question.triggering_answer_id] |= question
                # else:
                #     triggered_questions_by_answer[question.triggering_answer_id] = question
        return triggering_answer_by_question, triggered_questions_by_answer, triggering_question

    @api.model
    def next_question(self, user_input, page_or_question_id, data_trigger, go_back=False):
        """ The next page to display to the user, knowing that page_id is the id
            of the last displayed page.

            If page_id == 0, it will always return the first page of the survey.

            If all the pages have been displayed and go_back == False, it will
            return None

            If go_back == True, it will return the *previous* page instead of the
            next page.

            .. note::
                It is assumed here that a careful user will not try to set go_back
                to True if she knows that the page to display is the first one!
                (doing this will probably cause a giant worm to eat her house)
        """
        survey = user_input.survey_id

        if survey.questions_layout == 'one_page':
            return (None, False)
        elif survey.questions_layout == 'page_per_question' and survey.questions_selection == 'random':
            pages_or_questions = list(enumerate(
                user_input.question_ids
            ))
        else:
            pages_or_questions = list(enumerate(
                survey.question_ids if survey.questions_layout == 'page_per_question' else survey.page_ids
            ))

        # First page
        if page_or_question_id == 0:
            return (pages_or_questions[0][1], len(pages_or_questions) == 1)

        current_page_index = pages_or_questions.index(
            next(p for p in pages_or_questions if p[1].id == page_or_question_id))

        # All the pages have been displayed
        if current_page_index == len(pages_or_questions) - 1 and not go_back:
            return (None, False)
        # Let's get back, baby!
        elif go_back and survey.users_can_go_back:
            return (pages_or_questions[current_page_index - 1][1], False)
        else:
            # This will show the last page
            if current_page_index == len(pages_or_questions) - 2:
                return (pages_or_questions[current_page_index + 1][1], True)
            # This will show a regular page
            else:
                next_question = pages_or_questions[current_page_index + 1][1]
                questions_trigger = None
                question_trigger_id = None
                if data_trigger and 'triggering_question' in data_trigger:
                    if next_question.id in data_trigger['triggering_question']:
                        # Lấy câu hỏi trigger, kiểm tra câu trả lời
                        question_trigger_id = data_trigger['triggering_question'][next_question.id]

                answer_question_line = user_input.user_input_line_ids.filtered(
                    lambda line: line.question_id.id == question_trigger_id)
                if answer_question_line:

                    if data_trigger and 'triggered_questions_by_answer' in data_trigger:
                        if data_trigger['triggered_questions_by_answer']:
                            # Câu trả lời của khách có trong trigger, hiển thị câu hỏi
                            if answer_question_line.value_suggested.id in data_trigger['triggered_questions_by_answer']:
                                questions_trigger = data_trigger['triggered_questions_by_answer'][
                                    answer_question_line.value_suggested.id]
                if questions_trigger:
                    if next_question.id in questions_trigger:
                        print("lập tức hiển thị")
                    else:
                        index = 1

                        while next_question.id in data_trigger['triggering_answer_by_question']:
                            index += 1
                            next_question = pages_or_questions[current_page_index + index][1]

                else:
                    index = 1

                    while next_question.id in data_trigger['triggering_answer_by_question']:
                        index += 1
                        next_question = pages_or_questions[current_page_index + index][1]

                return (next_question, False)

    def _create_answer_booking(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True,
                               booking=False, group_service_id=None, survey_time_id=None, **additional_vals):
        """ Main entry point to get a token back or create a new one. This method
        does check for current user access in order to explicitely validate
        security.
          :param user: target user asking for a token; it might be void or a
                       public user in which case an email is welcomed;
          :param email: email of the person asking the token is no user exists;
        """
        self.check_access_rights('read')
        self.check_access_rule('read')
        answers = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts,
                                          invite_token=invite_token)

            answer_vals = {
                'survey_id': survey.id,
                'group_service_id': group_service_id,
                'survey_time_id': survey_time_id,
                'test_entry': test_entry,
                'question_ids': [(6, 0, survey._prepare_answer_questions().ids)]
            }
            if booking:
                # crm_lead = self.env['crm.lead'].search([('id', '=', booking)])
                crm_lead = self.env['crm.lead'].browse(int(booking))
                answer_vals['crm_lead'] = [(4, crm_lead.id)]
                answer_vals['crm_id'] = crm_lead.id

            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            answers += answers.create(answer_vals)

        return answers

    def _create_answer_walkin(self, user=False, partner=False, email=False, test_entry=False,
                              check_attempts=True, walkin_id=False, group_service_id=None, survey_time_id=None,
                              **additional_vals):

        self.check_access_rights('read')
        self.check_access_rule('read')
        answers = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts,
                                          invite_token=invite_token)

            answer_vals = {
                'survey_id': survey.id,
                'group_service_id': group_service_id,
                'survey_time_id': survey_time_id,
                'test_entry': test_entry,
                'question_ids': [(6, 0, survey._prepare_answer_questions().ids)]
            }

            if walkin_id:
                walkin = self.env['sh.medical.appointment.register.walkin'].browse(int(walkin_id))
                answer_vals['walkin_id'] = walkin.id
                answer_vals['crm_lead'] = [(4, walkin.booking_id.id)]
                answer_vals['crm_id'] = walkin.booking_id.id

            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            answers += answers.create(answer_vals)

        return answers

    def _create_answer_evaluation(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True,
                                  evaluation_id=False, group_service_id=None, survey_time_id=None,
                                  **additional_vals):

        self.check_access_rights('read')
        self.check_access_rule('read')
        answers = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts,
                                          invite_token=invite_token)

            answer_vals = {
                'survey_id': survey.id,
                'group_service_id': group_service_id,
                'survey_time_id': survey_time_id,
                'test_entry': test_entry,
                'question_ids': [(6, 0, survey._prepare_answer_questions().ids)]
            }

            if evaluation_id:
                evaluation = self.env['sh.medical.evaluation'].browse(int(evaluation_id))
                answer_vals['evaluation_id'] = evaluation.id
                answer_vals['walkin_id'] = evaluation.walkin.id
                answer_vals['crm_lead'] = [(4, evaluation.walkin.booking_id.id)]
                answer_vals['crm_id'] = evaluation.walkin.booking_id.id

            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            answers += answers.create(answer_vals)

        return answers

    def _create_answer_phone_call(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True,
                                  phone_call_id=False, group_service_id=None, survey_time_id=None,
                                  **additional_vals):

        self.check_access_rights('read')
        self.check_access_rule('read')
        answers = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts,
                                          invite_token=invite_token)

            answer_vals = {
                'survey_id': survey.id,
                'group_service_id': group_service_id,
                'survey_time_id': survey_time_id,
                'test_entry': test_entry,
                'question_ids': [(6, 0, survey._prepare_answer_questions().ids)]
            }

            if phone_call_id:
                phone_call = self.env['crm.phone.call'].browse(int(phone_call_id))
                answer_vals['phone_call_id'] = phone_call.id
                answer_vals['walkin_id'] = phone_call.medical_id.id if phone_call.medical_id else None
                answer_vals['crm_lead'] = [(4, phone_call.crm_id.id)]
                answer_vals['crm_id'] = phone_call.crm_id.id

            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            answers += answers.create(answer_vals)

        return answers

    # @api.model
    # def create(self, vals):
    #     survey = super(Survey, self).create(vals)
    #     if survey:
    #         survey.create_survey()
    #     return survey
    #
    # def write(self, vals):
    #     result = super(Survey, self).write(vals)
    #     if result:
    #         self.create_survey()
    #     return result
    #
    # def create_survey(self):
    #     brand = self.env['survey.brand.config'].search([('brand_id','=',self.brand_id.id)])
    #     url_base = brand.survey_brand_url
    #     token = brand.survey_brand_token
    #     url = url_base + "api/v1/create-survey"
    #     headers = {
    #         'Authorization': token,
    #         'Content-Type': 'application/json',
    #     }
    #     list = []
    #     for question in self.question_and_page_ids:
    #         list_triggering_answer = []
    #         list_answer = []
    #         list_matrix = []
    #         for answer in question.labels_ids:
    #             value_answer = {
    #                 'id': answer.id,
    #                 'value': answer.value,
    #                 'value_description': answer.value_description
    #             }
    #             list_answer.append(value_answer)
    #         for matrix in question.labels_ids_2:
    #             value_matrix = {
    #                 'id': matrix.id,
    #                 'value': matrix.value
    #             }
    #             list_matrix.append(value_matrix)
    #         for triggering_answer in question.triggering_answer_ids:
    #             list_triggering_answer.append(triggering_answer.id)
    #         data = {
    #             'id': question.id,
    #             'title': question.title,
    #             'question_type': question.question_type,
    #             'constr_mandatory': question.constr_mandatory,
    #             'constr_error_msg': question.constr_error_msg,
    #             'is_conditional': question.is_conditional,
    #             'triggering_question_id': question.triggering_question_id.id,
    #             'triggering_answer_ids': list_triggering_answer,
    #             'comments_allowed': question.comments_allowed,
    #             'comments_message': question.comments_message,
    #             'comment_count_as_answer': question.comment_count_as_answer,
    #             'suggested_answer_ids': list_answer,
    #             'matrix_row_ids': list_matrix,
    #             'has_description': question.has_description,
    #             'column_nb': question.column_nb,
    #             'has_note': question.has_note,
    #             'active': question.active,
    #             'sequence': question.sequence
    #         }
    #         list.append(data)
    #     data = {
    #         'id': self.id,
    #         'title': self.title,
    #         'questions_layout': self.questions_layout,
    #         'description_done': self.thank_you_message,
    #         'description': self.description,
    #         'access_mode': self.access_mode,
    #         'users_login_required': self.users_login_required,
    #         'is_attempts_limited': self.is_attempts_limited,
    #         'attempts_limit': self.attempts_limit,
    #         'questions_selection': self.questions_selection,
    #         'brand_id': self.brand_id.code,
    #         'question_ids': list
    #     }
    #
    #     response = requests.post(url, data=json.dumps(data), headers=headers)




class SurveySurveyTime(models.Model):
    _name = 'survey.survey.type'
    _description = 'Tiêu chí'

    name = fields.Char(string="Thời điểm")
    type = fields.Selection([('time', 'Thời điểm khảo sát'),
                             ('object', 'Đối tượng khảo sát')], string="Phân loại khảo sát")
    is_bk = fields.Boolean(string="BK", help="Tiêu chí áp dụng trên Booking")
    is_pk = fields.Boolean(string="PK", help="Tiêu chí áp dụng trên phiếu khám")
    is_tk = fields.Boolean(string="TK", help="Tiêu chí áp dụng trên tái khám")
    is_pc = fields.Boolean(string="PC", help="Tiêu chí áp dụng trên phone_call")
