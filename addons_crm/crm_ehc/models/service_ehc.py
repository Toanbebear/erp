import logging

import requests

from odoo import fields, models
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import get_user_hh, get_company_id_hh
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class ServiceEHC(models.Model):
	_name = "crm.hh.ehc.service"
	_description = 'Service EHC'

	service_id_ehc = fields.Integer('ID EHC')
	service_code_ehc = fields.Char('Mã EHC')
	name = fields.Char('Tên')
	list_price = fields.Integer('Đơn giá')
	service_price_bhyt = fields.Integer('Giá BHYT')
	service_code_bhyt = fields.Char('Mã BHYT')
	stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')], string='Trạng thái')
	service_type_code = fields.Char('Loại dịch vụ')
	service_type = fields.Char('Loại phẫu thuật')
	service_unit = fields.Char('Đơn vị tính')
	service_room_ids = fields.Many2many('crm.hh.ehc.department', 'crm_hh_ehc_department_rel', 'service_id', 'room_id',
										string='Phòng thực hiện')
	sync = fields.Boolean('Sync', default=False)

	# phân loại dịch vụ
	vs_hm = fields.Boolean('VSHM', default=False)
	pttm = fields.Boolean('PTTM', default=False)
	da_khoa = fields.Boolean('DAKHOA', default=False)

	def get_service_ehc(self):
		token = get_token_ehc()
		url = get_url_ehc()
		api_code = get_api_code_ehc()

		url = url + '/api/service?api=%s' % api_code

		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer %s' % token
		}
		codes = []
		services = self.env['crm.hh.ehc.service'].search([])
		for ser in services:
			codes.append(ser.service_code_ehc)
		r = requests.get(url, headers=headers)
		response = r.json()
		_logger.info('========================= cron get service ===================================')
		i = 0
		if 'data' in response and response['data']:
			for rec in response['data']:
				if rec['service_code'] not in ['XNHH0004', 'KB20', 'XNHH0001', 'XNHH0003', 'DVHH0527', 'DVHH_TM11',
											   'XNHS0059']:
					room = []
					if 'service_room_id' in rec and rec['service_room_id']:
						roomes = rec['service_room_id'].split(';')
						for rec_room in roomes:
							department = self.env['crm.hh.ehc.department'].search(
								[('room_id', '=', int(rec_room))], limit=1)
							if department:
								room.append((4, department.id))
					vs_hm = False
					pttm = False
					da_khoa = False
					if rec['service_code'] not in codes:
						service = self.env['crm.hh.ehc.service'].create({
							"service_id_ehc": rec['service_id'],
							"service_code_ehc": rec['service_code'],
							"name": rec['service_name'],
							"list_price": rec['service_price'],
							"service_price_bhyt": rec['service_price_bhyt'],
							"service_code_bhyt": str(rec['service_code_bhyt']),
							"service_type": rec['service_type'],
							"service_unit": rec['service_unit'],
							"service_type_code": rec['service_type_code'],
							"service_room_ids": room,
							"stage": str(rec['stage']),
							"vs_hm": vs_hm,
							"pttm": pttm,
							"da_khoa": da_khoa,
						})
						_logger.info("stt: %s" % i)
						_logger.info("create: %s" % service)
						i += 1
					else:
						service = self.env['crm.hh.ehc.service'].search(
							[('service_code_ehc', '=', rec['service_code'])])
						service.write({
							"service_id_ehc": rec['service_id'],
							# "service_code_ehc": rec['service_code'],
							"name": rec['service_name'],
							"list_price": rec['service_price'],
							"service_price_bhyt": rec['service_price_bhyt'],
							"service_code_bhyt": str(rec['service_code_bhyt']),
							"service_type": rec['service_type'],
							"service_type_code": rec['service_type_code'],
							"service_unit": rec['service_unit'],
							"stage": str(rec['stage']),
							"service_room_ids": room,
							"vs_hm": vs_hm,
							"pttm": pttm,
							"da_khoa": da_khoa,
						})
						_logger.info("stt: %s" % i)
						_logger.info("write: %s" % service)
						i += 1

	def create_prd_prd_service_ehc(self):
		services_ehc = self.env['crm.hh.ehc.service'].search([('sync', '=', False)], limit=300)
		# services_ehc = self.env['crm.hh.ehc.service'].search([('service_code_ehc', '=', 'KB25')])
		_logger.info('data: %s' % services_ehc)
		all_prd = self.env['product.product'].sudo().search([])
		dict_prd = {}
		for prd in all_prd:
			if prd.default_code:
				dict_prd[prd.default_code] = prd.id
		i = 0
		if services_ehc:
			for ser in services_ehc:
				_logger.info('ser: %s' % ser)
				roomes = []
				for rec_room in ser.service_room_ids:
					roomes.append((4, rec_room.id))

				default_code_ehc = 'EHC-' + ser.service_code_ehc
				value = {
					"service_id_ehc": ser.service_id_ehc,
					"service_code_ehc": ser.service_code_ehc,
					"name": ser.name,
					"list_price": ser.list_price,
					"service_price_bhyt": ser.service_price_bhyt,
					"default_code": default_code_ehc,
					"service_room_ids": roomes,
					# "service_room_code": rec['service_room_code'],
					# "service_type_id": rec['service_type_id'],
					# "service_type_code": rec['service_type_code'],
					# "group_master_id": rec['group_master_id'],
					# "group_master_code": rec['group_master_code'],
					"service_unit": ser.service_unit,
					"service_code_bhyt": ser.service_code_bhyt,
					"service_type": ser.service_type_code,
					"stage": str(ser.stage),
					"company_id": get_company_id_hh(),
					"responsible_id": get_user_hh(),
					"vs_hm": ser.vs_hm,
					"pttm": ser.pttm,
					"da_khoa": ser.da_khoa,
				}
				if ser.service_type_code:
					code_product_category = 'EHC-' + ser.service_type_code
					product_category = self.env['product.category'].sudo().search(
						[('code', '=', code_product_category)])
					if product_category:
						value['categ_id'] = product_category.id
					else:
						product_category = self.env['product.category'].sudo().search(
							[('name', '=', 'All')])
						value['categ_id'] = product_category.id
				if default_code_ehc in dict_prd:
					_logger.info('default_code_ehc')
					exits_product = self.env['product.product'].sudo().browse(dict_prd[default_code_ehc])
					exits_product.product_tmpl_id.sudo().write(value)
					exits_product.sudo().write(value)
					service_his = self.env['sh.medical.health.center.service'].sudo().search(
						[('product_id', '=', exits_product.id)])
					if service_his:
						service_his.sudo().write({
							'name': exits_product.name,
						})
					_logger.info("stt: %s" % i)
					_logger.info("write: %s" % exits_product)
					i += 1
				else:
					value['type'] = 'service'
					product_template = self.env['product.template'].sudo().create(value)
					product = self.env['product.product'].sudo().search(
						[('product_tmpl_id', '=', product_template.id)], limit=1)
					product.write({
						"service_code_ehc": ser.service_code_ehc,
						"service_price_bhyt": ser.service_price_bhyt,
						"service_unit": ser.service_unit,
						"service_code_bhyt": ser.service_code_bhyt,
						"service_type": ser.service_type_code,
						"stage": str(ser.stage),
						"service_room_ids": roomes,
						"vs_hm": ser.vs_hm,
						"pttm": ser.pttm,
						"da_khoa": ser.da_khoa,
					})
					if product:
						service_his = self.env['sh.medical.health.center.service'].sudo().search(
							[('product_id', '=', product.id)])
						if service_his:
							service_his.sudo().write({
								'name': product.name,
							})
						else:
							service_category = self.env[
								'sh.medical.health.center.service.category'].sudo().search(
								[('code', '=', product.categ_id.code)], limit=1)
							service_his = self.env['sh.medical.health.center.service'].sudo().create({
								'name': product.name,
								'default_code': product.default_code,
								'product_id': product.id,
								'service_category': service_category.id if service_category else None,
								'his_service_type': 'ChiPhi'
							})
						_logger.info("stt: %s" % i)
						_logger.info("create: %s" % product)
						i += 1
					ser.sync = True
					product = self.env['product.product'].sudo().search(
						[('product_tmpl_id', '=', product_template.id)], limit=1)
					health_center_ids = []
					health_center_id = self.env['sh.medical.health.center'].sudo().search(
						[('his_company.id', '=', get_company_id_hh())], limit=1)
					if health_center_id:
						health_center_ids.append((4, health_center_id.id))
					if product:
						service_his = self.env['sh.medical.health.center.service'].sudo().search(
							[('product_id', '=', product.id)])
						if service_his:
							service_his.sudo().write({
								'name': product.name,
								'institution': health_center_ids
							})
						else:
							service_category = self.env['sh.medical.health.center.service.category'].sudo().search(
								[('code', '=', product.categ_id.code)], limit=1)
							service_his = self.env['sh.medical.health.center'].sudo().create({
								'name': product.name,
								'default_code': product.default_code,
								'product_id': product.id,
								'service_category': service_category.id if service_category else None,
								'his_service_type': 'ChiPhi',
								'institution': health_center_ids
							})
				ser.sync = True
