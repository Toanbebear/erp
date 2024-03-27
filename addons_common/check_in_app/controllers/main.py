from datetime import datetime, timedelta
import json
import logging

from odoo.addons.restful.common import (
    valid_response,
    valid_response_once,
    invalid_response
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token,
)
from odoo import fields
import pyotp
from odoo import http
from odoo.http import request
import requests
from datetime import datetime, date, time, timedelta
from pytz import timezone, utc

_logger = logging.getLogger(__name__)
STAGE = {
    'cho_tu_van': 'Chờ tư vấn',
    'dang_tu_van': 'Đang tư vấn',
    'hoan_thanh': 'Hoàn thành',
    'huy': 'Hủy',
    '': ''
}

gender = {
    'male': 'Nam',
    'female': 'Nữ',
    'other': 'Khác'
}

gender_r = {
    'Nam': 'male',
    'Nữ': 'female',
    'Khác': 'other'
}
know = {'internet': 'Internet (fb/gg/tiktok...)',
        'friend': 'Bạn bè người thân giới thiệu',
        'voucher': 'Voucher/quà tặng...',
        'signs': 'Biển hiệu chi nhánh'}

target = {'tu_van': 'Tư vấn',
          'service': 'Thực hiện dịch vụ liệu trình',
          'eva': 'Tái khám'}


def get_gender(value):
    if value:
        return gender[value]
    else:
        return ''


