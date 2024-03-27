# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, convert_string_to_date

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GetBookingEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/get-booking", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_get_booking(self, **payload):
        """
            8.1 API lấy danh sách booking
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 8.1 API lấy danh sách booking =========================')
        _logger.info(body)
        _logger.info('=================================================================================')
        # domain = [('type', '=', 'opportunity')]
        domain = [('type', '=', 'opportunity'), '|',('company_id.brand_id.code', '=', 'HH'), ('company2_id.brand_id.code', '=', 'HH')]
        if body['booking_code']:
            domain.append(('name', '=', body['booking_code']))
            data = request.env['crm.lead'].sudo().search(domain, limit=1)
        else:
            if body['phone']:
                if len(body['phone']) == 11:
                    phone_search_erp = body['phone'][1:]
                    domain.append(('phone', '=', phone_search_erp))
                else:
                    domain.append(('phone', '=', body['phone']))
            if body['date_from']:
                domain.append(('booking_date', '>=', convert_string_to_date(body['date_from'])))
            if body['date_to']:
                domain.append(('booking_date', '<=', convert_string_to_date(body['date_to'])))
            data = request.env['crm.lead'].sudo().search(domain)
        list_booking = []
        if 'phone' in body and body['phone'] and len(body['phone']) == 11:
            for item in data:
                if not item.crm_hh_ehc_medical_record_ids or str(item.crm_hh_ehc_medical_record_ids[0].status) == '0' or \
                        item.crm_hh_ehc_medical_record_ids[0].status == False:
                    if item.crm_hh_ehc_medical_record_ids[0].patient_id.phone == body['phone']:
                        list_service = []
                        for service in item.crm_line_ids:
                            list_service = [{
                                'service_code': service.product_id.default_code,
                                'service_name': service.product_id.name,
                            }]
                        birth_date = ''
                        if item.birth_date:
                            date = item.birth_date
                            birth_date = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d") + '000000'

                        gender = {
                            'male': '1',
                            'female': '2',
                            'transguy': '3',
                            'transgirl': '4',
                            'other': '5',
                        }

                        patient_code = False
                        if item.crm_hh_ehc_medical_record_ids and item.crm_hh_ehc_medical_record_ids[0].patient_code:
                            patient_code = item.crm_hh_ehc_medical_record_ids[0].patient_code
                        else:
                            patient = request.env['crm.hh.ehc.patient'].sudo().search([('partner_id', '=', item.partner_id.id)], limit=1)
                            if patient:
                                patient_code = patient.patient_code

                        # tên bệnh nhân
                        patient_name = ''
                        if item.crm_hh_ehc_medical_record_ids:
                            if item.crm_hh_ehc_medical_record_ids[0].patient_id:
                                patient_name = item.crm_hh_ehc_medical_record_ids[0].patient_id.name
                            else:
                                patient_name = item.partner_id.name
                        else:
                            patient_name = item.partner_id.name

                        state_id = '00'
                        district_id = '000'
                        ward_id = '00000'
                        if item.state_id:
                            if item.state_id.id_dvhc:
                                state_id = item.state_id.id_dvhc
                            else:
                                state_id = item.state_id.cs_id
                            if len(str(state_id)) == 1:
                                state_id = '0' + str(state_id)

                        if item.district_id:
                            if item.district_id.id_dvhc:
                                district_id = item.district_id.id_dvhc
                            else:
                                district_id = item.district_id.cs_id
                            if len(str(district_id)) == 1:
                                district_id = '00' + str(district_id)

                            if len(str(district_id)) == 2:
                                district_id = '00' + str(district_id)

                        if item.ward_id:
                            if item.ward_id.id_dvhc:
                                ward_id = item.ward_id.id_dvhc
                            if len((str(ward_id))) == 1:
                                ward_id = '0000' + str(ward_id)

                            if len((str(ward_id))) == 2:
                                ward_id = '000' + str(ward_id)

                            if len((str(ward_id))) == 3:
                                ward_id = '00' + str(ward_id)

                            if len((str(ward_id))) == 4:
                                ward_id = '0' + str(ward_id)

                        list_booking.append({
                            'booking_code': item.name,
                            'patient_name': patient_name,
                            'patient_code': patient_code,
                            'patient_birth_date': birth_date,
                            'gender': gender[item.gender],
                            'phone': item.phone,
                            'patient_address': item.street,
                            'patient_address_2': "%s,%s,%s" % (
                                state_id, district_id, ward_id),
                            'source_code': item.source_id.code,
                            'notes': item.note if item.note else '',
                            'services': list_service,
                        })

        else:
            for item in data:
                if not item.crm_hh_ehc_medical_record_ids or str(item.crm_hh_ehc_medical_record_ids[0].status) == '0' or \
                        item.crm_hh_ehc_medical_record_ids[0].status == False:
                    list_service = []
                    for service in item.product_category_ids:
                        list_service = [{
                            'service_code': service.code,
                            'service_name': service.name,
                        }]
                    birth_date = ''
                    if item.birth_date:
                        date = item.birth_date
                        birth_date = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d") + '000000'

                    gender = {
                        'male': '1',
                        'female': '2',
                        'transguy': '3',
                        'transgirl': '4',
                        'other': '5',
                    }
                    patient_code = False
                    if item.crm_hh_ehc_medical_record_ids and item.crm_hh_ehc_medical_record_ids[0].patient_code:
                        patient_code = item.crm_hh_ehc_medical_record_ids[0].patient_code
                    else:
                        patient = request.env['crm.hh.ehc.patient'].sudo().search(
                            [('partner_id', '=', item.partner_id.id)], limit=1)
                        if patient:
                            patient_code = patient.patient_code

                    # tên bệnh nhân
                    patient_name = ''
                    if item.crm_hh_ehc_medical_record_ids:
                        if item.crm_hh_ehc_medical_record_ids[0].patient_id:
                            patient_name = item.crm_hh_ehc_medical_record_ids[0].patient_id.name
                        else:
                            patient_name = item.partner_id.name
                    else:
                        patient_name = item.partner_id.name

                    state_id = '00'
                    district_id = '000'
                    ward_id = '00000'
                    if item.state_id:
                        if item.state_id.id_dvhc:
                            state_id = item.state_id.id_dvhc
                        else:
                            state_id = item.state_id.cs_id
                        if len(str(state_id)) == 1:
                            state_id = '0' + str(state_id)

                    if item.district_id:
                        if item.district_id.id_dvhc:
                            district_id = item.district_id.id_dvhc
                        else:
                            district_id = item.district_id.cs_id
                        if len(str(district_id)) == 1:
                            district_id = '00' + str(district_id)

                        if len(str(district_id)) == 2:
                            district_id = '00' + str(district_id)
                    if item.ward_id:
                        if item.ward_id.id_dvhc:
                            ward_id = item.ward_id.id_dvhc
                        if len((str(ward_id))) == 1:
                            ward_id = '0000' + str(ward_id)

                        if len((str(ward_id))) == 2:
                            ward_id = '000' + str(ward_id)

                        if len((str(ward_id))) == 3:
                            ward_id = '00' + str(ward_id)

                        if len((str(ward_id))) == 4:
                            ward_id = '0' + str(ward_id)

                    # check source
                    if item.collaborators_id:
                        source_id = item.collaborators_id.code_collaborators
                    else:
                        source_id = item.source_id.code

                    list_booking.append({
                        'booking_code': item.name,
                        'patient_name': patient_name,
                        'patient_code': patient_code,
                        'patient_birth_date': birth_date,
                        'gender': gender[item.gender],
                        'phone': item.phone,
                        'patient_address': item.street,
                        'patient_address_2': "%s,%s,%s" % (
                            state_id, district_id, ward_id),
                        'source_code': source_id,
                        'notes': item.note if item.note else '',
                        'services': list_service,
                    })
        if list_booking:
            return {
                'stage': 0,
                'message': 'Lay du lieu booking thanh cong!!!',
                'data': list_booking
            }
        else:
            return {
                'stage': 1,
                'message': 'Khong co du lieu!!!'
            }
