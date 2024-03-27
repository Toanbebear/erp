# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import http
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh, \
	convert_string_to_date, get_company_id_hh, get_price_list_id_hh
from odoo.http import request

_logger = logging.getLogger(__name__)


class UpdateServiceBookingEHCController(http.Controller):
	@ehc_validate_token
	@http.route("/api/v1/update-service-booking", methods=["POST"], type="json", auth="none", csrf=False)
	def v1_ehc_update_service_booking(self, **payload):
		body = json.loads(request.httprequest.data.decode('utf-8'))
		_logger.info('========================= 9.1 API dịch vụ thực hiện ===================================')
		_logger.info(body)
		_logger.info('======================================================================================')
		field_require = [
			'booking_code',
			'service_order_form_id',
			'service_order_form_code',
			'medical_examination_stage',
			"key_data_master",
			"key_data",
			"service_code",
			"service_quantity",
			"service_unit_price",
			"service_discount",
			"service_source",
			"service_object",
			"service_designated_date",
			"service_date",
			"service_result_day",
			"service_designator",
			"service_executor",
			"service_result_payer",
			"service_designated_room",
			"service_implementation_room",
			"service_result_room",
			"service_status"
		]
		for field in field_require:
			if field not in body.keys():
				return {
					'stage': 1,
					'message': 'Thieu tham so %s!!!' % field
				}
		# search booking
		booking = request.env['crm.lead'].sudo().search(
			[('name', '=', body['booking_code']), ('brand_id.code', '=', 'HH')], limit=1)
		if booking:
			if booking.stage_id.id == request.env.ref('crm_base.crm_stage_confirm').id or booking.stage_id.id == request.env.ref('crm_base.crm_stage_paid').id:
				booking.stage_id = request.env.ref('crm_base.crm_stage_processing').id

			if body['medical_examination_stage'] == '3':
				for crm_line_id in booking.crm_line_ids:
					if crm_line_id.service_order_form_id == int(
							body['service_order_form_id']) and crm_line_id.service_order_form_code == body[
						'service_order_form_code']:
						crm_line_id.with_user(get_user_hh()).sudo().write({
							'service_status': '3'
						})
			else:
				if 'service_code' in body and body['service_code'] is None and 'key_data' in body and body['key_data']:
					line = booking.crm_line_ids.filtered(
						lambda s: s.key_data == int(body['key_data']))
					line.with_user(get_user_hh()).sudo().write({
						'service_status': str(body['service_status']),
					})
					return {
						'stage': 0,
						'message': 'Huy dich vu tren Booking thanh cong!'
					}
				else:
					# list_service_booking_erp = booking.crm_line_ids.mapped('product_id.default_code')
					dict_check_service = {}
					for service_booking_erp in booking.crm_line_ids:
						dict_check_service[service_booking_erp.product_id.default_code] = service_booking_erp.key_data
					service_code_check = 'EHC-' + body['service_code']
					product_erp = request.env['product.product'].sudo().search(
						[('default_code', '=', service_code_check)])
					if product_erp:
						service_his = request.env['sh.medical.health.center.service'].sudo().search(
							[('product_id', '=', product_erp.id)])
						if int(body['key_data_master']) != 0:
							unit_price = product_erp.lst_price
						else:
							if 'service_unit_price' in body and body['service_unit_price']:
								unit_price = body['service_unit_price']
							else:
								unit_price = 0
						# check user gắn vs dịch vụ
						service_designator = False
						service_result_payer = False
						service_executor = False
						if 'service_executor' in body and body['service_executor']:
							service_executor = request.env['crm.hh.ehc.user'].sudo().search(
								[('user_id', '=', body['service_executor'])], limit=1).id

						if 'service_result_payer' in body and body['service_result_payer']:
							service_result_payer = request.env['crm.hh.ehc.user'].sudo().search(
								[('user_id', '=', body['service_result_payer'])], limit=1).id

						if 'service_designator' in body and body['service_designator']:
							service_designator = request.env['crm.hh.ehc.user'].sudo().search(
								[('user_id', '=', body['service_designator'])], limit=1).id

						# check department gắn vs dịch vụ
						service_designated_room = False
						service_implementation_room = False
						service_result_room = False
						if 'service_designated_room' in body and body['service_designated_room']:
							service_designated_room = request.env['crm.hh.ehc.department'].sudo().search(
								[('room_id', '=', body['service_designated_room'])], limit=1).id

						if 'service_implementation_room' in body and body['service_implementation_room']:
							service_implementation_room = request.env['crm.hh.ehc.department'].sudo().search(
								[('room_id', '=', body['service_implementation_room'])], limit=1).id

						if 'service_result_room' in body and body['service_result_room']:
							service_result_room = request.env['crm.hh.ehc.department'].sudo().search(
								[('room_id', '=', body['service_result_room'])], limit=1).id

						source_payment = '0'
						if 'source_payment' in body and body['source_payment']:
							if body['source_payment'] in [0, 1]:
								source_payment = str(body['source_payment'])
							else:
								return {
									'stage': 1,
									'message': 'Tham so source_payment chi nhan 2 gia tri 0 va 1!!!'
								}

						# check nếu tồn tại 1 cặp giá trị service & key_data trên ERP thì cập nhật và ko có thì tạo mới
						if service_code_check in dict_check_service and int(body['key_data']) == int(
								dict_check_service[service_code_check]):
							line = booking.crm_line_ids.filtered(
								lambda s: s.key_data == int(
									body['key_data']) and s.product_id.default_code == service_code_check)
							line.with_user(get_user_hh()).sudo().write({
								'crm_id': booking.id,
								'service_id': service_his.id,
								'product_id': product_erp.id,
								'quantity': body['service_quantity'],
								'company_id': get_company_id_hh(),
								'unit_price': unit_price,
								'price_list_id': get_price_list_id_hh(),
								'status_cus_come': 'come',
								'key_data_master': body['key_data_master'],
								'key_data': body['key_data'],
								'service_order_form_id': body['service_order_form_id'],
								'service_order_form_code': body['service_order_form_code'],
								'service_object': str(body['service_object']),
								'service_status': str(body['service_status']),
								'service_designated_date': convert_string_to_date(
									body['service_designated_date']) if body[
									'service_designated_date'] else None,
								'service_date': convert_string_to_date(body['service_date']) if
								body['service_date'] else None,
								'service_result_day': convert_string_to_date(
									body['service_result_day']) if body[
									'service_result_day'] else None,
								'discount_cash': body['service_discount'],
								'service_designated_room': service_designated_room,
								'service_implementation_room': service_implementation_room,
								'service_result_room': service_result_room,
								'service_designator': service_designator,
								'service_result_payer': service_result_payer,
								'service_executor': service_executor,
								'source_payment': source_payment,
							})
							return {
								'stage': 0,
								'message': 'Cap nhat dich vu vao Booking thanh cong!'
							}
						else:
							booking.crm_line_ids.with_user(get_user_hh()).sudo().create(
								{
									'crm_id': booking.id,
									'service_id': service_his.id,
									'product_id': product_erp.id,
									'quantity': body['service_quantity'],
									'company_id': get_company_id_hh(),
									'unit_price': unit_price,
									'price_list_id': get_price_list_id_hh(),
									'status_cus_come': 'come',
									'key_data_master': body['key_data_master'],
									'key_data': body['key_data'],
									'service_order_form_id': body['service_order_form_id'],
									'service_order_form_code': body['service_order_form_code'],
									'service_object': str(body['service_object']),
									'service_status': str(body['service_status']),
									'service_designated_date': convert_string_to_date(
										body['service_designated_date']) if body[
										'service_designated_date'] else None,
									'service_date': convert_string_to_date(body['service_date']) if
									body['service_date'] else None,
									'service_result_day': convert_string_to_date(
										body['service_result_day']) if body[
										'service_result_day'] else None,
									'discount_cash': body['service_discount'],
									'service_designated_room': service_designated_room,
									'service_implementation_room': service_implementation_room,
									'service_result_room': service_result_room,
									'service_designator': service_designator,
									'service_result_payer': service_result_payer,
									'service_executor': service_executor,
									'source_extend_id': booking.source_id.id,
								}
							)
							return {
								'stage': 0,
								'message': 'Them dich vu vao Booking thanh cong!'
							}
					else:
						return {
							'stage': 1,
							'message': 'Khong tim thay dich vu co ma %s!!!' % body['service_code']
						}
		else:
			return {
				'stage': 1,
				'message': 'Khong tim thay Booking co ma %s!!!' % body['booking_code']
			}