class CrmCheckInController(http.Controller):

    @http.route("/api/v1/check-in/service-group", type="http", auth="none", methods=["GET"], csrf=False)
    def v1_check_in_get_service_group(self, **payload):
        """ API lấy danh sách nhóm dịch vụ """

        company_id = payload.get('company_id')
        brand_id = request.env['res.company'].sudo().browse(int(company_id)).brand_id.id
        record = request.env['crm.check.in.service.category'].sudo().search([('brand_id', '=',brand_id)])
        data = []
        if record:
            for rec in record:
                data.append({
                    'id': rec.id,
                    'name': rec.name,
                })
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/check-in/check-phone/<phone>/<company_id>", type="http", auth="none", methods=["GET"],
                csrf=False)
    def v1_check_in_check_phone(self, phone=None, company_id=None, **payload):
        """ API check số điện thoại """
        if phone:
            check_type = payload.get('type', None)
            checkin_type = payload.get('check_type')
            if not check_type:
                data = {
                    'status': 1,
                    'data': {
                        'partner_id': '',
                        'name': '',
                        'birth_date': '',
                        'gender': '',
                        'know': '',
                        'phone': '',
                        'booking_id': '',
                        'booking_url': '',
                        'check_in_id': '',
                        'check_in_url': ''
                    }
                }
                booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
                booking_menu_id = request.env.ref('crm.crm_menu_root').id
                check_in_action_id = request.env.ref('check_in_app.crm_check_in_list_act').id
                check_in_menu_id = request.env.ref('check_in_app.crm_check_in_list_sub_menu').id
                sd = datetime.now().date() - timedelta(days=1)
                ed = datetime.now().date() + timedelta(days=1)
                check_in_record = request.env['crm.check.in'].sudo().search(
                    [('phone', '=', phone), ('company_id', '=', int(company_id)), ('create_date', '>', sd),
                     ('create_date', '<', ed)], limit=1)
                if check_in_record:
                    data['status'] = 2
                    data['data'] = {
                        'partner_id': check_in_record.partner.id if check_in_record.partner else '',
                        'name': check_in_record.name,
                        'birth_date': check_in_record.date_of_birth.strftime(
                            "%Y-%d-%m") if check_in_record.date_of_birth else '',
                        'gender': get_gender(check_in_record.gender),
                        'know': know[check_in_record.know] if check_in_record.know else '',
                        'phone': phone,
                        'booking_id': check_in_record.booking.id if check_in_record.booking else '',
                        'booking_url': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                            check_in_record.booking.id,
                            booking_action_id, booking_menu_id) if check_in_record.booking else '',
                        'check_in_id': check_in_record.id,
                        'check_in_url': get_url_base() + "/web#id=%d&model=crm.check.in&view_type=form&action=%d&menu_id=%d" % (
                            check_in_record.id,
                            check_in_action_id, check_in_menu_id)

                    }
                    return valid_response_once(data)

                brand_id = int(request.brand_id)
                domain_book = [('type', '=', 'opportunity'), '|', '|', ('phone', '=', phone),
                               ('mobile', '=', phone), ('phone_no_3', '=', phone), ('brand_id', '=', brand_id)]
                booking = request.env['crm.lead'].sudo().search(domain_book, order='booking_date desc', limit=1)
                if booking:
                    if booking.effect == 'effect':
                        if booking.customer_come == 'no':
                            booking.set_stage_customer_come()
                            stage_not_confirm = request.env.ref('crm_base.crm_stage_not_confirm').id
                            stage_confirm = request.env.ref('crm_base.crm_stage_confirm').id
                            stage_no_come = request.env.ref('crm_base.crm_stage_no_come').id
                            query = """update crm_lead set customer_come = 'yes',arrival_date = '%s'""" % datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S')
                            if booking.stage_id.id == int(stage_not_confirm) or booking.stage_id.id == int(
                                    stage_no_come):
                                query += """, stage_id = %s where id = %s""" % (stage_confirm, booking.id)
                            else:
                                query += """where id = %s""" % booking.id
                            request._cr.execute(query)
                        data['status'] = 0
                        partner = booking.partner_id

                        bd = False
                        if booking.birth_date:
                            bd = booking.birth_date.strftime("%Y-%d-%m")
                        elif partner.birth_date:
                            bd = partner.birth_date.strftime("%Y-%d-%m")
                        else:
                            bd = ''

                        data['data'] = {
                            'partner_id': booking.partner_id.id,
                            'name': booking.contact_name,
                            'birth_date': bd,
                            'gender': gender[booking.gender],
                            'phone': phone,
                            'booking_id': booking.id,
                            'booking_url': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                                booking.id,
                                booking_action_id, booking_menu_id)
                        }
                        record = request.env['crm.check.in'].sudo().create({
                            'name': data['data']['name'],
                            'phone': data['data']['phone'],
                            'gender': gender[data['data']['gender']] if 'data' in data and 'gender' in
                                                                        data['data'] and data['data'][
                                                                            'gender'] in gender else False,
                            'check_type': checkin_type,
                            'company_id': int(company_id),
                            'desire': False,
                            'service_category_ids': False,
                            'booking': int(data['data']['booking_id']) if 'data' in data and 'booking_id' in
                                                                          data['data'] and data['data'][
                                                                              'booking_id'] else False,
                            'partner': int(data['data']['partner_id']) if 'data' in data and 'partner_id' in
                                                                          data['data'] and data['data'][
                                                                              'partner_id'] else False,
                        })

                    else:
                        if booking.customer_come == 'no':
                            booking.set_stage_customer_come()
                        data['status'] = 3
                        partner = booking.partner_id

                        bd = False
                        if booking.birth_date:
                            bd = booking.birth_date.strftime("%Y-%d-%m")
                        elif partner.birth_date:
                            bd = partner.birth_date.strftime("%Y-%d-%m")
                        else:
                            bd = ''

                        data['data'] = {
                            'partner_id': booking.partner_id.id,
                            'name': booking.contact_name,
                            'birth_date': bd,
                            'gender': gender[booking.gender],
                            'phone': phone,
                            'booking_id': booking.id,
                            'booking_url': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                                booking.id,
                                booking_action_id, booking_menu_id)
                        }
                else:
                    domain_partner = ['|', '|', ('phone', '=', phone), ('mobile', '=', phone),
                                      ('phone_no_3', '=', phone)]
                    partner = request.env['res.partner'].sudo().search(domain_partner, limit=1)
                    if partner:
                        data['status'] = 1
                        data['data'] = {
                            'partner_id': partner.id,
                            'name': partner.name,
                            'birth_date': partner.birth_date.strftime("%Y-%d-%m") if partner.birth_date else '',
                            'gender': gender[partner.gender] if partner.gender else False,
                            'phone': phone,
                            'booking_id': '',
                            'booking_url': ''
                        }
                    else:
                        domain_lead = [('type', '!=', 'opportunity'), '|', '|', ('phone', '=', phone),
                                       ('mobile', '=', phone), ('phone_no_3', '=', phone),
                                       ('brand_id', '=', brand_id)]
                        lead = request.env['crm.lead'].sudo().search(domain_lead, order='id desc', limit=1)
                        if lead:

                            bd = False
                            if lead.birth_date:
                                bd = lead.birth_date.strftime("%Y-%d-%m")
                            else:
                                bd = ''

                            data['status'] = 1
                            data['data'] = {
                                'partner_id': '',
                                'name': lead.contact_name,
                                'birth_date': bd,
                                'gender': gender[lead.gender],
                                'phone': phone,
                                'booking_id': '',
                                'booking_url': ''
                            }

                return valid_response_once(data)
            else:
                data_ctv = {
                    'status': 1,
                    'data': {
                        'partner_id': '',
                        'name': '',
                        'birth_date': '',
                        'gender': '',
                        'phone': '',
                        'booking_id': '',
                        'booking_url': '',
                        'check_in_id': '',
                        'check_in_url': '',
                        'pass': 0
                    }
                }
                booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
                booking_menu_id = request.env.ref('crm.crm_menu_root').id
                check_in_action_id = request.env.ref('check_in_app.crm_check_in_list_act').id
                check_in_menu_id = request.env.ref('check_in_app.crm_check_in_list_sub_menu').id
                sd = datetime.now().date() - timedelta(days=1)
                ed = datetime.now().date() + timedelta(days=1)
                check_in_record = request.env['crm.check.in'].sudo().search(
                    [('phone', '=', phone), ('company_id', '=', int(company_id)), ('create_date', '>', sd),
                     ('create_date', '<', ed)], limit=1)
                if check_in_record:
                    data_ctv['status'] = 2
                    data_ctv['data'] = {
                        'partner_id': check_in_record.partner.id if check_in_record.partner else '',
                        'name': check_in_record.name,
                        'birth_date': check_in_record.date_of_birth.strftime(
                            "%Y-%d-%m") if check_in_record.date_of_birth else '',
                        'gender': gender[check_in_record.gender],
                        'phone': phone,
                        'booking_id': check_in_record.booking.id if check_in_record.booking else '',
                        'booking_url': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                            check_in_record.booking.id,
                            booking_action_id, booking_menu_id) if check_in_record.booking else '',
                        'check_in_id': check_in_record.id,
                        'check_in_url': get_url_base() + "/web#id=%d&model=crm.check.in&view_type=form&action=%d&menu_id=%d" % (
                            check_in_record.id,
                            check_in_action_id, check_in_menu_id),
                        'pass': 0

                    }
                    return valid_response_once(data_ctv)

                brand_id = int(request.brand_id)
                domain_book = [('effect', '=', 'effect'), ('type', '=', 'opportunity'), '|', '|', ('phone', '=', phone),
                               ('mobile', '=', phone), ('phone_no_3', '=', phone), ('brand_id', '=', brand_id)]
                booking = request.env['crm.lead'].sudo().search(domain_book, order='booking_date desc', limit=1)
                if booking:
                    if booking.customer_come == 'no':
                        booking.set_stage_customer_come()
                    if booking.effect == 'effect':
                        if booking.stage_id in [request.env.ref('crm_base.crm_stage_not_confirm'),
                                                request.env.ref('crm_base.crm_stage_no_come')]:
                            booking.write({
                                'stage_id': request.env.ref('crm_base.crm_stage_confirm').id,
                                'customer_come': 'yes',
                                'arrival_date': datetime.now()
                            })

                    data_ctv['status'] = 0
                    partner = booking.partner_id

                    bd = False
                    if booking.birth_date:
                        bd = booking.birth_date.strftime("%Y-%d-%m")
                    elif partner.birth_date:
                        bd = partner.birth_date.strftime("%Y-%d-%m")
                    else:
                        bd = ''

                    data_ctv['data'] = {
                        'partner_id': booking.partner_id.id,
                        'name': booking.contact_name,
                        'birth_date': bd,
                        'gender': get_gender(booking.gender),
                        'phone': phone,
                        'check_in_id': '',
                        'check_in_url': '',
                        'booking_id': booking.id,
                        'booking_url': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                            booking.id,
                            booking_action_id, booking_menu_id),
                        'pass': 0
                    }

                else:
                    domain_partner = ['|', '|', ('phone', '=', phone), ('mobile', '=', phone),
                                      ('phone_no_3', '=', phone)]
                    partner = request.env['res.partner'].sudo().search(domain_partner, limit=1)
                    if partner:
                        data_ctv['status'] = 1
                        data_ctv['data'] = {
                            'partner_id': partner.id,
                            'name': partner.name,
                            'birth_date': partner.birth_date.strftime("%Y-%d-%m") if partner.birth_date else '',
                            'gender': get_gender(booking.gender),
                            'phone': phone,
                            'booking_id': '',
                            'booking_url': '',
                            'check_in_id': '',
                            'check_in_url': '',
                            'pass': 0
                        }
                    else:
                        domain_lead = [('type', '!=', 'opportunity'), '|', '|', ('phone', '=', phone),
                                       ('mobile', '=', phone), ('phone_no_3', '=', phone),
                                       ('brand_id', '=', brand_id)]
                        lead = request.env['crm.lead'].sudo().search(domain_lead, order='id desc', limit=1)
                        if lead:

                            bd = False
                            if lead.birth_date:
                                bd = lead.birth_date.strftime("%Y-%d-%m")
                            else:
                                bd = ''
                            data_ctv['status'] = 1
                            data_ctv['data'] = {
                                'partner_id': '',
                                'name': lead.contact_name,
                                'birth_date': bd,
                                'gender': gender[lead.gender],
                                'phone': phone,
                                'booking_id': '',
                                'booking_url': '',
                                'check_in_id': '',
                                'check_in_url': '',
                                'pass': 0
                            }
                # ctv: check thông tin để tạo check in
                if data_ctv['data']['name'] and data_ctv['data']['gender'] and data_ctv['data']['phone'] and \
                        data_ctv['data']['gender'] in ['Nam', 'Nữ', 'Khác']:
                    record = request.env['crm.check.in'].sudo().create({
                        'name': data_ctv['data']['name'],
                        'phone': data_ctv['data']['phone'],
                        'gender': gender_r[data_ctv['data']['gender']] if 'data' in data_ctv and 'gender' in data_ctv[
                            'data'] and data_ctv['data']['gender'] in gender_r else False,
                        'check_type': checkin_type,
                        'company_id': int(company_id),
                        'desire': False,
                        'service_category_ids': False,
                        'booking': int(data_ctv['data']['booking_id']) if 'data' in data_ctv and 'booking_id' in
                                                                          data_ctv['data'] and data_ctv['data'][
                                                                              'booking_id'] else False,
                        'partner': int(data_ctv['data']['partner_id']) if 'data' in data_ctv and 'partner_id' in
                                                                          data_ctv['data'] and data_ctv['data'][
                                                                              'partner_id'] else False,
                    })
                    if record:
                        data_ctv['data'] = {
                            'partner_id': '',
                            'name': data_ctv['data']['name'],
                            'gender': gender[record.gender] if record.gender else False,
                            'phone': phone,
                            'booking_id': int(data_ctv['data']['booking_id']) if 'data' in data_ctv and 'booking_id' in
                                                                                 data_ctv['data'] and data_ctv['data'][
                                                                                     'booking_id'] else '',
                            'booking_url': data_ctv['data']['booking_url'] if 'data' in data_ctv and 'booking_url' in
                                                                              data_ctv['data'] and data_ctv['data'][
                                                                                  'booking_id'] else '',
                            'check_in_id': record.id,
                            'check_in_url': get_url_base() + "/web#id=%d&model=crm.check.in&view_type=form&action=%d&menu_id=%d" % (
                                record.id,
                                check_in_action_id, check_in_menu_id),
                            'pass': 1
                        }
                    else:
                        invalid_response("ERROR", "Check in lỗi !!!")
                else:
                    data_ctv['data'] = {
                        'partner_id': '',
                        'name': data_ctv['data']['name'],
                        'gender': gender[data_ctv['data']['gender']] if 'data' in data_ctv and 'gender' in data_ctv[
                            'data'] and data_ctv['data']['gender'] in gender else False,
                        'phone': phone,
                        'booking_id': '',
                        'booking_url': '',
                        'check_in_id': '',
                        'check_in_url': '',
                        'pass': 0
                    }

                return valid_response_once(data_ctv)

        else:
            return invalid_response("ERROR", "Co loi xay ra !!!")

    @validate_token
    @http.route("/api/v1/check-in/register", type="json", auth="none", methods=["POST"], csrf=False)
    def v1_check_in_register(self, check_ctv=0, *payload):
        """ API check in """
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info(body)
        field_require = [
            'name',
            'phone',
            'company_id',
            'desire',
            'service_category_ids',
            'booking_id',
            'partner_id',
        ]
        checkin_type = body['check_type'] if 'check_type' in body else None
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thiếu tham số %s' % field,
                }
        check_in_action_id = request.env.ref('check_in_app.crm_check_in_list_act').id
        check_in_menu_id = request.env.ref('check_in_app.crm_check_in_list_sub_menu').id

        sd = datetime.now().date() - timedelta(days=1)
        ed = datetime.now().date() + timedelta(days=1)
        check_in_record = request.env['crm.check.in'].sudo().search(
            [('phone', '=', body['phone']), ('company_id', '=', int(body['company_id'])), ('create_date', '>', sd),
             ('create_date', '<', ed)], limit=1, order='id desc')
        if not check_in_record:
            # bd = False
            # if body['date_of_birth']:
            #     # năm - ngày - tháng => năm - tháng - ngày
            #     date = body['date_of_birth'].split('-')
            #     bd = date[0] + '-' + date[2] + '-' + date[1]

            if 'check_ctv' in body and int(body['check_ctv']) == 1:
                check_ctv = 1
            booking_id = None
            if body['booking_id']:
                booking = request.env['crm.lead'].sudo().browse(int(body['booking_id']))
                if booking:
                    if booking.effect == 'effect':
                        booking_id = booking.id
                    else:
                        booking_id = None
            record = request.env['crm.check.in'].sudo().create({
                'name': body['name'] if body['name'] else False,
                'phone': body['phone'] if body['name'] else False,
                'gender': body['gender'] if 'gender' in body and body['gender'] else False,
                'know': body['know'] if 'know' in body and body['know'] else False,
                'check_type': checkin_type if checkin_type else '',
                'company_id': int(body['company_id']) if body['company_id'] else False,
                'desire': body['desire'] if body['desire'] else False,
                'service_category_ids': [
                    (6, 0, request.env['crm.check.in.service.category'].browse(body['service_category_ids']).ids)] if
                body['service_category_ids'] else False,
                'booking': booking_id,
                'partner': int(body['partner_id']) if body['partner_id'] else False,
            })
            if record:
                return {
                    'stage': 0,
                    'message': 'Check in thanh cong',
                    'check_in_id': record.id,
                    'check_in_url': get_url_base() + "/web#id=%d&model=crm.check.in&view_type=form&action=%d&menu_id=%d" % (
                        record.id,
                        check_in_action_id, check_in_menu_id)
                }
            else:
                return {
                    'stage': 1,
                    'message': 'That bai',
                }
        else:
            return {
                'stage': 0,
                'message': 'Khach hang da check in',
                'check_in_id': check_in_record.id,
                'check_in_url': get_url_base() + "/web#id=%d&model=crm.check.in&view_type=form&action=%d&menu_id=%d" % (
                    check_in_record.id,
                    check_in_action_id, check_in_menu_id)
            }

    # @validate_token
    # @http.route("/api/v1/check-in/check-invalid/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    # def v1_check_in_check_invalid(self, id=None, *payload):
    #     """ API gắn check in sai thong tin """
    #     check_in_id = request.env['crm.check.in'].sudo().browse(int(id))
    #     if check_in_id:
    #         check_in_id.sudo().write({
    #             'wrong': True
    #         })
    #         return valid_response_once([])
    #     else:
    #         return invalid_response("ERROR", "Khong tim thay check in id !!!")

    @validate_token
    @http.route("/api/v1/check-in/generate-otp/<phone>/<company_id>", type="http", auth="none", methods=["GET"],
                csrf=False)
    def v1_check_in_generate_otp(self, phone=None, company_id=None, *payload):
        """ API sinh otp """
        if phone:
            config = request.env['ir.config_parameter'].sudo()
            brand_code = request.brand_code

            date_now = datetime.now().date()

            sd = date_now - timedelta(days=1)
            ed = date_now + timedelta(days=1)

            query = ''' select count(*) from crm_check_in_otp where phone =  '%s' and company_id = %s and create_date > '%s' and create_date < '%s' ''' % (
                phone, company_id, sd, ed)
            request.env.cr.execute(query)
            count = request.env.cr.fetchone()
            # 2 sms otp trong 1 ngày của 1 cty
            # Todo set số limit trong config
            if count[0] < 2:
                otp = pyotp.TOTP('base32secret3232', digits=4).at(for_time=fields.datetime.now(), counter_offset=300)
                record = request.env['crm.check.in.otp'].sudo().create({
                    'otp': otp,
                    'phone': phone,
                    'company_id': company_id,
                    'stage': False
                })

                domain = config.get_param('domain_caresoft_%s' % (brand_code.lower()))
                token = config.get_param('domain_caresoft_token_%s' % (brand_code.lower()))
                service_id = config.get_param('domain_caresoft_service_id_%s' % (brand_code.lower()))

                sms = request.env['script.sms'].sudo().search(
                    [('company_id', '=', int(company_id)), ('type', '=', 'CI')])
                if sms:
                    content = sms.content
                    content = content.replace('[OTP]', otp)
                else:
                    content = 'Dung %s lam ma xac nhan thong tin tu van. Cam on quy khach!' % otp
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
                _logger.info("Send headers %s data %s", headers, data)

                res = requests.post(url, headers=headers, data=json.dumps(data))
                res = res.json()
                if 'code' in res and res['code'] == 'ok':
                    record.write({
                        'stage': 'sent'
                    })
                else:
                    record.write({
                        'stage': 'error'
                    })
                _logger.info("Response %s", res)

                return valid_response_once({
                    'otp': otp,
                    'phone': phone
                })
            return invalid_response("ERROR", "Đã hết lượt gửi OTP, Quý khách liên hệ lễ tân tư vấn để được hỗ trợ.")

    @validate_token
    @http.route("/api/v1/check-in/validate-otp/<phone>/<otp>/<company_id>", type="http", auth="none", methods=["GET"],
                csrf=False)
    def v1_check_in_validate_otp(self, phone=None, company_id=None, otp=None, *payload):
        date_now = datetime.now().date()
        sd = date_now - timedelta(days=1)
        ed = date_now + timedelta(days=1)

        query = ''' select count(*) from crm_check_in_otp where phone =  '%s' and otp = '%s' and company_id = %s and create_date > '%s' and create_date < '%s' ''' % (
            phone, otp, company_id, sd, ed)
        request.env.cr.execute(query)
        count = request.env.cr.fetchone()
        if count[0] > 0:
            return valid_response_once({
                'stage': 0,
            })
        else:
            return valid_response_once({
                'stage': 1,
            })

    @validate_token
    @http.route("/api/v1/check-in/booking-not-effect/<target>/<company_id>/<booking_id>", type="http", auth="none",
                methods=["GET"],
                csrf=False)
    def v1_check_in_booking_not_effect(self, target=None, *payload):
        if target == 'tu_van':
            data = {'stage': 'tu_van'}
        else:
            data = {'stage': 0}
        return valid_response_once(data)

    @http.route('/pt_attendance/kiosk_keepalive', auth='user', type='json')
    def kiosk_keepalive(self):
        request.httprequest.session.modified = True
        return {}

    @http.route('/check-in-patient', type="http")
    def checkin(self):
        local_tz = timezone('Etc/GMT+7')
        now = datetime.now()
        today = now.date()
        attendance = request.env['crm.check.in'].sudo().search(
            [('create_date', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
             ('create_date', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7)),
             ('create_uid', '=', request.env.user.id)], order='create_date desc')
        if attendance:
            booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = request.env.ref('crm.crm_menu_root').id
            html = ""
            stt = 0
            for rec in attendance:
                if rec.booking:
                    url = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                        rec.booking.id, booking_action_id, booking_menu_id)
                    stt += 1
                    html += "<tr><td scope='col' style='border-style: solid; border-width: thin; border-color: black' class='text-center'>" + str(
                        stt) + "</td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" + local_tz.localize(
                        rec.create_date, is_dst=None).astimezone(utc).replace(tzinfo=None).strftime(
                        "%d-%m-%Y %H:%M:%S") + "</td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'><a href='" + url + "' target='new'>" + rec.booking.name + "</a></td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" + rec.partner.name + "</td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" + \
                            STAGE[rec.stage] + "</td>"
                    html += "</tr>"
            return html
        return "<tr><td colspan='4'> Không có dữ liệu</td></tr>"

    @http.route('/check-out-patient', type="http")
    def checkout(self):
        local_tz = timezone('Etc/GMT+7')
        now = datetime.now()
        today = now.date()
        attendance = request.env['patient.attendance'].sudo().search([
            ('create_date', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
            ('create_date', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7))])
        if attendance:
            html = ""
            stt = 0
            for rec in attendance:
                stt += 1
                html += "<td scope='col'>" + str(
                    local_tz.localize(rec.check_out, is_dst=None).astimezone(utc).replace(tzinfo=None)) + "</td>"
                html += "<tr><td scope='col'>" + str(stt) + "</td>"
                html += "<td scope='col'>" + str(rec.patient_id.default_code) + "</td>"
                html += "<td scope='col'>" + rec.patient_id.name + "</td>"
                html += "</tr>"
            return html
        return "<tr><td colspan='4'> Không có dữ liệu</td></tr>"

    @http.route('/delete-check-in', type="http")
    def _delete_check_in(self, **kw):

        attendance = request.env['patient.attendance'].sudo().search([('id', '=', int(kw['id']))])
        if attendance:
            attendance.unlink()

        action_id = request.env.ref('patient.pt_attendance_action_kiosk_mode').id
        return request.redirect('/web#&action=' + str(action_id))

    @http.route('/delete-check-out', type="http")
    def _delete_check_out(self, **kw):

        attendance = request.env['patient.attendance'].sudo().search([('id', '=', int(kw['id']))])
        if attendance:
            attendance.check_out = False

        action_id = request.env.ref('patient.pt_attendance_action_kiosk_mode_checkout').id
        return request.redirect('/web#&action=' + str(action_id))

    @http.route('/get-data-check-in', type="http")
    def get_data_check_in(self, **kw):
        query = kw['q']
        local_tz = timezone('Etc/GMT+7')
        now = datetime.now()
        today = now.date()
        attendance = request.env['crm.check.in'].sudo().search(
            [('create_date', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
             ('create_date', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7)),
             ('create_uid', '=', request.env.user.id)], order='create_date desc')
        if len(query) > 0:
            attendance = request.env['crm.check.in'].sudo().search(
                [('create_date', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
                 ('create_date', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7)),
                 ('create_uid', '=', request.env.user.id), '|', '|',
                 ('booking.name', 'ilike', "%" + query + "%"),
                 ('partner.name', 'ilike', "%" + query + "%"),
                 ('partner.phone', 'ilike', "%" + query + "%")], order='create_date desc')
        elif query == "":
            attendance = request.env['crm.check.in'].sudo().search(
                [('create_date', 'like', '%' + str(today) + '%'), ('create_uid', '=', request.env.user.id)],
                order='create_date desc')

        booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
        booking_menu_id = request.env.ref('crm.crm_menu_root').id

        if attendance:
            html = ""
            for rec in attendance:
                if rec.booking:
                    url = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                        rec.booking.id, booking_action_id, booking_menu_id)
                    html += "<tr><td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" + local_tz.localize(
                        rec.create_date, is_dst=None).astimezone(utc).replace(tzinfo=None).strftime(
                        "%d-%m-%Y %H:%M:%S") + "</td>"
                    # html += "<tr><td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" +  rec.booking.name + "</td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'><a href='" + url + "' target='new'>" + rec.booking.name + "</a></td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" + rec.partner.name + "</td>"
                    html += "<td scope='col' style='border-style: solid; border-width: thin; border-color: black'>" + \
                            STAGE[rec.stage] + "</td>"
                    html += "</tr>"
            return html
        return "<tr><td colspan='4'> Không có dữ liệu</td></tr>"

    @http.route('/get-data-check-out', type="http")
    def get_data_check_out(self, **kw):
        query = kw['q'];
        local_tz = timezone('Etc/GMT+7')
        now = datetime.now()
        today = now.date()
        attendance = request.env['patient.attendance'].sudo().search(
            [('check_out', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
             ('check_out', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7))])
        if len(query) > 0:
            attendance = request.env['patient.attendance'].sudo().search(
                [('check_out', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
                 ('check_out', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7)), '|',
                 ('patient_id.default_code', 'like', "%" + query + "%"),
                 ('patient_id.name', 'like', "%" + query + "%")])
        elif query == "":
            attendance = request.env['patient.attendance'].sudo().search(
                [('check_out', 'like', '%' + str(today) + '%')])

        if attendance:
            html = ""
            for rec in attendance:
                html += "<tr><td scope='col' style='border-style: solid; border-width: medium; border-color: black'>" + rec.patient_id.default_code + "</td>"
                html += "<td scope='col' style='border-style: solid; border-width: medium; border-color: black'>" + rec.patient_id.name + "</td>"
                html += "<td scope='col' style='border-style: solid; border-width: medium; border-color: black'>" + str(
                    rec.check_out) + "</td>"
                html += "</tr>"
            return html
        return "<tr><td colspan='4'> Không có dữ liệu</td></tr>"
