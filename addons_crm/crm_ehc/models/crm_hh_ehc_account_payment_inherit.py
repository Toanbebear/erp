import json
import logging

import requests

from odoo import fields, models, api
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class AccountPaymentInherit(models.Model):
	_inherit = "account.payment"

	statement_payment_ehc_ids = fields.One2many('crm.hh.ehc.statement.payment', 'payment_id',
												string='Danh sách phiếu thu EHC')
	check_ehc = fields.Boolean('Check EHC', compute='payment_check_ehc', default=False, store=True)

	@api.depends('company_id')
	def payment_check_ehc(self):
		for rec in self:
			if rec.company_id.code == 'BVHH.HN.01':
				rec.check_ehc = True
			else:
				rec.check_ehc = False

	def post(self):
		res = super(AccountPaymentInherit, self).post()
		if self.company_id.code == 'BVHH.HN.01' and self.crm_id:
			if self.crm_id.crm_hh_ehc_medical_record_ids and self.crm_id.crm_hh_ehc_medical_record_ids[0].status != '0':
				self.post_ehc()
		return res

	def post_ehc(self):
		token = get_token_ehc()
		url = get_url_ehc()
		api_code = get_api_code_ehc()

		url = url + '/api/votepayment?api=%s' % api_code

		headers = {
			'Content-Type': 'application/json',
			'Authorization': 'Bearer %s' % token,
		}
		date = self.payment_date
		payment_date = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d") + '000000'

		user_ehc = self.env['crm.hh.ehc.user'].sudo().search([('user_name', 'ilike', 'Quản Trị Hệ Thống')])

		payload = {
			"booking_code": self.crm_id.name,
			"payment_code": self.name,
			"amount": int(self.amount),
			"currency_id": self.currency_id.name,
			"payment_date": payment_date,
			"communication": self.communication,
			"user_name": self.partner_id.name,
			"user_code": user_ehc.user_code if user_ehc else ''
		}
		_logger.info("======== payload ===========")
		_logger.info(payload)
		r = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
		response = r.json()
		_logger.info("response: %s" % response)
		_logger.info("post payment done")


class StatementPaymentEHCInherit(models.Model):
	_inherit = "crm.hh.ehc.statement.payment"

	payment_id = fields.Many2one('account.payment', string='Phiếu thu tổng EHC')
