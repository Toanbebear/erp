# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import get_company_id_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ServiceEHCController(http.Controller):
	@ehc_validate_token
	@http.route("/api/v1/update-service", methods=["POST"], type="json", auth="none", csrf=False)
	def v1_ehc_update_service(self, **payload):
		"""
			6.2 API cập nhật dịch vụ EHC-HIS
		"""
		# get body
		body = json.loads(request.httprequest.data.decode('utf-8'))
		_logger.info('========================= 6.2 API cập nhật dịch vụ EHC-HIS ==================')
		_logger.info(body)
		_logger.info('=================================================================================')

		field_require = [
			'service_id',
			'service_code',
			'service_name',
			'service_price',
			'service_price_bhyt',
			'service_type_id',
			'service_unit',
			'service_code_bhyt',
			'service_room_id',
			'stage'
		]
		for field in field_require:
			if field not in body.keys():
				return {
					'stage': 1,
					'message': 'Thieu tham so %s!!!' % field
				}

		if 'service_type_code' in body and body['service_type_code']:
			product_category_ehc = request.env['product.category'].sudo().search(
				[('code', '=', body['service_type_code'])], limit=1)
			if product_category_ehc:
				default_code_ehc = 'EHC-' + body['service_code']
				data = {
					'name': body['service_name'],
					'default_code': default_code_ehc,
					'service_id_ehc': body['service_id'],
					'service_code_ehc': body['service_code'],
					'lst_price': body['service_price'],
					'service_price_bhyt': body['service_price_bhyt'],
					'service_code_bhyt': body['service_code_bhyt'],
					'stage': str(body['stage']),
					'service_unit': body['service_unit'],
					'categ_id': product_category_ehc.id,
					'service_type': body['service_type_code']
				}
				room = []
				if 'service_room_id' in body and body['service_room_id']:
					roomes = body['service_room_id'].split(';')
					for rec_room in roomes:
						department = request.env['crm.hh.ehc.department'].sudo().search(
							[('room_id', '=', int(rec_room))], limit=1)
						if department:
							room.append((4, department.id))
				if room:
					data['service_room_ids'] = room

				exits_product = request.env['product.product'].sudo().search(
					[('default_code', '=', default_code_ehc)], limit=1)

				if exits_product:
					exits_product.product_tmpl_id.with_user(get_user_hh()).sudo().write(data)
					exits_product.with_user(get_user_hh()).sudo().write(data)
					exits_product.product_tmpl_id.write({'default_code': default_code_ehc})
					ServiceEHCController.update_service_his(service=exits_product, type=1)
					return {
						'stage': 0,
						'message': 'Cap nhat dich vu thanh cong!!!'
					}
				else:
					room = []
					if 'service_room_id' in body and body['service_room_id']:
						roomes = body['service_room_id'].split(';')
						for rec_room in roomes:
							department = request.env['crm.hh.ehc.department'].sudo().search(
								[('room_id', '=', int(rec_room))], limit=1)
							if department:
								room.append((4, department.id))
					if room:
						data['service_room_ids'] = room

					data['type'] = 'service'
					product_template = request.env['product.template'].with_user(get_user_hh()).sudo().create(data)
					product = request.env['product.product'].sudo().search(
						[('product_tmpl_id', '=', product_template.id)], limit=1)
					product.sudo().write({
						'service_id_ehc': body['service_id'],
						'service_code_ehc': body['service_code'],
						'service_price_bhyt': body['service_price_bhyt'],
						'service_code_bhyt': body['service_code_bhyt'],
						'stage': str(body['stage']),
						'service_room_ids': room,
						'service_type': body['service_type_code']
					})
					if product:
						ServiceEHCController.update_service_his(service=product, type=0)
					return {
						'stage': 0,
						'message': 'Cap nhat dich vu thanh cong!!!'
					}
			else:
				default_code_ehc = 'EHC-' + body['service_code']
				data = {
					'name': body['service_name'],
					'default_code': default_code_ehc,
					'service_id_ehc': body['service_id'],
					'service_code_ehc': body['service_code'],
					'lst_price': body['service_price'],
					'service_price_bhyt': body['service_price_bhyt'],
					'service_code_bhyt': body['service_code_bhyt'],
					'stage': str(body['stage']),
					'service_unit': body['service_unit'],
					'categ_id': request.env['product.category'].sudo().search(
						[('name', '=', 'All')]).id,
					'service_type': body['service_type_code']
				}

				room = []
				if 'service_room_id' in body and body['service_room_id']:
					roomes = body['service_room_id'].split(';')
					for rec_room in roomes:
						department = request.env['crm.hh.ehc.department'].sudo().search(
							[('room_id', '=', int(rec_room))], limit=1)
						if department:
							room.append((4, department.id))
				if room:
					data['service_room_ids'] = room
				exits_product = request.env['product.product'].sudo().search(
					[('default_code', '=', default_code_ehc)], limit=1)
				# exits_product_temp = request.env['product.template'].sudo().search(
				#     [('default_code', '=', default_code_ehc)], limit=1)
				if exits_product:
					exits_product.product_tmpl_id.with_user(get_user_hh()).sudo().write(data)
					exits_product.with_user(get_user_hh()).sudo().write(data)
					exits_product.product_tmpl_id.write({'default_code': default_code_ehc})
					ServiceEHCController.update_service_his(service=exits_product, type=1)
					return {
						'stage': 0,
						'message': 'Cap nhat dich vu thanh cong!!!'
					}
				else:

					room = []
					if 'service_room_id' in body and body['service_room_id']:
						roomes = body['service_room_id'].split(';')
						for rec_room in roomes:
							department = request.env['crm.hh.ehc.department'].sudo().search(
								[('room_id', '=', int(rec_room))], limit=1)
							if department:
								room.append((4, department.id))
					if room:
						data['service_room_ids'] = room
					data['type'] = 'service'
					product_template = request.env['product.template'].with_user(get_user_hh()).sudo().create(data)
					product = request.env['product.product'].sudo().search(
						[('product_tmpl_id', '=', product_template.id)], limit=1)
					product.sudo().write({
						'service_id_ehc': body['service_id'],
						'service_code_ehc': body['service_code'],
						'service_price_bhyt': body['service_price_bhyt'],
						'service_code_bhyt': body['service_code_bhyt'],
						'stage': str(body['stage']),
						'service_room_ids': room,
						'service_type': body['service_type_code']
					})
					if product:
						ServiceEHCController.update_service_his(service=product, type=0)
					return {
						'stage': 0,
						'message': 'Cap nhat dich vu thanh cong!!!'
					}
			# TODO gọi lại cron lấy loại dịch vụ
			# return {
			#     'stage': 1,
			#     'message': 'Khong tim thay nhom dich vu co ma %s!!!' % body['service_type_code']
			# }
		else:
			return {
				'stage': 1,
				'message': 'Kiem tra lai tham so truyen vao!!!'
			}

	def update_service_his(service, type):
		# 0: tạo mới
		# khác 0: cập nhật
		if service:
			health_center_ids = []
			health_center_id = request.env['sh.medical.health.center'].sudo().search(
				[('his_company.id', '=', get_company_id_hh())], limit=1)
			if health_center_id:
				health_center_ids.append((4, health_center_id.id))
			service_category = request.env['sh.medical.health.center.service.category'].sudo().sudo().search(
				[('code', '=', service.categ_id.code)], limit=1)
			data = {
				'name': service.name,
				'default_code': service.default_code,
				'product_id': service.id,
				'service_category': service_category.id if service_category else None,
				'his_service_type': 'ChiPhi',
				'institution': health_center_ids
			}
			if type == 0:
				service_his = request.env['sh.medical.health.center.service'].with_user(get_user_hh()).sudo().create(
					data)
				service.product_tmpl_id.write({'default_code': 'EHC' + service.service_code_ehc})
			else:
				service_his = request.env['sh.medical.health.center.service'].sudo().search(
					[('product_id', '=', service.id)], limit=1)
				service_his.with_user(get_user_hh()).sudo().write(data)
			# service.product_tmpl_id.write({'default_code': 'EHC' + service.service_code_ehc})
