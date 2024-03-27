# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh, \
    convert_string_to_date, get_company_id_hh, get_price_list_id_hh, get_brand_id_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CreateBookingEHCController(http.Controller):

    @ehc_validate_token
    @http.route("/api/v1/create-booking", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_create_booking(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 8.2 API tạo booking ===================================')
        _logger.info(body)
        _logger.info('=================================================================================')
        field_require = [
            'treatment_id',
            'agent_email',
            'phone',
            'name',
            'gender',
            'source_code',
            'booking_date',
            'address',
            'address_2',
            'notes',
            'patient_code'
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        # check treatment_id: nếu có thì ko cho tạo bk
        booking = request.env['crm.lead'].sudo().search([('treatment_id', '=', int(body['treatment_id']))], limit=1)
        if booking:
            return {
                'stage': 0,
                'message': 'Khong the tao moi Booking do treatment_id %s da ton tai!!!' % body['treatment_id'],
                'data': {
                    'booking_code': booking.name
                }
            }

        gender = {
            '1': 'male',
            '2': 'female',
            '3': 'Transguy',
            '4': 'Transgirl',
            '5': 'other'
        }

        # xử lý sđt từ EHC
        check = 0
        if len(body['phone']) > 10:
            count = len(body['phone']) - 10
            phone_erp = body['phone'][count:]
            check = 1
        else:
            phone_erp = body['phone']
        if check != 0:
            # search partner theo sđt đã xử lý
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone_erp)], limit=1)
            if partner:
                booking_effect = request.env['crm.lead'].sudo().search(
                    [('type', '=', 'opportunity'), ('partner_id', '=', partner.id),
                     ('brand_id', '=', get_brand_id_hh()),
                     ('effect', '=', 'effect')])
                if booking_effect:
                    for booking in booking_effect:
                        booking.sudo().write({
                            'effect': 'expire'
                        })
            data_crm = {
                'phone': phone_erp,
                'contact_name': body['name'],
                'gender': gender[str(body['gender'])],
                'company_id': get_company_id_hh(),
                'brand_id': get_brand_id_hh(),
                'price_list_id': get_price_list_id_hh(),
                'street': body['address'],
                'note': body['notes'],
                'treatment_id': body['treatment_id']
            }

            data_partner = {
                'phone': phone_erp,
                'gender': gender[str(body['gender'])],
                'street': body['address'],
                'type_data_partner': 'new'
            }

            # check user
            user = request.env['res.users'].search([('login', '=', body['agent_email'])]).id
            if user:
                data_crm['create_by'] = user
                data_crm['assign_person'] = user
            else:
                user = get_user_hh()

            # tìm bệnh nhân
            patient_ehc = request.env['crm.hh.ehc.patient'].sudo().search([('patient_code', '=', body['patient_code'])],
                                                                          limit=1)

            if patient_ehc:
                patient_ehc.sudo().write({
                    'name': body['name'],
                })
                partner = patient_ehc.partner_id
            else:
                if partner:
                    # check khach hang cu moi
                    if partner.type_data_partner == 'new' or not partner.type_data_partner:
                        if partner.sudo().sale_order_ids:
                            for rec in partner.sudo().sale_order_ids:
                                if rec.state in ['sale', 'done']:
                                    data_crm['type_data_partner'] = 'old'
                                    data_partner['type_data_partner'] = 'old'
                                    break
                    partner.sudo().write(data_partner)
                    patient_ehc = request.env['crm.hh.ehc.patient'].sudo().create({
                        'partner_id': partner.id,
                        'name': body['name'],
                        'phone': body['phone'],
                        'patient_code': body['patient_code']
                    })
                else:
                    data_partner['name'] = body['name']
                    data_partner['code_customer'] = request.env['ir.sequence'].sudo().next_by_code('res.partner')
                    partner = request.env['res.partner'].with_user(user).sudo().create(data_partner)
                    patient_ehc = request.env['crm.hh.ehc.patient'].sudo().create({
                        'partner_id': partner.id,
                        'name': body['name'],
                        'phone': body['phone'],
                        'patient_code': body['patient_code']
                    })
                    data_crm['type_data_partner'] = 'new'

            data_crm['partner_id'] = partner.id
            data_crm['original_source_id'] = partner.source_id.id if partner.source_id else None

            # check booking date
            booking_date = convert_string_to_date(body['booking_date'])
            data_crm['booking_date'] = booking_date

            # check source
            source_code = body['source_code']
            if source_code[0:3] == 'CTV' or source_code[0:2] == 'HH':
                ctv = request.env['crm.collaborators'].sudo().search([('code_collaborators', '=', source_code)])
                if ctv:
                    data_crm['source_id'] = ctv.source_id.id
                    data_crm['collaborators_id'] = ctv.id
                    data_crm['category_source_id'] = ctv.source_id.category_id.id
                else:
                    return {
                        'stage': 1,
                        'message': 'Khong tim thay nguon bac si co ma %s!!!' % body['source_code']
                    }
            else:
                source = request.env['utm.source'].sudo().search(
                    [('code', '=', body['source_code']), ('brand_id.code', '=', 'HH')], limit=1)
                if source:
                    data_crm['source_id'] = source.id
                    data_crm['category_source_id'] = source.category_id.id
                else:
                    return {
                        'stage': 1,
                        'message': 'Khong tim thay nguon co ma %s!!!' % body['source_code']
                    }
            # tạo lead
            country_id = request.env['res.country'].sudo().search([('code', '=', 'VN')], limit=1)
            if country_id:
                data_crm['country_id'] = country_id.id
            else:
                data_crm['country_id'] = False
            data_crm['type'] = 'lead'
            data_crm['name'] = body['name']
            data_crm['type_crm_id'] = request.env.ref('crm_base.type_lead_new').id
            data_crm['stage_id'] = request.env.ref('crm_base.crm_stage_confirm').id
            record_lead = request.env['crm.lead'].with_user(user).sudo().create(data_crm)

            # tạo booking
            data_crm['type'] = 'opportunity'
            data_crm['name'] = '/'
            data_crm['type_crm_id'] = request.env.ref('crm_base.type_oppor_new').id
            data_crm['lead_id'] = record_lead.id if record_lead else False
            data_crm['customer_come'] = 'yes'
            # check type_data
            lead = request.env['crm.lead'].sudo().search(
                [('type', '=', 'lead'), ('partner_id', '=', partner.id),
                 ('brand_id', '=', get_brand_id_hh())])
            if len(lead) == 1 or len(lead) == 0:
                data_crm['type_data'] = 'new'
            else:
                data_crm['type_data'] = 'old'
            record_booking = request.env['crm.lead'].with_user(user).sudo().create(data_crm)
            if record_booking:
                if 'contract_code' in body and body['contract_code']:
                    contract_id = request.env['crm.hh.ehc.contract.group.exam'].sudo().search(
                        [('contract_code', '=', body['contract_code'])], limit=1)
                    if contract_id:
                        contract_id.write({
                            'crm_ids': [(6, 0, record_booking.id)],
                        })

                if not record_booking.crm_hh_ehc_medical_record_ids:
                    medical_record = request.env['crm.hh.ehc.medical.record'].sudo().create({
                        'booking_id': record_booking.id,
                        'patient_id': patient_ehc.id,
                        'status': '1',
                    })
                else:
                    record_booking.crm_hh_ehc_medical_record_ids[0].sudo().write({
                        'patient_id': patient_ehc.id,
                        'status': '1',
                    })
                phone_call = record_booking.sudo().create_phone_call()
                return {
                    'stage': 0,
                    'message': 'Tao Booking thanh cong!!!',
                    'data': {
                        'booking_code': record_booking.name
                    }
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Tao Booking that bai!!!',
                }
        else:
            # search partner theo sđt đã xử lý
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone_erp)], limit=1)
            # tìm bệnh nhân
            patient_ehc = request.env['crm.hh.ehc.patient'].sudo().search([('patient_code', '=', body['patient_code'])],
                                                                          limit=1)
            booking_effect = request.env['crm.lead'].sudo().search(
                [('type', '=', 'opportunity'), ('partner_id', '=', partner.id),
                 ('brand_id', '=', get_brand_id_hh()),
                 ('effect', '=', 'effect')], limit=1, order="id desc")
            if booking_effect:
                if 'contract_code' in body and body['contract_code']:
                    contract_id = request.env['crm.hh.ehc.contract.group.exam'].sudo().search(
                        [('contract_code', '=', body['contract_code'])], limit=1)
                    if contract_id:
                        contract_id.write({
                            'crm_ids': [(6, 0, booking_effect.id)],
                        })

                if not booking_effect.crm_hh_ehc_medical_record_ids:
                    medical_record = request.env['crm.hh.ehc.medical.record'].sudo().create({
                        'booking_id': booking_effect.id,
                        'patient_id': patient_ehc.id,
                        'status': '1',
                    })
                else:
                    booking_effect.crm_hh_ehc_medical_record_ids[0].sudo().write({
                        'patient_id': patient_ehc.id,
                        'status': '1',
                    })
                return {
                    'stage': 0,
                    'message': 'Don tiep thanh cong!!!',
                    'data': {
                        'booking_code': booking_effect.name
                    }
                }
            else:
                data_crm = {
                    'phone': phone_erp,
                    'contact_name': body['name'],
                    'gender': gender[str(body['gender'])],
                    'company_id': get_company_id_hh(),
                    'brand_id': get_brand_id_hh(),
                    'price_list_id': get_price_list_id_hh(),
                    'street': body['address'],
                    'note': body['notes'],
                    'treatment_id': body['treatment_id']
                }

                data_partner = {
                    'phone': phone_erp,
                    'gender': gender[str(body['gender'])],
                    'street': body['address'],
                    'type_data_partner': 'new'
                }

                # check user
                user = request.env['res.users'].search([('login', '=', body['agent_email'])]).id
                if user:
                    data_crm['create_by'] = user
                    data_crm['assign_person'] = user
                else:
                    user = get_user_hh()

                # tìm bệnh nhân
                patient_ehc = request.env['crm.hh.ehc.patient'].sudo().search(
                    [('patient_code', '=', body['patient_code'])],
                    limit=1)

                if patient_ehc:
                    patient_ehc.sudo().write({
                        'name': body['name'],
                    })
                    partner = patient_ehc.partner_id
                else:
                    if partner:
                        # check khach hang cu moi
                        if partner.type_data_partner == 'new' or not partner.type_data_partner:
                            if partner.sudo().sale_order_ids:
                                for rec in partner.sudo().sale_order_ids:
                                    if rec.state in ['sale', 'done']:
                                        data_crm['type_data_partner'] = 'old'
                                        data_partner['type_data_partner'] = 'old'
                                        break
                        partner.sudo().write(data_partner)
                        patient_ehc = request.env['crm.hh.ehc.patient'].sudo().create({
                            'partner_id': partner.id,
                            'name': body['name'],
                            'phone': body['phone'],
                            'patient_code': body['patient_code']
                        })
                    else:
                        data_partner['name'] = body['name']
                        data_partner['code_customer'] = request.env['ir.sequence'].sudo().next_by_code('res.partner')
                        partner = request.env['res.partner'].with_user(user).sudo().create(data_partner)
                        patient_ehc = request.env['crm.hh.ehc.patient'].sudo().create({
                            'partner_id': partner.id,
                            'name': body['name'],
                            'phone': body['phone'],
                            'patient_code': body['patient_code']
                        })
                        data_crm['type_data_partner'] = 'new'

                data_crm['partner_id'] = partner.id
                data_crm['original_source_id'] = partner.source_id.id if partner.source_id else None

                # check booking date
                booking_date = convert_string_to_date(body['booking_date'])
                data_crm['booking_date'] = booking_date

                # check source
                source_code = body['source_code']
                if source_code[0:3] == 'CTV' or source_code[0:2] == 'HH':
                    ctv = request.env['crm.collaborators'].sudo().search([('code_collaborators', '=', source_code)])
                    if ctv:
                        data_crm['source_id'] = ctv.source_id.id
                        data_crm['collaborators_id'] = ctv.id
                        data_crm['category_source_id'] = ctv.source_id.category_id.id
                    else:
                        return {
                            'stage': 1,
                            'message': 'Khong tim thay nguon bac si co ma %s!!!' % body['source_code']
                        }
                else:
                    source = request.env['utm.source'].sudo().search(
                        [('code', '=', body['source_code']), ('brand_id.code', '=', 'HH')], limit=1)
                    if source:
                        data_crm['source_id'] = source.id
                        data_crm['category_source_id'] = source.category_id.id
                    else:
                        return {
                            'stage': 1,
                            'message': 'Khong tim thay nguon co ma %s!!!' % body['source_code']
                        }
                # tạo lead
                country_id = request.env['res.country'].sudo().search([('code', '=', 'VN')], limit=1)
                if country_id:
                    data_crm['country_id'] = country_id.id
                else:
                    data_crm['country_id'] = False
                data_crm['type'] = 'lead'
                data_crm['name'] = body['name']
                data_crm['type_crm_id'] = request.env.ref('crm_base.type_lead_new').id
                data_crm['stage_id'] = request.env.ref('crm_base.crm_stage_confirm').id
                record_lead = request.env['crm.lead'].with_user(user).sudo().create(data_crm)

                # tạo booking
                data_crm['type'] = 'opportunity'
                data_crm['name'] = '/'
                data_crm['type_crm_id'] = request.env.ref('crm_base.type_oppor_new').id
                data_crm['lead_id'] = record_lead.id if record_lead else False
                data_crm['customer_come'] = 'yes'
                # check type_data
                lead = request.env['crm.lead'].sudo().search(
                    [('type', '=', 'lead'), ('partner_id', '=', partner.id),
                     ('brand_id', '=', get_brand_id_hh())])
                if len(lead) == 1 or len(lead) == 0:
                    data_crm['type_data'] = 'new'
                else:
                    data_crm['type_data'] = 'old'
                record_booking = request.env['crm.lead'].with_user(user).sudo().create(data_crm)
                if record_booking:
                    if 'contract_code' in body and body['contract_code']:
                        contract_id = request.env['crm.hh.ehc.contract.group.exam'].sudo().search(
                            [('contract_code', '=', body['contract_code'])], limit=1)
                        if contract_id:
                            contract_id.write({
                                'crm_ids': [(6, 0, record_booking.id)],
                            })

                    if not record_booking.crm_hh_ehc_medical_record_ids:
                        medical_record = request.env['crm.hh.ehc.medical.record'].sudo().create({
                            'booking_id': record_booking.id,
                            'patient_id': patient_ehc.id,
                            'status': '1',
                        })
                    else:
                        record_booking.crm_hh_ehc_medical_record_ids[0].sudo().write({
                            'patient_id': patient_ehc.id,
                            'status': '1',
                        })
                    phone_call = record_booking.sudo().create_phone_call()
                    return {
                        'stage': 0,
                        'message': 'Tao Booking thanh cong!!!',
                        'data': {
                            'booking_code': record_booking.name
                        }
                    }
                else:
                    return {
                        'stage': 1,
                        'message': 'Tao Booking that bai!!!',
                    }
