# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import http
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, convert_string_to_date
from odoo.http import request

_logger = logging.getLogger(__name__)


class UpdateMedicalRecordDepartmentEHCController(http.Controller):
	@ehc_validate_token
	@http.route("/api/v1/update-medical-record-department", methods=["POST"], type="json", auth="none", csrf=False)
	def v1_ehc_update_medical_record(self, **payload):
		body = json.loads(request.httprequest.data.decode('utf-8'))
		_logger.info(
			'========================= 10.2 API cập nhật bệnh án theo phòng ===================================')
		_logger.info(body)
		_logger.info('======================================================================================')
		field_require = [
			'booking_code',
			'patient_code',
			'room_id',
			'key_data',
		]
		for field in field_require:
			if field not in body:
				return {
					'stage': 1,
					'message': 'Thieu tham so %s!!!' % field
				}

		# search booking
		booking = request.env['crm.lead'].sudo().search([('name', '=', body['booking_code'])], limit=1)
		if booking:
			if booking.crm_hh_ehc_medical_record_ids:
				medical_record = booking.crm_hh_ehc_medical_record_ids[0]
				if medical_record:
					list_check_key_data = []
					for key_data_record_department in medical_record.crm_hh_ehc_medical_record_line_ids:
						list_check_key_data.append(key_data_record_department.key_data)

					processing_time = False
					if 'processing_time' in body and body['processing_time']:
						if body['processing_time'] != '000101010000':
							processing_time = convert_string_to_date(body['processing_time'])

					if not list_check_key_data:
						room = request.env['crm.hh.ehc.department'].sudo().search(
							[('room_id', '=', int(body['room_id']))], limit=1)
						if room:
							medical_record_department = request.env['crm.hh.ehc.medical.record.line'].sudo().create({
								'crm_hh_ehc_medical_record_line_id': medical_record.id,
								'key_data': body['key_data'],
								'room_id': room.id,
								'screening_information': body['screening_information'],
								'reason_for_examination': body['reason_for_examination'],
								'pathological_process': body['pathological_process'],
								'personal_history': body['personal_history'],
								'diagnose': body['diagnose'],
								'treatment_form': body['treatment_form'],
								'processing_time': processing_time,
								'desc_doctor': body['desc_doctor'],
								'result': body['result'],
							})
							return {
								'stage': 0,
								'message': 'Tao benh an theo phong thanh cong'
							}
					else:
						if 'key_data' in body and body['key_data']:
							for record_department in medical_record.crm_hh_ehc_medical_record_line_ids:
								if body['key_data'] in list_check_key_data:
									line = medical_record.crm_hh_ehc_medical_record_line_ids.filtered(
										lambda s: s.key_data == int(body['key_data']))
									line.sudo().write({
										'screening_information': body['screening_information'],
										'reason_for_examination': body['reason_for_examination'],
										'pathological_process': body['pathological_process'],
										'personal_history': body['personal_history'],
										'diagnose': body['diagnose'],
										'treatment_form': body['treatment_form'],
										'processing_time': processing_time,
										'desc_doctor': body['desc_doctor'],
										'result': body['result'],
									})
									return {
										'stage': 0,
										'message': 'Cap nhat benh an theo phong thanh cong'
									}
								else:
									room = request.env['crm.hh.ehc.department'].sudo().search(
										[('room_id', '=', int(body['room_id']))], limit=1)
									if room:
										record_department.sudo().create({
											'crm_hh_ehc_medical_record_line_id': medical_record.id,
											'key_data': body['key_data'],
											'room_id': room.id,
											'screening_information': body['screening_information'],
											'reason_for_examination': body['reason_for_examination'],
											'pathological_process': body['pathological_process'],
											'personal_history': body['personal_history'],
											'diagnose': body['diagnose'],
											'treatment_form': body['treatment_form'],
											'processing_time': processing_time,
											'desc_doctor': body['desc_doctor'],
											'result': body['result'],
										})
										return {
											'stage': 0,
											'message': 'Tao benh an theo phong thanh cong'
										}
									else:
										return {
											'stage': 1,
											'message': 'Khong tim thay phong kham co ID là %s' % body['room_id']
										}
						else:
							return {
								'stage': 1,
								'message': 'Tham so key_data dang rong'
							}
				else:
					return {
						'stage': 1,
						'message': 'Booking %s chua duoc tao benh an tong, lien he admin' % body['booking_code']
					}
			else:
				return {
					'stage': 1,
					'message': 'Booking %s chua duoc tao benh an tong, lien he admin' % body['booking_code']
				}
		else:
			return {
				'stage': 1,
				'message': 'Khong tim thay Booking co ma %s' % body['booking_code']
			}
