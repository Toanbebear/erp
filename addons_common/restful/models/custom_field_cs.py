import logging

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResBrand(models.Model):
	_inherit = 'res.brand'

	custom_field_cs = fields.One2many('custom.field.cs', 'brand_id', string='Danh sách field CS')
	config_phone_cs = fields.One2many('config.phone.call.care.soft', 'brand_id', string='Config phonecall CS')


class CustomFieldCS(models.Model):
	_name = 'custom.field.cs'
	_description = 'Custom field Care Soft'
	_rec_name = 'custom_field_lable'

	custom_field_id = fields.Integer('Custom field id')
	custom_field_lable = fields.Char('Custom field lable')
	type = fields.Char('Type field')
	brand_id = fields.Many2one('res.brand', string='Brand')
	code_custom_field = fields.Char('Code')
	values = fields.One2many('value.custom.field.cs', 'custom_field_cs_id', string='Values')

	def cron_get_custom_field(self):
		params = self.env['ir.config_parameter'].sudo()
		brands = self.env['res.brand'].search([('code', 'in', ['KN', 'PR', 'DA', 'HH'])])

		cs_custom_fields = {}
		cs_groups = {}
		cs_groups_dict = {}
		cs_custom_fields_dict = {}
		cs_service_code_custom_fields_id_dict = {}
		cs_service_code_custom_fields_id_dict_reverse = {}
		for brand in brands:
			domain_config = 'domain_caresoft_%s' % (brand.code.lower())
			token_config = 'domain_caresoft_token_%s' % (brand.code.lower())
			token = params.get_param(token_config)
			# get url of brand
			url = params.get_param(domain_config)
			# url = url + '/api/v1/tickets/custom_fields'
			headers = {
				'Authorization': 'Bearer ' + token,
				'Content-Type': 'application/json'
			}

			# get data
			r = requests.get('%s/api/v1/tickets/custom_fields' % url, headers=headers)
			response = r.json()

			# Tạo dictionary lưu custom_fields
			data_custom_fields = response
			custom_fields = data_custom_fields['custom_fields']
			dict_custom_fields = {}
			for custom_field in custom_fields:
				dict_custom_fields[custom_field['custom_field_id']] = custom_field

				cs_custom_fields_dict[custom_field['custom_field_id']] = custom_field['custom_field_lable']

				# Giá trị trong values cũng đưa vào dict
				if 'values' in custom_field:
					for value in custom_field['values']:
						cs_custom_fields_dict[value['id']] = value['lable']

						if 'Dịch vụ chi tiết' == custom_field['custom_field_lable'] or 'Dịch vụ chi tiết (*)' == \
								custom_field['custom_field_lable']:
							# Tạo dictionary
							# [KNPTCMM0053]Nhóm mắt
							# Tách mã dịch vụ
							codes = value['lable'].split(']')
							if codes:
								code = codes[0].replace('[', '')
								cs_service_code_custom_fields_id_dict[code] = value['id']
								cs_service_code_custom_fields_id_dict_reverse[value['id']] = code

			cs_custom_fields[brand.code] = dict_custom_fields

			# new field
			new_field = []
			for rec in response['custom_fields']:
				record_field = self.env['custom.field.cs'].search(
					[('custom_field_id', '=', int(rec['custom_field_id'])), ('brand_id', '=', brand.id)])
				if record_field:
					value_field = []
					record_field.values.unlink()
					if 'values' in rec and len(rec['values']) != 0:
						for value in rec['values']:
							value_field.append((0, 0, {
								'custom_field_cs_id': record_field.id,
								'id_value': int(value['id']),
								'lable_value': value['lable'],
							}))
					record_field.sudo().write({
						'custom_field_id': int(rec['custom_field_id']),
						'custom_field_lable': rec['custom_field_lable'],
						'type': rec['type'],
						'brand_id': brand.id,
						'values': value_field,
					})
				else:
					record = self.env['custom.field.cs'].sudo().create({
						'custom_field_id': int(rec['custom_field_id']),
						'custom_field_lable': rec['custom_field_lable'],
						'type': rec['type'],
						'brand_id': brand.id,
					})
					value_field = []
					if 'values' in rec and len(rec['values']) != 0:
						for value in rec['values']:
							value_field.append((0, 0, {
								'custom_field_cs_id': record.id,
								'id_value': int(value['id']),
								'lable_value': value['lable'],
							}))
					record.sudo().write({
						'values': value_field,
					})

			# Lấy dữ liệu groups từ caresoft
			resp = requests.get('%s/api/v1/groups' % url, headers=headers)
			data_groups = resp.json()
			groups = data_groups['groups']
			dict_groups = {}
			for group in groups:
				dict_groups[group['group_id']] = group
				cs_groups_dict[group['group_id']] = group['group_name']
			cs_groups[brand.code] = dict_groups

		params.set_param('cs_custom_fields', cs_custom_fields)
		params.set_param('cs_groups', cs_groups)
		params.set_param('cs_groups_dict', cs_groups_dict)
		params.set_param('cs_custom_fields_dict', cs_custom_fields_dict)
		params.set_param('cs_service_code_custom_fields_id_dict', cs_service_code_custom_fields_id_dict)
		params.set_param('cs_service_code_custom_fields_id_dict_reverse', cs_service_code_custom_fields_id_dict_reverse)


class ValuesCustomFieldCS(models.Model):
	_name = 'value.custom.field.cs'
	_description = 'Value custom field Care Soft'

	custom_field_cs_id = fields.Many2one('custom.field.cs', string='Custom field Care Soft', invisible=1)
	id_value = fields.Integer('ID Value')
	lable_value = fields.Char('Lable Value')
	code_value = fields.Char('Code Value')
