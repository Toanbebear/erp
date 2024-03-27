# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import json
import requests
from urllib.parse import urlparse, parse_qs


class SciSmartButtonController(http.Controller):

    @http.route('/sci-smart-button/feedback/create', type='json', auth='user')
    def create_feedback_survey(self, **payload):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', int(payload.get('user_id')))], limit=1)
        survey_param = request.env['ir.config_parameter'].sudo().get_param('sci_smart_button.survey_dict')
        survey_dict = json.loads(survey_param)
        # Parse URL
        parsed_url = urlparse(payload.get('link'))

        # Lấy tham số từ query string
        query_params = parse_qs(parsed_url.fragment)

        view_id = request.env['ir.actions.act_window.view'].sudo().search(
            [('act_window_id', '=', int(query_params.get('action')[0])), ('view_mode', '=', payload.get('viewType'))],
            limit=1)
        data = {
            "survey_id": int(survey_dict['survey_id']),
            "lines": [
                {
                    "question_id": int(survey_dict['name']),
                    "value_text_box": employee.name if employee.name else ' '
                },
                {
                    "question_id": int(survey_dict['view_id']),
                    "value_text_box": str(view_id.view_id.id) if view_id.view_id.id else ' '
                },
                {
                    "question_id": int(survey_dict['content']),
                    "value_text_box": payload.get('content') if payload.get('content') else ' '
                },
                {
                    "question_id": int(survey_dict['rating']),
                    "value_text_box": str(payload.get('rating')) if payload.get('rating') else ' '
                },
                {
                    "question_id": int(survey_dict['user_id']),
                    "value_text_box": str(payload.get('user_id')) if payload.get('user_id') else ' '
                },
                {
                    "question_id": int(survey_dict['department_name']),
                    "value_text_box": employee.department_id.name if employee.department_id.name else ' '
                },
                {
                    "question_id": int(survey_dict['email']),
                    "value_text_box": payload.get('email') if payload.get('email') else ' '
                },
                {
                    "question_id": int(survey_dict['link']),
                    "value_text_box": payload.get('link') if payload.get('link') else ' '
                }
            ]
        }
        header = {
            'Content-Type': 'application/json',
            'Authorization': '9a9af5b8174facde56cdb07e803c9f16'
        }

        url = "{}/api/v1/create-report-employee".format(survey_dict['survey_url'])
        r = requests.post(url, data=json.dumps(data), headers=header)

        return json.dumps({
            'status': 'ok'
        })
