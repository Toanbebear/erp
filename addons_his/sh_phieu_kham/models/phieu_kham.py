# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError, UserError


_logger = logging.getLogger(__name__)


class ShWalkinCancelMedical(models.Model):
	_inherit = 'sh.medical.appointment.register.walkin'

	@api.depends('reexam_ids.state')
	def _count_reexam(self):
		for record in self:
			record.reexam_count = len(record.reexam_ids.filtered(lambda s: s.state != 'Draft'))

	def action_view_phieu_kham(self):
		# start_time = datetime.datetime.now()
		domain = ['|', ('company_id', 'in', self.env.companies.ids), ('company2_id', 'in', self.env.companies.ids)]
		room_type_dict = {
			'shealth_all_in_one.group_sh_medical_physician_surgery': 'Surgery',
			'shealth_all_in_one.group_sh_medical_physician_odontology': 'Odontology',
			'shealth_all_in_one.group_sh_medical_physician_spa': 'Spa',
			'shealth_all_in_one.group_sh_medical_physician_laser': 'Laser'}

		room_types = []
		for grp, rt in room_type_dict.items():
			if self.env.user.has_group(grp):
				room_types.append(rt)
		if room_types:
			domain = [('room_type', 'in', room_types)] + domain
		# end_time = datetime.datetime.now(
		# execution_time = end_time - start_time
		# print(domain)
		# print("Thời gian thực hiện:", execution_time)
		action = self.env.ref('sh_phieu_kham.sh_phieu_kham_action').read()[0]
		action['domain'] = domain
		return action

	def action_open_phieu_xet_nghiem(self):
		self.ensure_one()
		action = self.env.ref('sh_phieu_kham.phieu_xet_nghiem_action').read()[0]
		action['domain'] = [('walkin', 'in', self.ids)]
		action['context'] = {
			'default_walkin': self.ids,
			'default_requestor': self.doctor.id,
			'default_patient': self.patient.id,
			'default_sex': self.sex,
			'default_dob': self.dob,
			'default_department': self.department.id,
			'default_institution': self.institution.id
		}
		if self.state in ['Scheduled', 'InProgress']:
			action['views'] = [[self.env.ref('sh_phieu_kham.tao_phieu_xet_nghiem_tree').id, 'tree']]
		return action

	def action_open_phieu_chan_doan_hinh_anh(self):
		self.ensure_one()
		action = self.env.ref('sh_phieu_kham.phieu_chan_doan_ha_action').read()[0]
		action['context'] = {
			'default_walkin': self.ids,
			'default_requestor': self.doctor.id,
			'default_patient': self.patient.id,
			'default_sex': self.sex,
			'default_dob': self.dob,
			'default_department': self.department.id,
			'default_institution': self.institution.id
		}

		action['domain'] = [('walkin', 'in', self.ids)]
		return action

	def action_open_phieu_phau_thuat_thu_thuat(self):
		self.ensure_one()
		action = self.env.ref('sh_phieu_kham.phieu_phau_thua_thu_thuat_action').read()[0]
		action['domain'] = [('walkin', 'in', self.ids)]
		return action

	def action_open_phieu_chuyen_khoa(self):
		self.ensure_one()
		action = self.env.ref('sh_phieu_kham.phieu_chuyen_khoa_action').read()[0]
		action['domain'] = [('walkin', 'in', self.ids)]
		return action

	def action_open_benh_nhan_luu(self):
		self.ensure_one()
		action = self.env.ref('sh_phieu_kham.phieu_benh_nhan_luu_action').read()[0]
		action['domain'] = [('walkin', 'in', self.ids)]
		return action

	def action_open_lich_tai_kham(self):
		self.ensure_one()
		action = self.env.ref('sh_phieu_kham.phieu_lich_tai_kham_action').read()[0]
		action['context'] = {
			'default_walkin': self.id,
			'default_company': self.institution.his_company.id,
			'default_patient': self.patient.id,
			'default_date': self.date,
			'default_services': self.service.ids,
		}
		action['domain'] = [('walkin', 'in', self.ids)]
		return action

	reexam_count = fields.Integer('Reexam count', compute="_count_reexam", store=True)
