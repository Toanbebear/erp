import base64
import json
import logging
from io import BytesIO
import qrcode
import requests
import re
from odoo import http
from odoo.addons.restful.common import (
    valid_response,
    extract_arguments
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token,
)
from odoo.addons.survey_brand.controller.common import survey_validate_token
from odoo.http import request
from datetime import datetime

_logger = logging.getLogger(__name__)


def body_survey(user_name, survey_type, link):
    return """
        <style>
            .fcc-btn {
          background-color: #199319;
          color: white;
          padding: 10px 15px;
          text-decoration: none;
          border-radius: 10px;
        }
        .fcc-btn:hover {
          background-color: #223094;
        }
        </style>
        <p>Dear %s,</p>
        <p>Thương hiệu vừa nhận được phản ánh của Khách hàng thông qua %s</p>
        <p>Nội dung phản ánh <a style="background-color: #199319;color: white;padding: 10px 15px;text-decoration: none;border-radius: 10px;" class="fcc-btn" href=%s>Ấn vào đây</a></p>
        <p>Đề nghị quản lý thương hiệu/chi nhánh kiểm tra và giải quyết nhanh chóng, triệt để cho Khách hàng nhằm gia tăng trải nghiệm cho khách hàng tại thương hiệu</p>
        <p>----------------------------</p>
        <p>Thanks and Best Regards !</p>
    """ % (user_name, survey_type, link)


