import json
import logging
from datetime import datetime
from odoo.addons.queue_job.job import job

import requests
from odoo import fields, models, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class CRMCaseInherit(models.Model):
    _inherit = 'crm.case'

    @job
    def sync_record(self, id):
        config = request.env['ir.config_parameter'].sudo()
        title_question = config.get_param('title_question')
        title_question_2 = config.get_param('title_question_2')
        title_answer = config.get_param('title_answer')
        survey_time = config.get_param('survey_time')
        case = self.sudo().browse(int(id))
        complain = self.env['crm.content.complain'].sudo().search([('crm_case','=',case.id)], limit=1)
        value_free_text = complain.desc
        survey_time_id = self.env['survey.survey.type'].sudo().search([('name', 'ilike', survey_time)], limit=1)
        survey = self.env['survey.survey'].sudo().search(
            [('brand_id', '=', case.brand_id.id), ('state', '=', 'open')], limit=1)
        list_survey_time = []
        for time in survey.survey_time_ids:
            list_survey_time.append(time.id)
            if survey_time_id.id in list_survey_time:
                group_service = None
                if case.booking_id:
                    for line in case.booking_id.crm_line_ids:
                        if line.stage == 'done':
                            group_service = line.service_id.service_category
                            break
                        else:
                            group_service = None
                    if group_service is None:
                        for line in case.booking_id.crm_line_ids:
                            group_service = line.service_id.service_category
                            break
                value = {
                    'survey_id': survey.id,
                    'partner_id': case.partner_id.id,
                    'create_date': case.create_date,
                    'input_type': "auto",
                    'survey_type': "case",
                    'brand_id': case.brand_id.id,
                    'company_id': case.company_id.id,
                    'department_id': case.department_create_by.id,
                    'survey_time_id': survey_time_id.id,
                    'crm_id': case.booking_id.id if case.booking_id else None,
                    'group_service_id': group_service.id if group_service else None,
                    'state': "done",
                    'case_id': id
                }
                user_input = self.env['survey.user_input'].sudo().search([('case_id', '=', id)])
                if user_input:
                    user_input.sudo().write(value)
                else:
                    user_input_id = self.env['survey.user_input'].sudo().create(value)
                question = self.env['survey.question'].sudo().search(
                    [('survey_id', '=', survey.id), ('title', 'ilike', title_question)])
                question_2 = self.env['survey.question'].sudo().search(
                    [('survey_id', '=', survey.id), ('title', 'ilike', title_question_2)])
                answer = self.env['survey.label'].sudo().search(
                    [('question_id', '=', question.id), ('value', 'ilike', title_answer)])
                value_line = {
                    'question_id': question.id,
                    'answer_type': "suggestion",
                    'value_suggested': answer.id,
                    'user_input_id': user_input.id if user_input else user_input_id.id,
                    'case_id': id
                }
                value_line_2 = {
                    'question_id': question_2.id,
                    'answer_type': "free_text",
                    'value_free_text': value_free_text,
                    'user_input_id': user_input.id if user_input else user_input_id.id,
                    'content_complain_id': complain.id
                }
                user_input_line = self.env['survey.user_input_line'].sudo().search([('case_id','=',id)])
                if user_input_line:
                    user_input_line.sudo().write(value_line)
                else:
                    self.env['survey.user_input_line'].sudo().create(value_line)
                user_input_line_2 = self.env['survey.user_input_line'].sudo().search([('content_complain_id','=',complain.id)])
                if user_input_line_2:
                    user_input_line_2.sudo().write(value_line_2)
                else:
                    self.env['survey.user_input_line'].sudo().create(value_line_2)

    @api.model
    def create(self, vals):
        res = super(CRMCaseInherit, self).create(vals)
        if res and vals['type_case'] == 'complain':
            job = self.sudo().with_delay(priority=0, channel='sync_survey_crm_case').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(CRMCaseInherit, self).write(vals)
        if res and 'type_case' in vals and vals['type_case'] == 'complain':
            job = self.sudo().with_delay(priority=0, channel='sync_survey_crm_case').sync_record(id=self.id)
        if res and self.type_case == 'complain':
            job = self.sudo().with_delay(priority=0, channel='sync_survey_crm_case').sync_record(id=self.id)
        return res

    def create_survey_case(self):
        config = request.env['ir.config_parameter'].sudo()
        title_question = config.get_param('title_question')
        title_answer = config.get_param('title_answer')
        survey_time = config.get_param('survey_time')
        survey_time_id = self.env['survey.survey.type'].sudo().search([('name', 'ilike', survey_time)], limit=1)
        cases = self.env['crm.case'].sudo().search([('type_case','=','complain')])
        for case in cases:
            surveys = case.env['survey.survey'].sudo().search(
                [('brand_id', '=', case.brand_id.id), ('state', '=', 'open')])
            for survey in surveys:
                list_survey_time = []
                for time in survey.survey_time_ids:
                    list_survey_time.append(time.id)
                    if survey_time_id.id in list_survey_time:
                        group_service = None
                        if case.booking_id:
                            for line in case.booking_id.crm_line_ids:
                                if line.stage == 'done':
                                    group_service = line.service_id.service_category
                                    break
                                else:
                                    group_service = None
                            if group_service is None:
                                for line in case.booking_id.crm_line_ids:
                                    group_service = line.service_id.service_category
                                    break
                        value = {
                            'survey_id': survey.id,
                            'partner_id': case.partner_id.id,
                            'create_date': case.create_date,
                            'input_type': "auto",
                            'survey_type': "case",
                            'brand_id': case.brand_id.id,
                            'company_id': case.company_id.id,
                            'department_id': case.department_create_by.id,
                            'survey_time_id': survey_time_id.id,
                            'crm_id': case.booking_id.id if case.booking_id else None,
                            'group_service_id': group_service.id if group_service else None,
                            'state': "done",
                            'case_id': case.id
                        }
                        user_input = self.env['survey.user_input'].sudo().search([('case_id', '=', case.id)], limit=1)
                        if user_input:
                            user_input.sudo().write(value)
                            select = """update survey_user_input sui set create_date = '%s' where id = %s""" % (
                                case.create_date.strftime('%Y-%m-%d %H:%M:%S'), user_input.id)
                            self.env.cr.execute(select)
                        else:
                            user_input_id = self.env['survey.user_input'].sudo().create(value)
                            select = """update survey_user_input sui set create_date = '%s' where id = %s""" % (case.create_date.strftime('%Y-%m-%d %H:%M:%S'), user_input_id.id)
                            self.env.cr.execute(select)
                        question = self.env['survey.question'].sudo().search(
                            [('survey_id', '=', survey.id), ('title', 'ilike', title_question)])
                        answer = self.env['survey.label'].sudo().search(
                            [('question_id', '=', question.id), ('value', 'ilike', title_answer)])
                        value_line = {
                            'question_id': question.id,
                            'answer_type': "suggestion",
                            'value_suggested': answer.id,
                            'user_input_id': user_input.id if user_input else user_input_id.id,
                            'case_id': case.id
                        }
                        user_input_line = self.env['survey.user_input_line'].sudo().search([('case_id', '=', case.id)],
                                                                                           limit=1)
                        if user_input_line:
                            user_input_line.sudo().write(value_line)
                            select = """update survey_user_input_line suil set create_date = '%s' where id = %s""" % (
                                case.create_date.strftime('%Y-%m-%d %H:%M:%S'), user_input_line.id)
                            self.env.cr.execute(select)
                        else:
                            user_input_line_id = self.env['survey.user_input_line'].sudo().create(value_line)
                            select = """update survey_user_input_line suil set create_date = '%s' where id = %s""" % (
                                case.create_date.strftime('%Y-%m-%d %H:%M:%S'), user_input_line_id.id)
                            self.env.cr.execute(select)
                        break
