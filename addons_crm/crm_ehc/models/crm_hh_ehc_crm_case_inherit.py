import logging

from odoo import fields, api, models

_logger = logging.getLogger(__name__)


class CrmCase(models.Model):
	_inherit = "crm.case"

	case_coincide = fields.Boolean('Case trùng')
	check_case_ehc = fields.Boolean('EHC', compute='check_ehc', default=False, store=True)

	@api.depends('company_id')
	def check_ehc(self):
		for rec in self:
			rec.check_case_ehc = True if rec.company_id.code == "BVHH.HN.01" else False

	def set_case_coincide(self):
		self.ensure_one()
		self.case_coincide = True
		if self.crm_content_complain:
			for content in self.crm_content_complain:
				if content.stage != 'complete':
					content.sudo().write({'stage': 'complete'})