class SurveyController(http.Controller):
    @http.route('/survey_brand/survey/booking/<int:crm_lead>/create-survey-customer/<string:survey_token>', type='http',
                auth='public', website=True)
    def create_survey_customer(self, crm_lead, survey_token, **post):
        time_id = None
        group_service_id = None
        walkin_id = None
        evaluation_id = None
        phone_call_id = None
        if 'time_id' in post:
            time_id = int(post['time_id'])
        if 'group_service_id' in post:
            group_service_id = int(post['group_service_id'])
        if 'walkin_id' in post:
            walkin_id = int(post['walkin_id']) if post['walkin_id'] else None
        if 'evaluation_id' in post:
            evaluation_id = int(post['evaluation_id']) if post['evaluation_id'] else None
        if 'phone_call_id' in post:
            phone_call_id = int(post['phone_call_id']) if post['phone_call_id'] else None

        """ Tạo link khảo sát cho khách hàng
        """
        message = ''
        survey_sudo = request.env['survey.survey'].with_context(active_test=False).sudo().search(
            [('access_token', '=', survey_token)])
        # Tìm thông tin khách hàng
        booking = request.env['crm.lead'].sudo().browse(crm_lead)
        if booking:

            phone = booking.phone
            name = booking.partner_id.name
            company_id = booking.company_id.id
            user = request.env.user
            # Tạo link khảo sát bằng cách gọi qua API tới các API của thương hiệu
            brand = booking.brand_id
            # Cấu hình lấy theo thương hiệu
            survey_user_input = request.env['survey.user_input'].sudo().create({
                'survey_id': survey_sudo.id,
                'partner_id': booking.partner_id.id,
                'state': 'new',
                'crm_id': booking.id,
                'walkin_id': walkin_id if walkin_id else None,
                'evaluation_id': evaluation_id if evaluation_id else None,
                'phone_call_id': phone_call_id if phone_call_id else None,
                'group_service_id': group_service_id if group_service_id else None,
                'survey_time_id': time_id if time_id else None
            })
            config = request.env['survey.brand.config'].sudo().search([('brand_id', '=', booking.brand_id.id)], limit=1)
            if config:
                # link_survey = config.get_link_survey(survey_sudo.id,
                #                                      booking.partner_id.phone,
                #                                      booking.partner_id.name,
                #                                      booking.partner_id.id,
                #                                      group_service_id,
                #                                      time_id,
                #                                      crm_lead,
                #                                      walkin_id,
                #                                      evaluation_id,
                #                                      phone_call_id,
                #                                      request.env.user.id
                #                                      )
                link_survey = config.survey_brand_url + '%s' % survey_user_input.id
                if link_survey:
                    content_sms = config.survey_sms

                    if '[NAME]' in config.survey_sms:
                        # Loại bỏ dấu trong tên khách hàng
                        if config.is_remove_vietnamese:
                            name = self._convert(name)
                        content_sms = content_sms.replace('[NAME]', name)

                    if '[LINK]' in content_sms:
                        content_sms = content_sms.replace('[LINK]', link_survey)

                        data = {
                            'brand_id': survey_sudo.brand_id.id,
                            'company_id': company_id,
                            'customer_phone': phone,
                            'customer_phone_x': phone[0:3] + 'xxxx' + phone[7:],
                            'customer_name': name,
                            'content_sms': content_sms,
                            'link_survey': link_survey,
                            'qr_survey': 'data:image/jpeg;base64, %s' % self._generate_qr_code(link_survey)
                        }

                        if survey_sudo:
                            response = request.render('survey_brand.create_survey_customer', data)
                            response.headers['X-Frame-Options'] = 'DENY'
                            return response
                    else:
                        message = 'Cấu hình sai nội dung gửi SMS cho người dùng, thiếu [LINK] trong cấu hình nội dung'
                else:
                    message = 'Chưa đồng bộ khảo sát khách hàng cho thương hiệu. Vui lòng báo quản trị kiểm tra lại'
            else:
                message = 'Chưa cấu hình khảo sát khách hàng cho thương hiệu'

        return request.render("survey_brand.survey_error", {'title': "Thông báo", 'message': message})

    @http.route('/survey_brand/survey/send-sms-survey-customer', type='json', auth='user', website=True)
    def send_sms_survey_customer(self, **post):
        config = request.env['ir.config_parameter'].sudo()
        brand_id = None
        company_id = None
        phone = None
        content = None

        if 'brand' in post:
            brand_id = int(post['brand'])

        if 'company' in post:
            company_id = int(post['company'])

        if 'content' in post:
            content = post['content'].strip()

        if 'phone' in post:
            phone = post['phone'].strip()

        if 'production' == config.get_param('environment'):

            # Lấy account thương hiệu và token bên caresoft
            cs_account = {}

            brands = request.env['res.brand'].search([])
            for brand in brands:
                cs_account[brand.id] = {
                    'domain': config.get_param('domain_caresoft_%s' % (brand.code.lower())),
                    'token': config.get_param('domain_caresoft_token_%s' % (brand.code.lower())),
                    'service_id': config.get_param('domain_caresoft_service_id_%s' % (brand.code.lower()))
                }

            domain = cs_account[brand_id]['domain']
            service_id = cs_account[brand_id]['service_id']
            token = cs_account[brand_id]['token']
            if brand_id and phone and content:
                return self._sms_cs(domain, token, service_id, content, phone, company_id)

        return {'code': 'error', 'message': 'Chưa gửi được'}

    def _generate_qr_code(self, url):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_img = base64.b64encode(temp.getvalue()).decode()
        return qr_img

    def _convert(self, text):
        patterns = {
            '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
            '[đ]': 'd',
            '[èéẻẽẹêềếểễệ]': 'e',
            '[ìíỉĩị]': 'i',
            '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
            '[ùúủũụưừứửữự]': 'u',
            '[ỳýỷỹỵ]': 'y'
        }
        output = text
        for regex, replace in patterns.items():
            output = re.sub(regex, replace, output)

            # deal with upper case
            output = re.sub(regex.upper(), replace.upper(), output)
        return output

    def _sms_cs(self, domain, token, service_id, content, phone, company_id):
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        data = {
            "sms": {
                "service_id": service_id,
                "content": content,
                "phone": phone,
            }
        }

        url = "%s/api/v1/sms" % domain

        _logger.info("Survey....Send headers %s data %s", headers, data)
        res = requests.post(url, headers=headers, data=json.dumps(data))
        if res.status_code == 200:
            log = json.loads(res.content.decode())
            partner = request.env['res.partner'].search([('phone', '=', phone)])
            sms = request.env['crm.sms'].sudo().create({
                'name': 'Tin nhắn gửi link khảo sát cho khách hàng',
                'contact_name': partner.name,
                'partner_id': partner.id,
                'phone': phone,
                'company_id': company_id,
                'send_date': datetime.now(),
                'state': 'sent',
                'cs_response': log,
                'desc': content,
            })
            return {'code': 'OK', 'message': 'Đã gửi SMS cho khách hàng'}
        else:
            return {'code': 'error', 'message': 'Chưa gửi được'}

    @survey_validate_token
    @http.route("/api/v1/get-survey", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_get_survey(self, **payload):
        """ API get survey"""
        list_survey = request.env['survey.survey'].sudo().search([])
        ret_data = []
        for rec in list_survey:
            list_question_inactive = request.env['survey.question'].sudo().search(
                [('survey_id', '=', rec.id), ('active', '=', False)])
            list = []
            for question in list_question_inactive:
                if question.display_mode == 'icon':
                    is_display_icon = True
                else:
                    is_display_icon = False
                list_answer = request.env['survey.label'].sudo().search([('question_id', '=', question.id)])
                list_answer_2 = request.env['survey.label'].sudo().search([('question_id_2', '=', question.id)])
                triggering_question = request.env['survey.question'].sudo().browse(question.triggering_question_id)
                survey = request.env['survey.survey'].sudo().browse(question.survey_id)
                survey_id = survey.id
                triggering_question_1 = triggering_question.id
                list_value = []
                list_row = []
                list_id = []
                for answer in list_answer:
                    value_answer = {
                        "id": answer.id,
                        "value": answer.value,
                        "value_description": answer.value_description,
                        "question_id": question.id
                    }
                    list_value.append(value_answer)

                for row in list_answer_2:
                    value_row = {
                        "id": row.id,
                        "value": row.value,
                        "question_id_2": question.id
                    }
                    list_row.append(value_row)
                if question.is_conditional == True:
                    triggering_question_id = triggering_question_1.id
                    for answer in question.triggering_answer_ids:
                        value_trigger_answer = {
                            "id": answer.id
                        }
                        list_id.append(value_trigger_answer)
                else:
                    triggering_question_id = False
                value_question = {
                    "id": question.id,
                    'title': question.title,
                    'question_type': question.question_type,
                    'constr_mandatory': question.constr_mandatory,
                    'constr_error_msg': question.constr_error_msg,
                    'is_conditional': question.is_conditional,
                    'triggering_question_id': triggering_question_id,
                    'triggering_answer_ids': list_id,
                    'comments_allowed': question.comments_allowed,
                    'comments_message': question.comments_message,
                    'comment_count_as_answer': question.comment_count_as_answer,
                    'is_display_icon': is_display_icon,
                    'survey_id': survey_id.id,
                    'answer': list_value,
                    'row': list_row,
                    'has_description': question.has_description,
                    'column_nb': question.column_nb,
                    'has_note': question.has_note,
                    'active': question.active,
                    'sequence': question.sequence
                }
                list.append(value_question)
            list_question = request.env['survey.question'].sudo().search([('survey_id', '=', rec.id)])
            for question in list_question:
                if question.display_mode == 'icon':
                    is_display_icon = True
                else:
                    is_display_icon = False
                list_answer = request.env['survey.label'].sudo().search([('question_id', '=', question.id)])
                list_answer_2 = request.env['survey.label'].sudo().search([('question_id_2', '=', question.id)])
                triggering_question = request.env['survey.question'].sudo().browse(question.triggering_question_id)
                survey = request.env['survey.survey'].sudo().browse(question.survey_id)
                survey_id = survey.id
                triggering_question_1 = triggering_question.id
                list_value = []
                list_row = []
                list_id = []
                for answer in list_answer:
                    value_answer = {
                        "id": answer.id,
                        "value": answer.value,
                        "value_description": answer.value_description,
                        "question_id": question.id
                    }
                    list_value.append(value_answer)

                for row in list_answer_2:
                    value_row = {
                        "id": row.id,
                        "value": row.value,
                        "question_id_2": question.id
                    }
                    list_row.append(value_row)
                if question.is_conditional == True:
                    triggering_question_id = triggering_question_1.id
                    for answer in question.triggering_answer_ids:
                        value_trigger_answer = {
                            "id": answer.id
                        }
                        list_id.append(value_trigger_answer)
                else:
                    triggering_question_id = False
                value_question = {
                    "id": question.id,
                    'title': question.title,
                    'question_type': question.question_type,
                    'constr_mandatory': question.constr_mandatory,
                    'constr_error_msg': question.constr_error_msg,
                    'is_conditional': question.is_conditional,
                    'triggering_question_id': triggering_question_id,
                    'triggering_answer_ids': list_id,
                    'comments_allowed': question.comments_allowed,
                    'comments_message': question.comments_message,
                    'comment_count_as_answer': question.comment_count_as_answer,
                    'is_display_icon': is_display_icon,
                    'survey_id': survey_id.id,
                    'answer': list_value,
                    'row': list_row,
                    'has_description': question.has_description,
                    'column_nb': question.column_nb,
                    'has_note': question.has_note,
                    'active': question.active,
                    'sequence': question.sequence
                }
                list.append(value_question)
            value = {
                'id': rec.id,
                'title': rec.title,
                'questions_layout': rec.questions_layout,
                'questions_selection': rec.questions_selection,
                'description_done': rec.thank_you_message,
                'description': rec.description,
                'access_mode': rec.access_mode,
                'users_login_required': rec.users_login_required,
                'is_attempts_limited': rec.is_attempts_limited,
                'attempts_limit': rec.attempts_limit,
                'brand_id': rec.brand_id.code,
                'question_ids': list,
            }
            ret_data.append(value)
            _logger.info(value)
        return valid_response(ret_data)

    @survey_validate_token
    @http.route("/api/v1/create-survey-user-input", methods=["POST"], type="http", auth="none", csrf=False)
    def create_survey_user_input(self, **payload):
        """ API create user input"""
        partner = request.env['res.partner'].sudo().search([('phone', '=', payload.get('phone'))])
        survey = request.env['survey.survey'].sudo().browse(int(payload.get('survey_id')))
        list_line = []
        if payload.get('state') == 'in_progress':
            state = 'skip'
        else:
            state = payload.get('state')
        if payload.get('user_input_line_ids') != 'None':
            for value in eval(payload.get('user_input_line_ids')):
                question = request.env['survey.question'].sudo().browse(int(value['question_id']))
                answer = request.env['survey.label'].sudo().browse(int(value['suggested_answer_id'])) if value[
                    'suggested_answer_id'] else None
                matrix = request.env['survey.label'].sudo().browse(int(value['matrix_row_id'])) if value[
                    'matrix_row_id'] else None
                if value['answer_type'] == 'char_box':
                    type = 'text'
                elif value['answer_type'] == 'numerical_box':
                    type = 'number'
                elif value['answer_type'] == 'text_box':
                    type = 'free_text'
                else:
                    type = value['answer_type']
                if value['value_datetime']:
                    date_time = datetime.strptime(value['value_datetime'], "%Y-%m-%d %H:%M:%S")
                else:
                    date_time = None
                if value['value_date']:
                    date = datetime.strptime(value['value_date'], "%Y-%m-%d")
                else:
                    date = None
                val = {
                    'api_id': value['id'],
                    'question_id': question.id,
                    'answer_type': type,
                    'value_suggested': answer.id if answer else None,
                    'value_date': date,
                    'value_datetime': date_time,
                    'value_free_text': value['value_text_box'] if value['value_text_box'] else None,
                    'value_number': value['value_numerical_box'] if value['value_numerical_box'] else None,
                    'value_suggested_row': matrix.id if matrix else None,
                    'value_text': value['value_char_box'],
                    'value_comment': value['value_comment'],
                    'skipped': value['skipped']
                }
                line = request.env['survey.user_input_line'].sudo().search(
                    [('api_id', '=', value['id']), ('question_id', '=', question.id)])
                if line:
                    line.sudo().write(val)
                else:
                    list_line.append((0, 0, val))
        group_service = request.env['sh.medical.health.center.service.category'].sudo().browse(
            int(payload.get('group_service_id')))
        time = request.env['survey.survey.type'].sudo().browse(int(payload.get('time')))
        booking = request.env['crm.lead'].sudo().browse(int(payload.get('booking_id')))
        walkin = request.env['sh.medical.appointment.register.walkin'].sudo().browse(
            int(payload.get('walkin_id'))) if payload.get('walkin_id') else None
        evaluation = request.env['sh.medical.evaluation'].sudo().browse(
            int(payload.get('evaluation_id'))) if payload.get('evaluation_id') else None
        phone_call = request.env['crm.phone.call'].sudo().browse(int(payload.get('phone_call_id'))) if payload.get(
            'phone_call_id') else None
        res_user = request.env['res.users'].sudo().browse(int(payload.get('user_id')))
        value = {
            'survey_id': survey.id,
            'partner_id': partner.id,
            'state': state,
            'api_id': int(payload.get('id')),
            'crm_id': booking.id,
            'walkin_id': walkin.id if walkin else None,
            'evaluation_id': evaluation.id if evaluation else None,
            'phone_call_id': phone_call.id if phone_call else None,
            'group_service_id': group_service.id,
            'survey_time_id': time.id,
            'user_input_line_ids': list_line
        }

        survey_user_input = request.env['survey.user_input'].sudo().search(
            [('api_id', '=', int(payload.get('id'))), ('survey_id', '=', survey.id)])
        if survey_user_input:
            survey_user_input.sudo().write(value)
            select = """update survey_user_input sui set create_uid = %s where id = %s""" % (
                int(res_user.id), survey_user_input.id)
            request.env.cr.execute(select)
            return valid_response(survey_user_input)
        else:
            survey_user_input_id = request.env['survey.user_input'].sudo().create(value)
            select = """update survey_user_input sui set create_uid = %s where id = %s""" % (
                int(res_user.id), survey_user_input_id.id)
            request.env.cr.execute(select)
            return valid_response(survey_user_input_id)

    @http.route('/survey_brand/survey', type='json', auth='public', website=True)
    def survey_brand_get_survey(self, **post):

        """ Lấy survey phù hợp với tiêu chí của phiếu """
        group_service_ids = []
        survey_time_ids = []
        brand = None
        branch = None
        if post:
            if 'group_service' in post:
                group_service_ids.append(int(post['group_service']))
            if 'time' in post:
                survey_time_ids.append(int(post['time']))
            if 'brand' in post:
                brand = int(post['brand'])

            if 'branch' in post:
                branch = int(post['branch'])

        domain = [
            ('state', '=', 'open'),
            ('group_service_ids', 'in', group_service_ids),
            ('survey_time_ids', 'in', survey_time_ids),
        ]

        # if brand:
        #     domain.append(('brand_id', '=', brand))

        if branch:
            domain.append(('company_ids', 'in', [branch]))

        surveys = request.env['survey.survey'].sudo().search_read(domain, ['id', 'title', 'access_token'], limit=5)
        ret = {'surveys': surveys}
        return json.dumps(ret)

    @survey_validate_token
    @http.route("/api/v1/get-survey-web", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_get_survey_web(self, **payload):
        """ API get survey"""
        user_input = request.env['survey.user_input'].sudo().browse(int(payload.get('id')))
        if user_input:
            survey = request.env['survey.survey'].sudo().browse(int(user_input.survey_id.id))
            ret_data = []
            if survey:
                list_q = []
                list_question = request.env['survey.question'].sudo().search([('survey_id', '=', survey.id)])
                for question in list_question:
                    list_answer = request.env['survey.label'].sudo().search([('question_id', '=', question.id)])
                    list_answer_2 = request.env['survey.label'].sudo().search([('question_id_2', '=', question.id)])
                    triggering_question = request.env['survey.question'].sudo().browse(question.triggering_question_id)
                    triggering_question_1 = triggering_question.id
                    list_value = []
                    list_row = []
                    list_id = []
                    for answer in list_answer:
                        value_answer = {
                            "id": answer.id,
                            "value": answer.value,
                            "value_description": answer.value_description,
                            "question_id": question.id
                        }
                        list_value.append(value_answer)

                    for row in list_answer_2:
                        value_row = {
                            "id": row.id,
                            "value": row.value,
                            "question_id_2": question.id
                        }
                        list_row.append(value_row)
                    if question.is_conditional == True:
                        triggering_question_id = triggering_question_1.id
                        for answer in question.triggering_answer_ids:
                            value_trigger_answer = {
                                "id": answer.id
                            }
                            list_id.append(value_trigger_answer)
                    else:
                        triggering_question_id = False
                    value_question = {
                        "id": question.id,
                        'title': question.title,
                        'question_type': question.question_type,
                        'constr_mandatory': question.constr_mandatory,
                        'constr_error_msg': question.constr_error_msg,
                        'is_conditional': question.is_conditional,
                        'triggering_question_id': triggering_question_id,
                        'triggering_answer_ids': list_id,
                        'survey_id': survey.id,
                        'sequence': question.sequence,
                        'col_nb': question.column_nb,
                        'answer': list_value,
                        'row': list_row,
                        'icon': question.has_icon

                    }
                    list_q.append(value_question)
                value = {
                    'id': survey.id,
                    'brand_code': survey.brand_id.code,
                    'title': survey.title,
                    'question_ids': list_q
                }
                ret_data.append(value)
            return valid_response(ret_data)

    @survey_validate_token
    @http.route("/api/v1/create-survey-user-input-web", methods=["POST"], type="json", auth="none", csrf=False,
                cors='*')
    def create_survey_user_input_web(self, **payload):
        """ API create user input"""
        list_line = []
        body = json.loads(request.httprequest.data.decode('utf-8'))
        dict_type = {
            'free_text': 'free_text',
            'text_box': 'text',
            'numerical_box': 'number',
            'date': 'date',
            'datetime': 'datetime',
            'simple_choice': 'suggestion',
            'multiple_choice': 'suggestion',
            'matrix': 'suggestion'
        }
        _logger.info(body)
        if body['user_input_line_ids']:
            for value in body['user_input_line_ids']:
                question = request.env['survey.question'].sudo().browse(int(value['question_id']))
                answer = request.env['survey.label'].sudo().browse(int(value['suggested_answer_id'])) if value[
                    'suggested_answer_id'] else None
                matrix = request.env['survey.label'].sudo().browse(int(value['matrix_row_id'])) if value[
                    'matrix_row_id'] else None
                if value['value_datetime']:
                    date_time = datetime.strptime(value['value_datetime'], "%Y-%m-%d %H:%M:%S")
                else:
                    date_time = None
                if value['value_date']:
                    date = datetime.strptime(value['value_date'], "%Y-%m-%d")
                else:
                    date = None
                val = {
                    'question_id': question.id,
                    'answer_type': dict_type[value['answer_type']],
                    'value_suggested': answer.id if answer else None,
                    'value_date': date,
                    'value_datetime': date_time,
                    'value_free_text': value['value_text_box'] if value['value_text_box'] else None,
                    'value_number': value['value_numberical_box'] if value['value_numberical_box'] else None,
                    'value_suggested_row': matrix.id if matrix else None,
                    'value_text': value['value_char_box'],
                    'value_comment': value['value_comment'],
                    'skipped': value['skipped']
                }
                list_line.append((0, 0, val))
        _logger.info(list_line)
        survey_user_input = request.env['survey.user_input'].sudo().browse(int(body['id']))
        if survey_user_input:
            survey_user_input.sudo().write({'user_input_line_ids': list_line,
                                            'state': body['state']})

            return valid_response(survey_user_input)

    @survey_validate_token
    @http.route("/api/v1/create-crm-case-survey", methods=["POST"], type="json", auth="none", csrf=False, cors='*')
    def create_crm_case_survey(self, **payload):
        """ API tạo phản ánh/góp ý khảo sát"""
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('==================Khảo sát QR==================')
        _logger.info('body: %s' % body)
        partner_id = None
        company_id = None
        company = None
        if body['company_id']:
            company = request.env['res.company'].sudo().browse(int(body['company_id']))
            company_id = company.id if company else None
        login = 'admin_%s' % company.brand_id.code.lower()
        user = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        user_id = user.id if user else 2
        if body['phone']:
            partner = request.env['res.partner'].sudo().search(['|', ('phone', '=', body['phone']),
                                                                ('mobile', '=', body['phone'])], limit=1)
            if partner:
                partner_id = partner.id
            else:
                if body['name']:
                    partner = request.env['res.partner'].sudo().with_user(user_id).create({
                        'name': body['name'],
                        'phone': body['phone']
                    })
                    partner_id = partner.id
                else:
                    partner = request.env['res.partner'].sudo().with_user(user_id).create({
                        'name': '',
                        'phone': body['phone']
                    })
                    partner_id = partner.id

        case = request.env['crm.case'].sudo().with_user(user_id).create({
            'name': 'Khách hàng phản ánh qua QR code/WEB',
            'partner_id': partner_id,
            'phone': body['phone'],
            'brand_id': company.brand_id.id,
            'start_date': datetime.now(),
            'type_case': 'complain',
            'company_id': company_id
        })
        content = request.env['crm.content.complain'].sudo().with_user(user_id).create({
            'stage': 'new',
            'desc': body['content'] if body['content'] else None,
            'crm_case': case.id
        })
        if 'type' in body:
            case_action_id = request.env.ref('crm_base.action_complain_case_view').id
            case_menu_id = request.env.ref('crm_base.crm_menu_case_complain').id
            url_long = get_url_base() + "/web#id=%d&model=crm.case&view_type=form&action=%d&menu_id=%d" % (
            case.id, case_action_id, case_menu_id)
            val_link = {
                'url': url_long
            }
            url_short = request.env['link.tracker'].sudo().create(val_link)
            desc = '[%s/%s]Thuong hieu vua nhan duoc phan anh cua Khach hang thong qua quet ma QR code. Noi dung phan anh: %s' % (
            case.company_id.brand_id.name, case.company_id.name, url_short.short_url)
            phone_x = body['phone'][:2] + 'xxxx' + body['phone'][6:],
            users = request.env['survey.send.mail.sms'].sudo().search([])
            for user in users:
                if company in user.company_ids:
                    sms = request.env['crm.sms'].with_user(1).sudo().create({
                        'name': 'Phản ánh/Góp ý của khách hàng: %s' % phone_x,
                        'partner_id': user.employee_id.user_id.partner_id.id,
                        'phone': user.phone,
                        'send_date': datetime.now(),
                        'company_id': company_id,
                        'active': True,
                        'state': 'draft',
                        'desc': desc
                    })
                    email_from = request.env['ir.mail_server'].sudo().search([], limit=1, order='id asc')
                    if body['type'] == 'qr':
                        temp_email = body_survey(user.employee_id.name, 'quét mã QRCode',url_short.short_url)
                        main_survey = {
                            'subject': '[%s/%s - QRCODE]' % (case.company_id.brand_id.name, case.company_id.name),
                            'body_html': temp_email,
                            'email_from': email_from.smtp_user if email_from else '',
                            'email_to': user.employee_id.work_email,
                        }
                        request.env['mail.mail'].sudo().create(main_survey).send()
                    else:
                        temp_email = body_survey(user.employee_id.name, 'Website', url_short.short_url)
                        main_survey = {
                            'subject': '[%s/%s - WEBSITE]' % (case.company_id.brand_id.name, case.company_id.name),
                            'body_html': temp_email,
                            'email_from': email_from.smtp_user if email_from else '',
                            'email_to': user.employee_id.work_email,
                        }
                        request.env['mail.mail'].sudo().create(main_survey).send()
        else:
            pass
        return 'Done'
