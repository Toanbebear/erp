# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging

import werkzeug
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo import http
from odoo.addons.survey.controllers.main import Survey
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SurveyBrandBooking(Survey):
    @http.route('/survey_brand/booking/<int:crm_lead>', type='http', auth='public', website=True)
    def survey_brand_init(self, crm_lead, **post):
        """ Khởi tạo khảo sát, dựa vào tiêu chí của phiếu và chọn lựa của người dùng
            Tìm ra phiếu khảo sát tương ứng
            Nếu không tìm thấy thì thông báo
            Nếu có hơn 1 phiếu thì cho người dùng chọn phiếu sẽ khảo sát
        """
        crm = request.env['crm.lead'].sudo().browse(crm_lead)
        customer_phone = crm.phone if crm.phone else crm.mobile
        timing = request.env['survey.survey.type'].sudo().search([('is_bk', '=', True)])

        data = {
            'user_id': request.env.user.id,  # Người làm khảo sát
            'customer_name': crm.contact_name,
            'customer_phone': customer_phone,
            'customer_phone_x': customer_phone[0:3] + 'xxxx' + customer_phone[7:],
            'branch': crm.company_id.name,
            'branch_id': crm.company_id.id,
            'brand': crm.brand_id.id,
            'group_services': crm.crm_line_ids.service_id.service_category,
            'booking': crm_lead,
            'timing': timing,
            'data_submit': '/survey_brand/booking/%s/survey' % (crm_lead),
        }

        if post:
            response = request.render('survey_brand.survey_brand_select_survey', data)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        else:
            return request.render('survey_brand.survey_brand_init_survey', data)

    @http.route('/survey_brand/booking/<string:crm_lead>/<string:survey_token>', type='http', auth='public',
                website=True)
    def survey_brand_start(self, crm_lead, survey_token, answer_token=None, email=False, **post):
        """ Start a survey by providing
         * a token linked to a survey;
         * a token linked to an answer or generate a new token if access is allowed;
        """
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error_survey_brand(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo:
            try:
                group_service = None
                survey_time_id = None
                if 'group_service' in post:
                    group_service = int(post['group_service'])
                if 'time' in post:
                    survey_time_id = int(post['time'])
                answer_sudo = survey_sudo._create_answer_booking(user=request.env.user, booking=crm_lead, email=email, group_service_id = group_service, survey_time_id = survey_time_id)
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
        return request.redirect(
            '/survey_brand/fill/booking/%s/%s/%s' % (crm_lead, survey_sudo.access_token, answer_sudo.token))
        # booking = request.env['crm.lead'].sudo().browse(int(crm_lead))
        # time_id = None
        # group_service_id = None
        # if 'time' in post:
        #     time_id = int(post['time'])
        # if 'group_service' in post:
        #     group_service_id = int(post['group_service'])
        # request.env['survey.user_input'].sudo().create({
        #     'survey_id': survey_sudo.id,
        #     'partner_id': booking.partner_id.id,
        #     'state': 'new',
        #     'crm_id': booking.id,
        #     'group_service_id': group_service_id if group_service_id else None,
        #     'survey_time_id': time_id if time_id else None
        # })
        # return request.redirect('https://www.google.com.vn/?hl=vi')

    @http.route('/survey_brand/evaluation/<string:evaluation_id>/<string:survey_token>', type='http', auth='public',
                website=True)
    def survey_brand_start_evaluation(self, evaluation_id, survey_token, answer_token=None, email=False, group_service=None,survey_time_id=None, **post):
        """ Start a survey by providing
         * a token linked to a survey;
         * a token linked to an answer or generate a new token if access is allowed;
        """
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error_survey_brand(access_data, access_data['validity_code'])
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo:
            try:
                answer_sudo = survey_sudo._create_answer_evaluation(
                    user=request.env.user,
                    evaluation_id=evaluation_id,
                    email=email,
                    group_service_id=group_service,
                    survey_time_id=survey_time_id
                )

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

        if answer_sudo.state == 'new':  # Intro page
            customer_phone = answer_sudo.crm_lead.phone if answer_sudo.crm_lead.phone else answer_sudo.crm_lead.mobile
            data = {
                'survey': survey_sudo,
                'answer': answer_sudo,
                'page': 0,
                'user_id': request.env.user.id,  # Người làm khảo sát
                'user_ids': survey_sudo.company_id.user_ids,
                'customer_name': answer_sudo.crm_lead.contact_name,
                'customer_phone': customer_phone,
                'customer_phone_x': customer_phone[0:3] + 'xxxx' + customer_phone[7:],
                'branch': answer_sudo.crm_lead.company_id.name,
                'group_services': answer_sudo.group_service_ids,
                'booking': answer_sudo.crm_lead.id,
            }
            return request.render('survey_brand.survey_brand_init', data)

        return request.redirect('/survey_brand/fill/%s/%s' % (survey_sudo.access_token, answer_sudo.token))

    @http.route(['/survey_brand/submit-creator/booking/<int:crm_lead>/<string:survey_token>/<string:answer_token>'],
                type='http',
                methods=['POST'], csrf=False, auth='public', website=True)
    def survey_brand_booking_creator(self, crm_lead, survey_token, answer_token, **post):
        ret = {}
        user_input = request.env['survey.user_input'].sudo().search([('token', '=', answer_token)], limit=1)

        if 'group_service' in post and post['group_service']:
            user_input['group_service_id'] = int(post['group_service'])

            # Nếu nhóm dịch vụ 1 thì chuyển về Survey 1
            # Nếu nhóm dịch vụ 2 thì chuyển về Survey 2
            if user_input['group_service_id'] in [10, 11]:
                print(user_input['group_service_id'])

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
            return self._redirect_with_error_survey_brand(access_data, access_data['validity_code'])
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        ret['redirect'] = '/survey_brand/fill/booking/%s/%s/%s' % (
            crm_lead, survey_sudo.access_token, answer_sudo.token)
        return json.dumps(ret)

    @http.route(['/survey_brand/submit-creator/<string:survey_token>/<string:answer_token>'], type='http',
                methods=['POST'], csrf=False, auth='public', website=True)
    def survey_brand_submit_creator(self, survey_token, answer_token, **post):
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
            return self._redirect_with_error_survey_brand(access_data, access_data['validity_code'])
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        ret['redirect'] = '/survey_brand/fill/%s/%s' % (survey_sudo.access_token, answer_sudo.token)
        return json.dumps(ret)

    # Hiển thị trang câu hỏi
    @http.route('/survey_brand/fill/<string:survey_token>/<string:answer_token>',
                type='http',
                auth='public',
                website=True)
    def survey_brand_page(self, survey_token, answer_token, prev=None, **post):
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error_survey_brand(access_data, access_data['validity_code'])

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
            return request.render('survey_brand.survey_brand', data)
        elif answer_sudo.state == 'done':  # Display success message
            return request.render('survey_brand.survey_finished',
                                  self._prepare_survey_finished_values(survey_sudo, answer_sudo))
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

            return request.render('survey_brand.survey_brand', data)
        else:
            return request.render("survey.403", {'survey': survey_sudo})

    @http.route('/survey_brand/fill/booking/<int:crm_lead>/<string:survey_token>/<string:answer_token>', type='http',
                auth='public', website=True)
    def survey_brand_booking_display_page_base(self, crm_lead, survey_token, answer_token, prev=None, **post):
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error_survey_brand(access_data, access_data['validity_code'])
        booking = request.env['crm.lead'].sudo().browse(int(crm_lead))
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        answer_sudo.partner_id = booking.partner_id.id if booking.partner_id.id else None
        if survey_sudo.is_time_limited and not answer_sudo.start_datetime:
            # init start date when user starts filling in the survey
            answer_sudo.write({
                'start_datetime': fields.Datetime.now()
            })

        page_or_question_key = 'question' if survey_sudo.questions_layout == 'page_per_question' else 'page'

        triggering_answer_by_question, triggered_questions_by_answer, triggering_question = answer_sudo._get_conditional_values()

        data_trigger = {
            'triggering_answer_by_question': {
                question.id: triggering_answer_by_question[question].id for question in
                triggering_answer_by_question.keys()
                if triggering_answer_by_question[question]
            },
            'triggered_questions_by_answer': {
                answer.id: triggered_questions_by_answer[answer].ids
                for answer in triggered_questions_by_answer.keys()
            },
            'triggering_question': triggering_question,
        }

        # Select the right page
        if answer_sudo.state == 'new':  # First page
            page_or_question_id, last = survey_sudo.next_question(answer_sudo, 0, data_trigger, go_back=False)
            data = {
                'survey': survey_sudo,
                page_or_question_key: page_or_question_id,
                'answer': answer_sudo,
                'booking': crm_lead
            }
            if last:
                data.update({'last': True})

            return request.render('survey_brand.survey_brand', data)
        elif answer_sudo.state == 'done':  # Display success message
            return request.render('survey_brand.survey_finished',
                                  self._prepare_survey_finished_values(survey_sudo, answer_sudo))
        elif answer_sudo.state == 'skip':
            flag = (True if prev and prev == 'prev' else False)
            page_or_question_id, last = survey_sudo.next_question(answer_sudo,
                                                                  answer_sudo.last_displayed_page_id.id,
                                                                  data_trigger,
                                                                  go_back=flag)

            # special case if you click "previous" from the last page, then leave the survey, then reopen it from the URL, avoid crash
            if not page_or_question_id:
                page_or_question_id, last = survey_sudo.next_question(answer_sudo,
                                                                      answer_sudo.last_displayed_page_id.id,
                                                                      data_trigger,
                                                                      go_back=True)

            data = {
                'survey': survey_sudo,
                page_or_question_key: page_or_question_id,
                'answer': answer_sudo,
                'booking': crm_lead
            }
            if last:
                data.update({'last': True})
            return request.render('survey_brand.survey_brand', data)
        else:
            return request.render("survey.403", {'survey': survey_sudo})


    @http.route('/survey_brand/survey/create-survey-customer', type='json', auth='public', website=True)
    def survey_brand_get_survey_customer(self, **post):

        """ Tạo link survey cho khách hàng """

        # group_service_ids = []
        # survey_time_ids = []
        # brand = None
        # branch = None
        # if post:
        #     if 'group_service' in post:
        #         group_service_ids.append(int(post['group_service']))
        #     if 'time' in post:
        #         survey_time_ids.append(int(post['time']))
        #     if 'brand' in post:
        #         brand = int(post['brand'])
        #
        #     if 'branch' in post:
        #         branch = int(post['branch'])
        #
        # domain = [
        #     ('state', '=', 'open'),
        #     ('group_service_ids', 'in', group_service_ids),
        #     ('survey_time_ids', 'in', survey_time_ids),
        # ]
        #
        # if brand:
        #     domain.append(('brand_id', '=', brand))
        #
        # if branch:
        #     domain.append(('company_ids', 'in', [branch]))
        # print(domain)
        # surveys = request.env['survey.survey'].sudo().search_read(domain, ['id', 'title', 'access_token'], limit=5)
        ret = {'surveys': ''}
        return json.dumps(ret)

    @http.route('/survey_brand/booking/<int:crm_lead>/survey', type='http', auth='public', website=True)
    def get_surveys(self, crm_lead, **post):
        crm = request.env['crm.lead'].sudo().browse(crm_lead)
        customer_phone = crm.phone if crm.phone else crm.mobile
        timing = request.env['survey.survey.type'].sudo().search([])

        data = {
            'user_id': request.env.user.id,  # Người làm khảo sát
            'customer_name': crm.contact_name,
            'customer_phone': customer_phone,
            'customer_phone_x': customer_phone[0:3] + 'xxxx' + customer_phone[7:],
            'branch': crm.company_id.name,
            'group_services': crm.crm_line_ids.service_id.service_category,
            'booking': crm_lead,
            'timing': timing,
        }

        if post and 'survey_survey' in post and 'group_service' in post and 'time' in post:
            ret = {'redirect': '/survey_brand/booking/%s/%s?group_service=%s&time=%s' % (crm_lead, post['survey_survey'], post['group_service'], post['time'])}
            return json.dumps(ret)
        else:
            return request.render('survey_brand.survey_brand_init_survey', data)

    @http.route('/survey_brand/submit/booking/<int:crm_lead>/<string:survey_token>/<string:answer_token>', type='http',
                methods=['POST'],
                auth='public', website=True)
    def survey_brand_submit_booking(self, crm_lead, survey_token, answer_token, **post):

        """ 
        Xử lý mỗi khi submit từng câu

        Submit a page from the survey.
        This will take into account the validation errors and store the answers to the questions.
        If the time limit is reached, errors will be skipped, answers wil be ignored and
        survey state will be forced to 'done'

        TDE NOTE: original comment: # AJAX submission of a page -> AJAX / http ?? 
        
        """
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return {}

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo.test_entry and not survey_sudo._has_attempts_left(answer_sudo.partner_id, answer_sudo.email,
                                                                             answer_sudo.invite_token):
            # prevent cheating with users creating multiple 'user_input' before their last attempt
            return {}

        triggering_answer_by_question, triggered_questions_by_answer, triggering_question = answer_sudo._get_conditional_values()

        data_trigger = {
            'triggering_answer_by_question': {
                question.id: triggering_answer_by_question[question].id for question in
                triggering_answer_by_question.keys()
                if triggering_answer_by_question[question]
            },
            'triggered_questions_by_answer': {
                answer.id: triggered_questions_by_answer[answer].ids
                for answer in triggered_questions_by_answer.keys()
            },
            'triggering_question': triggering_question,
        }

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
                next_page, last = request.env['survey.survey'].next_question(answer_sudo,
                                                                             page_or_question_id,
                                                                             data_trigger,
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

                ret['redirect'] = '/survey_brand/fill/booking/%s/%s/%s' % (
                    crm_lead, survey_sudo.access_token, answer_token)
                if go_back:
                    ret['redirect'] += '?prev=prev'

        return json.dumps(ret)

    def _redirect_with_error_survey_brand(self, access_data, error_key):
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
            return request.render("survey_brand.survey_finished",
                                  self._prepare_survey_finished_values(survey_sudo, answer_sudo,
                                                                       token=answer_sudo.token))

        return werkzeug.utils.redirect("/")
