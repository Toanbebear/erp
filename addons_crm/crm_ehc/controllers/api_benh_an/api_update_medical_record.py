# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh, \
	convert_string_to_date

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class UpdateMedicalRecordEHCController(http.Controller):
	@ehc_validate_token
	@http.route("/api/v1/update-medical-record", methods=["POST"], type="json", auth="none", csrf=False)
	def v1_ehc_update_medical_record(self, **payload):
		body = json.loads(request.httprequest.data.decode('utf-8'))
		_logger.info('========================= 10.1 API cập nhật bệnh án ===================================')
		_logger.info(body)
		_logger.info('======================================================================================')
		field_require = [
			'booking_code',
			'patient_code',
		]
		for field in field_require:
			if field not in body:
				return {
					'stage': 1,
					'message': 'Thieu tham so %s!!!' % field
				}

		# search booking
		booking = request.env['crm.lead'].sudo().search([('name', '=', body['booking_code']), '|',('company_id.brand_id.code', '=', 'HH'), ('company2_id.brand_id.code', '=', 'HH')], limit=1)
		if booking:
			value = {}
			# check field bình thường và khởi tạo
			field_values = [
				# 'booking_id',
				'patient_code',
				'patient_name',
				'patient_address',
				'amount_paid',
				'amount_due',
				'amount_discount',
				# 'desc_doctor',
				# 'result',
				# 'type',
				# 'screening_information',
				# 'reason_for_examination',
				# 'pathological_process',
				# 'personal_history',
				# 'diagnose',
				'processing_time',
				'treatment_form',
			]
			for field_value in field_values:
				if field_value in body and body[field_value]:
					value['%s' % field_value] = body[field_value]

			# check field có dạng date
			field_date_values = [
				'patient_birth_date',
				'reception_date',
				'in_date',
				'out_date',
				'appointment_date',
			]
			for field_date_value in field_date_values:
				if field_date_value in body and body[field_date_value]:
					if body[field_date_value] != '000101010000':
						value['%s' % field_date_value] = convert_string_to_date(body[field_date_value])
					else:
						value['%s' % field_date_value] = False
			# check field dạng selection
			if 'is_insurance' in body:
				if int(body['is_insurance']) in [0, 1]:
					if int(body['is_insurance']) == 0:
						value['is_insurance'] = True
					else:
						value['is_insurance'] = False
				else:
					return {
						'stage': 1,
						'message': 'Tham so is_insurance dang truyen sai, tham so is_insurance chi nhan 2 gia tri: 0 va 1!!!'
					}

			if 'status' in body and body['status']:
				if int(body['status']) in [0, 1, 2, 3]:
					value['status'] = str(body['status'])
				else:
					return {
						'stage': 1,
						'message': 'Tham so status dang truyen sai, tham so is_insurance chi nhan 2 gia tri: 0, 1, 2 va 3!!!'
					}

			if 'type_patient' in body:
				if int(body['type_patient']) in [0, 1, 2]:
					value['type_patient'] = str(body['type_patient'])

			if booking.crm_hh_ehc_medical_record_ids:
				booking.crm_hh_ehc_medical_record_ids[0].with_user(get_user_hh()).sudo().write(value)
				if not booking.crm_hh_ehc_medical_record_ids[0].patient_id:
					patient = request.env['crm.hh.ehc.patient'].sudo().search(
						[('patient_code', '=', body['patient_code'])],
						limit=1)
					if patient:
						booking.crm_hh_ehc_medical_record_ids[0].with_user(get_user_hh()).sudo().patient_id = patient.id
					else:
						patient = request.env['crm.hh.ehc.patient'].sudo().create({
							'patient_code': body['patient_code'],
							'name': body['patient_name'],
							'partner_id': booking.partner_id.id,
							'phone': booking.phone
						})
						if patient:
							booking.crm_hh_ehc_medical_record_ids[0].with_user(get_user_hh()).sudo().patient_id = patient.id
				return {
					'stage': 0,
					'message': 'Cap nhat benh an thanh cong'
				}
			else:
				if 'patient_code' in body and body['patient_code']:
					patient = request.env['crm.hh.ehc.patient'].sudo().search(
						[('patient_code', '=', body['patient_code'])],
						limit=1)
					if patient:
						value['patient_id'] = patient.id
						patient.sudo().write({
							'name': body['patient_name'],
						})
					else:
						patient = request.env['crm.hh.ehc.patient'].sudo().create({
							'patient_code': body['patient_code'],
							'name': body['patient_name'],
							'partner_id': booking.partner_id.id,
						})
						value['patient_id'] = patient.id
				value['booking_id'] = booking.id
				booking.crm_hh_ehc_medical_record_ids.with_user(get_user_hh()).sudo().create(value)
				return {
					'stage': 0,
					'message': 'Tao benh an thanh cong'
				}
		else:
			return {
				'stage': 1,
				'message': 'Khong tim thay Booking co ma %s' % body['booking_code']
			}
