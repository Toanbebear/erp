import datetime
from datetime import date
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class CheckPartnerUpdateMethodQualify(models.TransientModel):
	_inherit = 'check.partner.qualify'
	_description = 'Update method qualify'

	def qualify(self):
		res = super(CheckPartnerUpdateMethodQualify, self).qualify()
		booking = self.env['crm.lead'].browse(int(res['res_id']))
		booking.sudo().write({
			'seminar_customers': booking.lead_id.seminar_customers
		})
		if not booking.lead_id.partner_id.seminar_customers:
			booking.lead_id.partner_id.sudo().write({
				'seminar_customers': booking.lead_id.seminar_customers
			})
		return res