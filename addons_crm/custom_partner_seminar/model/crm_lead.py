from odoo import models, fields, api

seminar_customers = [
	('normal', 'KH bình thường'),
	('seminar', 'KH hội thảo')
]


class CrmLead(models.Model):
	_inherit = 'crm.lead'
	_description = 'CRM Lead'

	seminar_customers = fields.Selection(seminar_customers, string='Khách hàng hội thảo', default='normal')

	def create(self, vals):
		res = super(CrmLead, self).create(vals)
		if res.type == 'opportunity' and res.lead_id.seminar_customers:
			res.seminar_customers = res.lead_id.seminar_customers
		return res
