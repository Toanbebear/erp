# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

import requests

from odoo import fields, models, api
from datetime import datetime

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
    _order = "create_date desc"

    api_id = fields.Integer()
    check_syn = fields.Boolean('Khách hàng thực hiện', compute='set_check',
                               help='Khách hàng thực hiện theo link hoặc mã QR')
    survey_creator = fields.Many2one('res.users', 'Creator')
    crm_id = fields.Many2one('crm.lead', string='Booking')
    # booking_code = fields.Char(related='crm_id.name', store=True)

    # sh.medical.appointment.register.walkin
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')

    # sh.medical.evaluation
    evaluation_id = fields.Many2one('sh.medical.evaluation', string='Tái khám')

    phone_call_id = fields.Many2one('crm.phone.call', string='Phone call')
    phone_call_check = fields.Boolean(string='PHONE CALL', compute='_check_phone_call')
    company = fields.Many2one(related='survey_id.company_id')
    company_id = fields.Many2one('res.company', string='Chi nhánh', compute='set_company', store=True)
    brand_id = fields.Many2one(related='company_id.brand_id', store=True)
    department_id = fields.Many2one('hr.department',
                                    string='Business unit',
                                    compute='set_department',
                                    store=True)

    answer_id = fields.Many2one('survey.label', string='Trả lời', compute='set_answer', store=True)

    service_ids = fields.Many2many('sh.medical.health.center.service',
                                   'survey_user_input_service_rel',
                                   'input_id',
                                   'service_id',
                                   compute='_compute_service_ids',
                                   string='Dịch vụ',
                                   help="Dịch vụ khảo sát")

    # Nhóm dịch vụ được chọn mỗi lần thực hiện khảo sát
    # Mỗi lần khảo sát sẽ là 1 nhóm duy nhất
    # Nhóm được lấy từ các dịch vụ của các phiếu
    group_service_id = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ')

    group_service_ids = fields.Many2many('sh.medical.health.center.service.category',
                                         'survey_user_input_group_service_rel',
                                         'input_id',
                                         'group_id',
                                         compute='_compute_service_ids',
                                         store=False,
                                         string='Nhóm dịch vụ trong phiếu',
                                         help="Tất cả nhóm dịch vụ có trong phiếu")

    survey_type = fields.Selection([
        ('booking', 'Booking'),
        ('pk', 'Phiếu khám'),
        ('tk', 'Tái khám'),
        ('case', 'Khiếu nại'),
    ], string="Khảo sát từ", compute='_compute_service_ids')

    survey_time_id = fields.Many2one('survey.survey.type', string='Tiêu chí')

    input_type = fields.Selection([
        ('manually', 'Manual'), ('link', 'Invitation'), ('auto', 'Tự động')],
        string='Answer Type', default='manually', required=True, readonly=True)

    case_id = fields.Integer('ID của khiếu nại')
    service_type = fields.Char('Loại dịch vụ khách hàng thực hiện', compute='_compute_service_type', store=True)
    score_user_input = fields.Integer('Điểm quy đổi', compute = '_score_user_input', store=True)

    @api.depends('answer_id')
    def _score_user_input(self):
        for rec in self:
            if not rec.score_user_input and rec.answer_id:
                if '1' in rec.answer_id.value:
                    rec.score_user_input = 1
                elif '2' in rec.answer_id.value:
                    rec.score_user_input = 2
                elif '3' in rec.answer_id.value:
                    rec.score_user_input = 3
                elif '4' in rec.answer_id.value:
                    rec.score_user_input = 4
                elif '5' in rec.answer_id.value:
                    rec.score_user_input = 5
                elif '6' in rec.answer_id.value:
                    rec.score_user_input = 6

    def cron_job_score_user_input(self):
        suis = self.env['survey.user_input'].sudo().search([])
        for sui in suis:
            if not sui.score_user_input and sui.answer_id:
                if '1' in sui.answer_id.value:
                    sui.score_user_input = 1
                if '2' in sui.answer_id.value:
                    sui.score_user_input = 2
                if '3' in sui.answer_id.value:
                    sui.score_user_input = 3
                if '4' in sui.answer_id.value:
                    sui.score_user_input = 4
                if '5' in sui.answer_id.value:
                    sui.score_user_input = 5
                if '6' in sui.answer_id.value:
                    sui.score_user_input = 6

    @api.depends('phone_call_id')
    def _check_phone_call(self):
        for record in self:
            if record.phone_call_id:
                record.phone_call_check = True
            else:
                record.phone_call_check = False

    @api.depends('crm_id', 'walkin_id', 'evaluation_id', 'group_service_id')
    def _compute_service_type(self):
        for record in self:
            list_type = ''
            if record.evaluation_id:
                for service in record.evaluation_id.services:
                    if service.service_category == record.group_service_id:
                        if service.his_service_type and service.his_service_type not in list_type:
                            list_type += ',' + str(service.his_service_type)
            elif record.walkin_id:
                for service in self.walkin_id.service:
                    if service.service_category == record.group_service_id:
                        if service.his_service_type and service.his_service_type not in list_type:
                            list_type += ',' + str(service.his_service_type)
            elif record.crm_id and not record.walkin_id and not record.evaluation_id:
                for line in record.crm_id.crm_line_ids:
                    if line.service_id.service_category == record.group_service_id:
                        if line.service_id.his_service_type and line.service_id.his_service_type not in list_type:
                            list_type += ',' + str(line.service_id.his_service_type)
            service_type_1 = list_type[1:].lower().replace('spa', 'Spa')
            service_type_2 = service_type_1.replace('laser', 'Laser')
            service_type_3 = service_type_2.replace('odontology', 'Nha')
            service_type_4 = service_type_3.replace('surgery', 'Phẫu thuật')
            service_type_5 = service_type_4.replace('chiphi', 'Chi phí khác')
            record.service_type = service_type_5

    def cron_job_service_type(self):
        pass
        # FIX Remove me
        # suis = self.env['survey.user_input'].sudo().search([])
        # for sui in suis:
        #     list_type = ''
        #     if sui.evaluation_id:
        #         for service in sui.evaluation_id.services:
        #             if service.service_category == sui.group_service_id:
        #                 if service.his_service_type and service.his_service_type not in list_type:
        #                     list_type += ',' + str(service.his_service_type)
        #     elif sui.walkin_id:
        #         for service in sui.walkin_id.service:
        #             if service.service_category == sui.group_service_id:
        #                 if service.his_service_type and service.his_service_type not in list_type:
        #                     list_type += ',' + str(service.his_service_type)
        #     elif sui.crm_id and not sui.walkin_id and not sui.evaluation_id:
        #         for line in sui.crm_id.crm_line_ids:
        #             if line.service_id.service_category == sui.group_service_id:
        #                 if line.service_id.his_service_type and line.service_id.his_service_type not in list_type:
        #                     list_type += ',' + str(line.service_id.his_service_type)
        #     service_type_1 = list_type[1:].lower().replace('spa', 'Spa')
        #     service_type_2 = service_type_1.replace('laser', 'Laser')
        #     service_type_3 = service_type_2.replace('odontology', 'Nha')
        #     service_type_4 = service_type_3.replace('surgery', 'Phẫu thuật')
        #     service_type_5 = service_type_4.replace('chiphi', 'Chi phí khác')
        #     sui.sudo().write({'service_type': service_type_5})

    @api.depends('crm_id', 'walkin_id', 'evaluation_id','input_type')
    def _compute_service_ids(self):
        """ As config_parameters does not accept m2m field,
            we get the fields back from the Char config field, to ease the configuration in config panel """
        for record in self:
            if record.evaluation_id:
                record.service_ids = record.evaluation_id.services
                record.survey_type = 'tk'
            elif record.walkin_id:
                record.service_ids = record.walkin_id.service
                record.survey_type = 'pk'
            elif record.crm_id:
                if record.input_type == 'auto':
                    record.survey_type = 'case'
                    if record.crm_id.crm_line_ids:
                        record.service_ids = record.crm_id.crm_line_ids.mapped('service_id').ids
                    else:
                        record.service_ids = None
                else:
                    record.survey_type = 'booking'
                    if record.crm_id.crm_line_ids:
                        record.service_ids = record.crm_id.crm_line_ids.mapped('service_id').ids
                    else:
                        record.service_ids = None
            else:
                record.survey_type = 'case'

            if record.service_ids:
                record.group_service_ids = record.service_ids.mapped('service_category').ids
            else:
                record.group_service_ids = None

    @api.depends('create_uid')
    def set_department(self):
        for rec in self:
            if rec.create_uid:
                employee_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', rec.create_uid.id)])
                rec.department_id = employee_id.department_id.id

    @api.depends('crm_id', 'walkin_id', 'create_uid','input_type')
    def set_company(self):
        for record in self:
            if record.crm_id:
                if record.input_type == 'auto':
                    pass
                    # record.company_id = self.company_id.id
                else:
                    record.company_id = record.crm_id.company_id.id
            elif record.walkin_id:
                record.company_id = record.walkin_id.company_id.id
            # else:
            #     record.company_id = record.create_uid.company_id.id

    @api.depends('user_input_line_ids')
    def set_answer(self):
        for record in self:
            if record.user_input_line_ids:
                for line in record.user_input_line_ids:
                    if line.question_id.constr_mandatory and line.value_suggested and line.question_id.question_type != 'matrix':
                        record.answer_id = line.value_suggested.id
                        break

    @api.depends('api_id')
    def set_check(self):
        for record in self:
            record.check_syn = True if record.api_id else False

    def _get_conditional_values(self):
        """ For survey containing conditional questions, we need a triggered_questions_by_answer map that contains
                {key: answer, value: the question that the answer triggers, if selected},
         The idea is to be able to verify, on every answer check, if this answer is triggering the display
         of another question.
         If answer is not in the conditional map:
            - nothing happens.
         If the answer is in the conditional map:
            - If we are in ONE PAGE survey : (handled at CLIENT side)
                -> display immediately the depending question
            - If we are in PAGE PER SECTION : (handled at CLIENT side)
                - If related question is on the same page :
                    -> display immediately the depending question
                - If the related question is not on the same page :
                    -> keep the answers in memory and check at next page load if the depending question is in there and
                       display it, if so.
            - If we are in PAGE PER QUESTION : (handled at SERVER side)
                -> During submit, determine which is the next question to display getting the next question
                   that is the next in sequence and that is either not triggered by another question's answer, or that
                   is triggered by an already selected answer.
         To do all this, we need to return:
            - list of all selected answers: [answer_id1, answer_id2, ...] (for survey reloading, otherwise, this list is
              updated at client side)
            - triggered_questions_by_answer: dict -> for a given answer, list of questions triggered by this answer;
                Used mainly for dynamic show/hide behaviour at client side
            - triggering_answer_by_question: dict -> for a given question, the answer that triggers it
                Used mainly to ease template rendering
        """
        triggering_answer_by_question, triggered_questions_by_answer = {}, {}
        # Ignore conditional configuration if randomised questions selection
        if self.survey_id.questions_selection != 'random':
            triggering_answer_by_question, triggered_questions_by_answer, triggering_question = self.survey_id._get_conditional_maps()

        return triggering_answer_by_question, triggered_questions_by_answer, triggering_question

    def _get_selected_suggested_answers(self):
        """
        For now, only simple and multiple choices question type are handled by the conditional questions feature.
        Mapping all the suggested answers selected by the user will also include answers from matrix question type,
        Those ones won't be used.
        Maybe someday, conditional questions feature will be extended to work with matrix question.
        :return: all the suggested answer selected by the user.
        """
        return self.mapped('user_input_line_ids.suggested_answer_id')

    def cron_job_user_input(self):
        brands = self.env['survey.brand.config'].search([])
        for brand in brands:
            url_base = brand.survey_brand_url
            token = brand.survey_brand_token
            url = url_base + "api/v1/get-total-survey"
            if url:
                headers = {
                    'Authorization': token
                }
                response = requests.get(url, headers=headers)
                response = response.json()
                if response['status'] == 0:
                    datas = response['data']
                    for data in datas:
                        if data['state'] == 'in_progress':
                            state = 'skip'
                        else:
                            state = data['state']
                        survey = self.env['survey.survey'].browse(data['survey_id'])
                        partner = self.env['res.partner'].search([('phone', '=', data['partner_phone'])], limit=1)
                        group_service = self.env['sh.medical.health.center.service.category'].sudo().browse(int(data['group_service_id'])) if data['group_service_id'] else None
                        time = self.env['survey.survey.type'].sudo().browse(int(data['time'])) if data['time'] else None
                        booking = self.env['crm.lead'].sudo().browse(int(data['booking_id'])) if data['booking_id'] else None
                        walkin = self.env['sh.medical.appointment.register.walkin'].sudo().browse(int(data['walkin_id'])) if data['walkin_id'] else None
                        evaluation = self.env['sh.medical.evaluation'].sudo().browse(int(data['evaluation_id'])) if data['evaluation_id'] else None
                        if partner:
                            partner_id = partner.id
                        else:
                            value = self.env['res.partner'].sudo().create({
                                "name": data['partner_name'],
                                "phone": data['partner_phone']
                            })
                            partner_id = value.id
                        value_user_input = {
                            'api_id': data['id'],
                            'survey_id': survey.id,
                            'partner_id': partner_id,
                            'state': state,
                            'group_service_id': group_service.id if group_service else None,
                            'survey_time_id': time.id if time else None,
                            'crm_id': booking.id if booking else None,
                            'walkin_id': walkin.id if walkin else None,
                            'evaluation_id': evaluation.id if evaluation else None
                        }
                        user_input = self.env['survey.user_input'].search([('api_id', '=', data['id']), ('survey_id', '=', survey.id)])
                        if user_input.api_id:
                            user_input.sudo().write(value_user_input)
                        else:
                            self.env['survey.user_input'].sudo().create(value_user_input)

                        for line in data['line_ids']:
                            user_input = self.env['survey.user_input'].search([('api_id', '=', line['user_input_id'])])
                            question = self.env['survey.question'].browse(line['question_id'])
                            answer = self.env['survey.label'].browse(line['suggested_answer_id'])
                            matrix = self.env['survey.label'].browse(line['matrix_row_id'])
                            if line['answer_type'] == 'text_box':
                                type = 'free_text'
                            elif line['answer_type'] == 'numerical_box':
                                type = 'number'
                            elif line['answer_type'] == 'char_box':
                                type = 'text'
                            else:
                                type = line['answer_type']
                            if line['value_datetime']:
                                date_time = datetime.strptime(line['value_datetime'], "%Y-%m-%d %H:%M:%S")
                            else:
                                date_time = False
                            value_line = {
                                'api_id': line['id'],
                                'question_id': question.id,
                                'answer_type': type,
                                'value_suggested': answer.id,
                                'user_input_id': user_input.id,
                                'value_date': line['value_date'],
                                'value_datetime': date_time,
                                'value_free_text': line['value_text_box'],
                                'value_number': line['value_numerical_box'],
                                'value_suggested_row': matrix.id,
                                'value_text': line['value_char_box'],
                                'skipped': line['skipped']
                            }
                            user_input_line = self.env['survey.user_input_line'].search(
                                [('api_id', '=', line['id']), ('survey_id', '=', survey.id)])
                            if user_input_line.api_id:
                                user_input_line.sudo().write(value_line)
                            else:
                                self.env['survey.user_input_line'].sudo().create(value_line)

    @api.model
    def create(self, vals):
        res = super(SurveyUserInput, self).create(vals)
        if res and res.input_type == 'auto':
            res.survey_type == 'case'
        return res


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    api_id = fields.Integer()
    suggested_answer_id = fields.Many2one('survey.label', string="Suggested answer")
    answer_value = fields.Char(string='Câu trả lời', compute='set_answer_value', store=True)
    value_comment = fields.Char(string='Giải thích lựa chọn')
    case_id = fields.Integer('ID của khiếu nại')
    content_complain_id = fields.Integer('ID nội dung khách hàng khiếu nại')

    @api.depends('value_suggested', 'value_free_text','value_suggested_row')
    def set_answer_value(self):
        for record in self:
            if record.value_suggested:
                if record.value_suggested_row:
                    record.answer_value = record.value_suggested_row.value
                else:
                    record.answer_value = record.value_suggested.value
            else:
                record.answer_value = record.value_free_text

    @api.model
    def save_line_simple_choice(self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'survey_id': question.survey_id.id,
            'skipped': False
        }
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('survey_id', '=', question.survey_id.id),
            ('question_id', '=', question.id)
        ])
        old_uil.sudo().unlink()

        if answer_tag in post and post[answer_tag].strip():
            comment = post.pop(("%s_%s" % (int(post[answer_tag]), 'comment')), '').strip()
            vals.update(
                {'answer_type': 'suggestion', 'value_suggested': int(post[answer_tag]), 'value_comment': comment})
        else:
            vals.update({'answer_type': None, 'skipped': True})

        # '-1' indicates 'comment count as an answer' so do not need to record it
        if post.get(answer_tag) and post.get(answer_tag) != '-1':
            self.create(vals)

        comment_answer = post.pop(("%s_%s" % (answer_tag, 'comment')), '').strip()

        if comment_answer:
            vals.update(
                {'answer_type': 'text', 'value_text': comment_answer, 'skipped': False, 'value_suggested': False})
            self.create(vals)

        return True

    @api.model
    def save_line_multiple_choice(self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'survey_id': question.survey_id.id,
            'skipped': False
        }
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('survey_id', '=', question.survey_id.id),
            ('question_id', '=', question.id)
        ])
        old_uil.sudo().unlink()

        ca_dict = dict_keys_startswith(post, answer_tag + '_')
        comment_answer = ca_dict.pop(("%s_%s" % (answer_tag, 'comment')), '').strip()
        if len(ca_dict) > 0:
            for key in ca_dict:
                # '-1' indicates 'comment count as an answer' so do not need to record it
                if key != ('%s_%s' % (answer_tag, '-1')):
                    val = ca_dict[key]
                    comment = post.pop(("%s_%s" % (int(val), 'comment')), '').strip()
                    vals.update({'answer_type': 'suggestion', 'value_suggested': bool(val) and int(val),
                                 'value_comment': comment})
                    self.create(vals)
        if comment_answer:
            vals.update({'answer_type': 'text', 'value_text': comment_answer, 'value_suggested': False})
            self.create(vals)
        if not ca_dict and not comment_answer:
            vals.update({'answer_type': None, 'skipped': True})
            self.create(vals)
        return True
