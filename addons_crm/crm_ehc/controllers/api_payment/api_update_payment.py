# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh, \
	convert_string_to_date, get_price_list_id_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class UpdatePaymentEHCController(http.Controller):
	@ehc_validate_token
	@http.route("/api/v1/update-payment", methods=["POST"], type="json", auth="none", csrf=False)
	def v1_ehc_update_payment(self, **payload):
		body = json.loads(request.httprequest.data.decode('utf-8'))
		_logger.info('========================= 11.1 API cập nhật thanh toán ===================================')
		_logger.info(body)
		_logger.info('======================================================================================')
		field_require = [
			'booking_code',
			'invoice_code',
			'invoice_id',
			'amount_paid',
			'invoice_date',
		]
		for field in field_require:
			if field not in body.keys():
				return {
					'stage': 1,
					'message': 'Thieu tham so %s!!!' % field
				}
			if not body[field]:
				return {
					'stage': 1,
					'message': 'Tham so %s dang rong !!!' % field
				}

		# search booking
		booking = request.env['crm.lead'].sudo().search([('name', '=', body['booking_code']), '|',('company_id.brand_id.code', '=', 'HH'), ('company2_id.brand_id.code', '=', 'HH')], limit=1)
		if booking:
			value = {
				'booking_id': booking.id,
				'currency_id': request.env['product.pricelist'].sudo().browse(get_price_list_id_hh()).currency_id.id
			}

			if booking.crm_hh_ehc_medical_record_ids:
				patient = booking.sudo().crm_hh_ehc_medical_record_ids[0].patient_id
				if patient:
					value['patient_id'] = patient.id
				else:
					patient = request.env['crm.hh.ehc.patient'].sudo().search([('patient_code', '=', body['patient_code'])], limit=1)
					if patient:
						value['patient_id'] = patient.id
					else:
						value['patient_id'] = False
			else:
				patient = request.env['crm.hh.ehc.patient'].sudo().search([('patient_code', '=', body['patient_code'])], limit=1)
				if patient:
					value['patient_id'] = patient.id
				else:
					value['patient_id'] = False

			field_values = [
				'invoice_code',
				'invoice_id',
				'patient_code',
				'patient_name',
				'amount_paid',
				'invoice_group_code',
				'contract_code',
				'payment_code_erp'
			]
			for field_value in field_values:
				if field_value in body and body[field_value]:
					value['%s' % field_value] = body[field_value]

			if 'invoice_date' in body and body['invoice_date']:
				value['invoice_date'] = convert_string_to_date(body['invoice_date'])

			if 'invoice_status' in body and str(body['invoice_status']):
				if str(body['invoice_status']) in ['0', '1']:
					value['invoice_status'] = str(body['invoice_status'])
				else:
					return {
						'stage': 1,
						'message': 'Tham so invoice_status chi nhan 2 gia tri 0 va 1!!!'
					}

			if 'invoice_method' in body and body['invoice_method']:
				if body['invoice_method'] in [1, 2, 3, 4]:
					value['invoice_method'] = str(body['invoice_method'])
				else:
					return {
						'stage': 1,
						'message': 'Tham so invoice_method chi nhan 2 gia tri 1,2,3 va 4!!!'
					}

			if 'invoice_type' in body and body['invoice_type']:
				if body['invoice_type'] in [1, 2]:
					value['invoice_type'] = str(body['invoice_type'])
				else:
					return {
						'stage': 1,
						'message': 'Tham so invoice_type chi nhan 2 gia tri 1 va 2!!!'
					}

			if 'invoice_user' in body and body['invoice_user']:
				user = request.env['crm.hh.ehc.user'].sudo().search([('user_code', '=', body['invoice_user'])], limit=1)
				if user:
					value['invoice_user'] = user.id
				else:
					return {
						'stage': 1,
						'message': 'Khong tim thay user!!!'
					}

			if booking.statement_payment_ehc_ids:
				list_payment_check = []
				for statement_payment_ehc_id in booking.statement_payment_ehc_ids:
					list_payment_check.append(str(statement_payment_ehc_id.invoice_code))
				if str(body['invoice_code']) in list_payment_check:
					statement_payment_ehc_id = booking.statement_payment_ehc_ids.filtered(lambda x:
																						  x.invoice_code == str(
																							  body['invoice_code']))
					statement_payment_ehc_id.write(value)
					return {
						'stage': 0,
						'message': 'Cap nhat thang toan thanh cong!!!'
					}
				else:
					booking.statement_payment_ehc_ids.with_user(get_user_hh()).sudo().create(value)
					return {
						'stage': 0,
						'message': 'Tao phieu thanh toan thanh cong!!!'
					}
			else:
				booking.statement_payment_ehc_ids.with_user(get_user_hh()).sudo().create(value)
				return {
					'stage': 0,
					'message': 'Tao phieu thanh toan thanh cong!!!'
				}

		else:
			return {
				'stage': 1,
				'message': 'Khong tim thay Booking co ma %s!!!' % body['booking_code']
			}
