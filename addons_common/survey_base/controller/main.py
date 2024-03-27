# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging

import werkzeug
from odoo.addons.survey.controllers.main import Survey
from odoo import fields

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SurveyInherit(Survey):

    @http.route('/surveys', type="http", auth="public", website=True)
    def get_surveys(self, **post):
        surveys = request.env['survey.survey'].sudo().search([('state', '=', 'open')])

        data = {'surveys': surveys}
        return http.request.render('survey_base.online_survey_page', data)

    @http.route(['/survey/submit-creator/<string:survey_token>/<string:answer_token>'], type='http',
                methods=['POST'], csrf=False, auth='public', website=True)
    def submit_create_base(self, survey_token, answer_token, **post):

        ret = {}
        user_input = request.env['survey.user_input'].sudo().search([('token', '=', answer_token)], limit=1)

        if post['user']:
            user_id = request.env['res.users'].sudo().search([('id', '=', int(post['user']))], limit=1)
            user_input['survey_creator'] = user_id
        if 'customer_phone' in post:
            customer_name = post['customer_name'].upper()
            exit_partner = request.env['res.partner'].sudo().search([('phone', '=', post['customer_phone'])], limit=1)
            if exit_partner:
                exit_partner.name = post['customer_name']
                user_input.write({
                    'partner_id': exit_partner.id
                })
            else:
                partner = request.env['res.partner'].sudo().create({
                    'name': customer_name,
                    'phone': post['customer_phone']
                })
                user_input['partner_id'] = partner.id
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        ret['redirect'] = '/survey/fill/%s/%s' % (survey_sudo.access_token, answer_sudo.token)
        return json.dumps(ret)

    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """ Start a survey by providing
         * a token linked to a survey;
         * a token linked to an answer or generate a new token if access is allowed;
        """

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo:
            try:
                answer_sudo = survey_sudo._create_answer(user=request.env.user, email=email)
            except UserError:
                answer_sudo = False

        if not answer_sudo:
            try:
                survey_sudo.with_user(request.env.user).check_access_rights('read')
                survey_sudo.with_user(request.env.user).check_access_rule('read')
            except:
                return werkzeug.utils.redirect("/")
            else:
                return request.render("survey.403", {'survey': survey_sudo})

        # Select the right page
        if answer_sudo.state == 'new':  # Intro page
            data = {'survey': survey_sudo, 'answer': answer_sudo, 'page': 0, 'user_ids': survey_sudo.company_id.user_ids}
            return request.render('survey_base.survey_init', data)
        else:
            return request.redirect('/survey/fill/%s/%s' % (survey_sudo.access_token, answer_sudo.token))

    @http.route('/survey/get-name', type='json', auth='public', website=True)
    def get_name_partner(self, phone=None):
        partner = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
        return partner.name

    @http.route('/survey/fill/<string:survey_token>/<string:answer_token>', type='http', auth='public', website=True)
    def survey_display_page_base(self, survey_token, answer_token, prev=None, **post):

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']

        if survey_sudo.is_time_limited and not answer_sudo.start_datetime:
            # init start date when user starts filling in the survey
            answer_sudo.write({
                'start_datetime': fields.Datetime.now()
            })

        page_or_question_key = 'question' if survey_sudo.questions_layout == 'page_per_question' else 'page'
        # Select the right page
        if answer_sudo.state == 'new':  # First page
            page_or_question_id, last = survey_sudo.next_page_or_question(answer_sudo, 0, go_back=False)
            data = {
                'survey': survey_sudo,
                page_or_question_key: page_or_question_id,
                'answer': answer_sudo
            }
            if last:
                data.update({'last': True})
            return request.render('survey.survey', data)
        elif answer_sudo.state == 'done':  # Display success message
            return request.render('survey.sfinished', self._prepare_survey_finished_values(survey_sudo, answer_sudo))
        elif answer_sudo.state == 'skip':
            flag = (True if prev and prev == 'prev' else False)
            page_or_question_id, last = survey_sudo.next_page_or_question(answer_sudo,
                                                                          answer_sudo.last_displayed_page_id.id,
                                                                          go_back=flag)

            # special case if you click "previous" from the last page, then leave the survey, then reopen it from the URL, avoid crash
            if not page_or_question_id:
                page_or_question_id, last = survey_sudo.next_page_or_question(answer_sudo,
                                                                              answer_sudo.last_displayed_page_id.id,
                                                                              go_back=True)

            data = {
                'survey': survey_sudo,
                page_or_question_key: page_or_question_id,
                'answer': answer_sudo
            }
            if last:
                data.update({'last': True})

            return request.render('survey.survey', data)
        else:
            return request.render("survey.403", {'survey': survey_sudo})
