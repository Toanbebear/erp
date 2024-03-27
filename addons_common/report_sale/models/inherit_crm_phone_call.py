import logging

from odoo import fields, api, models

_logger = logging.getLogger(__name__)

GROUP_REPORT = [('Other', 'Khác'), ('Surgery', 'Phẫu thuật'), ('Laser', 'Laser'), ('Spa', 'Spa'), ('Odontology', 'Nha'), ('None', 'None')]
GROUP_REPORT_CHECK = ['Surgery', 'Laser', 'Spa', 'Odontology']


class PhoneCall(models.Model):
	_inherit = 'crm.phone.call'

	group_report = fields.Selection(GROUP_REPORT, string='Nhóm báo cáo', compute='set_group_report', store=True)

	@api.depends('service_id')
	def set_group_report(self):
		for rec in self:
			list_check = []
			if rec.service_id:
				for service in rec.service_id:
					if service.his_service_type not in list_check and service.his_service_type in GROUP_REPORT_CHECK:
						list_check.append(service.his_service_type)
						if len(list_check) > 2:
							rec.group_report = 'Other'
							break
				if len(list_check) == 1:
					rec.group_report = list_check[0]
			else:
				rec.group_report = 'None'
