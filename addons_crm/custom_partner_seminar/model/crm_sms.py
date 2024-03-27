from odoo import models, fields, api


class CRMSMS(models.Model):
	_inherit = 'crm.sms'
	_description = 'CRM SMS'

	@api.model
	def create(self, vals):
		res = super(CRMSMS, self).create(vals)
		if res.crm_id.seminar_customers == 'seminar':
			res.sudo().write({
				'state': 'cancelled'
			})
		return res