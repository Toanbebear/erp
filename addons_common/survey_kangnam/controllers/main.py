# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

import werkzeug
from dateutil.relativedelta import relativedelta
from odoo.addons.survey.controllers.main import Survey

from odoo import fields
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SurveyInherits(Survey):
    @http.route('/survey/start/<string:survey_token>/walkin_id=<string:walkin>', type='http', auth='public',
                website=True)
    def survey_start_kangnam(self, survey_token, answer_token=None, walkin=None, email=False, **post):
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
                answer_sudo = survey_sudo._create_answer_kangnam(user=request.env.user, walkin=int(walkin), email=email)

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

            services = ""
            for service in answer_sudo.walkin_id.service:
                services += service.name + '.'
            data = {'survey': survey_sudo, 'answer': answer_sudo, 'page': 0, 'user_ids': survey_sudo.company_id.user_ids,
                    'date': answer_sudo.walkin_id.date,
                    'customer_name': answer_sudo.walkin_id.patient.name,
                    'customer_phone': answer_sudo.walkin_id.patient.phone,
                    'doctor': answer_sudo.walkin_id.doctor.name,
                    'room': answer_sudo.walkin_id.service_room.name,
                    'walkin': walkin}

            return request.render('survey_kangnam.survey_kangnam_init', data)
        else:
            return request.redirect('/survey/fill/%s/%s' % (survey_sudo.access_token, answer_sudo.token))

    @http.route(['/survey/submit-creator/<string:survey_token>/<string:answer_token>/<int:walkin>'], type='http',
                methods=['POST'], csrf=False, auth='public', website=True)
    def submit_create(self, survey_token, answer_token, walkin, **post):

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
        ret['redirect'] = '/survey/fill/%s/%s/%s' % (survey_sudo.access_token, answer_sudo.token, walkin)
        return json.dumps(ret)

    @http.route('/survey/get-name', type='json', auth='public', website=True)
    def get_name_partner(self, phone=None):
        partner = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
        return partner.name

    @http.route('/survey/fill/<string:survey_token>/<string:answer_token>/<int:walkin>', type='http', auth='public',
                website=True)
    def survey_display_page(self, survey_token, answer_token, walkin, prev=None, **post):

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        register_walkin_id = request.env['sh.medical.appointment.register.walkin'].sudo().search([('id', '=', walkin)])

        if survey_sudo.is_time_limited and not answer_sudo.start_datetime:
            # init start date when user starts filling in the survey
            answer_sudo.write({
                'start_datetime': fields.Datetime.now()
            })

        page_or_question_key = 'question' if survey_sudo.questions_layout == 'page_per_question' else 'page'
        # Select the right page
        if answer_sudo.state == 'new':  # First page

            page_or_question_id, last = survey_sudo.next_page_or_question_kangnam(register_walkin_id, answer_sudo, 0, go_back=False)

            data = {
                'survey': survey_sudo,
                page_or_question_key: page_or_question_id,
                'answer': answer_sudo,
                'service_room': register_walkin_id.service_room.name,
                'walkin': walkin,
                'last': last if last else False
            }

            return request.render('survey_kangnam.survey_kangnam', data)
        elif answer_sudo.state == 'done':  # Display success message

            return request.render('survey_kangnam.sfinished',
                                  self._prepare_survey_finished_values(survey_sudo, answer_sudo))
        elif answer_sudo.state == 'skip':


            flag = (True if prev and prev == 'prev' else False)
            page_or_question_id, last = survey_sudo.next_page_or_question_kangnam(register_walkin_id,
                                                                          answer_sudo,
                                                                          answer_sudo.last_displayed_page_id.id,
                                                                          go_back=flag)

            # special case if you click "previous" from the last page,
            # then leave the survey, then reopen it from the URL, avoid crash
            if not page_or_question_id:
                page_or_question_id, last = survey_sudo.next_page_or_question_kangnam(register_walkin_id,
                                                                              answer_sudo,
                                                                              answer_sudo.last_displayed_page_id.id,
                                                                              go_back=True)

            data = {
                'survey': survey_sudo,
                page_or_question_key: page_or_question_id,
                'answer': answer_sudo,
                'service_room': register_walkin_id.service_room.name,
                'walkin': walkin,
                'last': last if last else False
                # 'last': True
            }

            if last:
                data.update({'last': True})

            return request.render('survey_kangnam.survey_kangnam', data)
        else:

            return request.render("survey.403", {'survey': survey_sudo})

    @http.route('/survey/page/<string:survey_token>/<string:answer_token>/<int:page_id>/<int:walkin>',
                type='http', auth='public', website=True)
    def survey_change_page(self, survey_token, answer_token, page_id, walkin, **post):
        # Controls if the survey can be displayed

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']

        return request.render('survey_kangnam.survey_kangnam', {
            'survey': survey_sudo,
            'page': request.env['survey.question'].sudo().browse(page_id),
            'answer': answer_sudo,
            'walkin': walkin
        })

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>/<int:walkin>', type='http',
                methods=['POST'],
                auth='public', website=True)
    def survey_submit_kangnam(self, survey_token, answer_token, walkin, **post):

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return {}
        register_walkin_id = request.env['sh.medical.appointment.register.walkin'].sudo().search([('id', '=', walkin)])
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo.test_entry and not survey_sudo._has_attempts_left(answer_sudo.partner_id, answer_sudo.email,
                                                                             answer_sudo.invite_token):
            # prevent cheating with users creating multiple 'user_input' before their last attempt
            return {}

        if survey_sudo.questions_layout == 'page_per_section':
            page_id = int(post['page_id'])
            questions = request.env['survey.question'].sudo().search(
                [('survey_id', '=', survey_sudo.id), ('page_id', '=', page_id)])
            # we need the intersection of the questions of this page AND the questions prepared for that user_input
            # (because randomized surveys do not use all the questions of every page)
            questions = questions & answer_sudo.question_ids
            page_or_question_id = page_id
        elif survey_sudo.questions_layout == 'page_per_question':
            question_id = int(post['question_id'])
            questions = request.env['survey.question'].sudo().browse(question_id)
            page_or_question_id = question_id
        else:
            questions = survey_sudo.question_ids
            questions = questions & answer_sudo.question_ids

        errors = {}
        # Answer validation
        if not answer_sudo.is_time_limit_reached:
            for question in questions:
                answer_tag = "%s_%s" % (survey_sudo.id, question.id)
                errors.update(question.validate_question(post, answer_tag))

        ret = {}
        if len(errors):
            # Return errors messages to webpage
            ret['errors'] = errors
        else:
            if not answer_sudo.is_time_limit_reached:
                for question in questions:
                    answer_tag = "%s_%s" % (survey_sudo.id, question.id)
                    request.env['survey.user_input_line'].sudo().save_lines(answer_sudo.id, question, post, answer_tag)

            vals = {}
            if answer_sudo.is_time_limit_reached or survey_sudo.questions_layout == 'one_page':
                go_back = False
                answer_sudo._mark_done()
            elif 'button_submit' in post:
                go_back = post['button_submit'] == 'previous'
                if post['button_submit'] == 'finish':
                    next_page = None
                else:
                    next_page, last = request.env['survey.survey'].next_page_or_question_kangnam(register_walkin_id,
                                                                                         answer_sudo,
                                                                                         page_or_question_id,
                                                                                         go_back=go_back)
                vals = {'last_displayed_page_id': page_or_question_id}

                if next_page is None and not go_back:
                    answer_sudo._mark_done()

                else:

                    vals.update({'state': 'skip'})

            if 'breadcrumb_redirect' in post:
                ret['redirect'] = post['breadcrumb_redirect']
            else:
                if vals:
                    answer_sudo.write(vals)

                ret['redirect'] = '/survey/fill/%s/%s/%s' % (survey_sudo.access_token, answer_token, walkin)
                if go_back:
                    ret['redirect'] += '?prev=prev'

        return json.dumps(ret)

    def _redirect_with_error(self, access_data, error_key):
        survey_sudo = access_data['survey_sudo']
        answer_sudo = access_data['answer_sudo']

        if error_key == 'survey_void' and access_data['can_answer']:
            return request.render("survey.survey_void", {'survey': survey_sudo, 'answer': answer_sudo})
        elif error_key == 'survey_closed' and access_data['can_answer']:
            return request.render("survey.survey_expired", {'survey': survey_sudo})
        elif error_key == 'survey_auth' and answer_sudo.token:
            if answer_sudo.partner_id and (answer_sudo.partner_id.user_ids or survey_sudo.users_can_signup):
                if answer_sudo.partner_id.user_ids:
                    answer_sudo.partner_id.signup_cancel()
                else:
                    answer_sudo.partner_id.signup_prepare(expiration=fields.Datetime.now() + relativedelta(days=1))
                redirect_url = answer_sudo.partner_id._get_signup_url_for_action(
                    url='/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.token))[
                    answer_sudo.partner_id.id]
            else:
                redirect_url = '/web/login?redirect=%s' % (
                        '/survey/start/%s?answer_token=%s' % (survey_sudo.access_token, answer_sudo.token))
            return request.render("survey.auth_required", {'survey': survey_sudo, 'redirect_url': redirect_url})
        elif error_key == 'answer_deadline' and answer_sudo.token:
            return request.render("survey.survey_expired", {'survey': survey_sudo})
        elif error_key == 'answer_done' and answer_sudo.token:
            return request.render("survey_kangnam.sfinished",
                                  self._prepare_survey_finished_values(survey_sudo, answer_sudo,
                                                                       token=answer_sudo.token))

        return werkzeug.utils.redirect("/")
