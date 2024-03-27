import logging
from datetime import datetime

import pytz

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class CrmEHC(models.Model):
	_inherit = "crm.lead"

	treatment_id = fields.Integer('Mã đón tiếp EHC')

	def create_booking_re_exam_ehc(self):
		patient_id = False
		if self.sudo().crm_hh_ehc_medical_record_ids:
			patient_id = self.sudo().crm_hh_ehc_medical_record_ids[0].patient_id
			if not patient_id:
				patient_id = self.env['crm.hh.ehc.patient'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
		return {
			'name': 'Booking',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
			'res_model': 'crm.lead',
			'context': {
				'default_phone': self.phone,
				'default_name': self.name,
				'default_contact_name': self.contact_name,
				'default_code_customer': self.code_customer,
				'default_customer_classification': self.customer_classification,
				'default_partner_id': self.partner_id.id,
				'default_aliases': self.aliases,
				'default_type_crm_id': self.env.ref('crm_ehc.type_oppor_re_exam_ehc').id,
				'default_type': self.type,
				'default_type_data': 'old',
				'default_type_data_partner': self.type_data_partner,
				'default_gender': self.gender,
				'default_birth_date': self.birth_date,
				'default_year_of_birth': self.year_of_birth,
				'default_mobile': self.mobile,
				'default_career': self.career,
				'default_pass_port': self.pass_port,
				'default_pass_port_date': self.pass_port_date,
				'default_pass_port_issue_by': self.pass_port_issue_by,
				'default_pass_port_address': self.pass_port_address,
				'default_country_id': self.country_id.id,
				'default_brand_id': self.brand_id.id,
				'default_state_id': self.state_id.id,
				'default_district_id': self.district_id.id,
				'default_street': self.street,
				'default_email_from': self.email_from,
				'default_facebook_acc': self.facebook_acc,
				'default_zalo_acc': self.zalo_acc,
				'default_stage_id': self.env.ref('crm_base.crm_stage_no_process').id,
				'default_company_id': self.company_id.id,
				'default_description': 'COPY',
				'default_special_note': self.special_note,
				'default_price_list_id': self.price_list_id.id,
				'default_currency_id': self.currency_id.id,
				'default_source_id': self.source_id.id,
				'default_collaborators_id': self.collaborators_id.id if self.collaborators_id else False,
				'default_campaign_id': self.campaign_id.id,
				'default_category_source_id': self.category_source_id.id,
				'default_work_online': self.work_online,
				'default_send_info_facebook': self.send_info_facebook,
				'default_online_counseling': self.online_counseling,
				'default_shuttle_bus': self.shuttle_bus,
				'default_root_booking_ehc': self.id,
				'default_customer_come': 'no',
				'default_lead_id': self.id,
				'default_booking_date': datetime.now(),
				'default_product_category_ids': [(6, 0, self.product_category_ids.ids)],
				'default_crm_hh_ehc_medical_record_ids': [(0, 0, {
					'booking_id': self.id,
					'patient_id': patient_id.id if patient_id else False,
					'status': '0',
				})],
			},
		}

	@api.model
	def create(self, vals):
		res = super(CrmEHC, self).create(vals)
		# tạo bệnh án
		if res.brand_id.code.lower() == 'hh' and res.type == 'opportunity':
			if not res.crm_hh_ehc_medical_record_ids:
				patient = self.env['crm.hh.ehc.patient'].sudo().search([('partner_id', '=', res.partner_id.id)], limit=1)
				res.crm_hh_ehc_medical_record_ids.sudo().create({
					'booking_id': res.id,
					'patient_id': patient.id if patient else False,
					'status': '0'
				})
		# xử lý quận huyện
		if res.type == 'opportunity':
			if res.lead_id.ward_id:
				res.ward_id = res.lead_id.ward_id.id

		# sinh mã bk tk
		if res.type_crm_id.id == self.env.ref('crm_ehc.type_oppor_re_exam_ehc').id:
			local_tz = pytz.timezone(self.env.user.tz or 'UTC')
			time = pytz.timezone('UTC').localize(datetime.now()).astimezone(local_tz)
			number = self.env.ref('crm_ehc.seq_crm_re_exam_ehc_opp_sci').number_next_actual
			prefix = 'TK'
			self.env['ir.sequence'].next_by_code('crm.lead.re.exam.ehc')
			res.name = "%s-%02s%02d%02d-%05d" % (prefix, str(time.year)[2:], time.month, time.day, number)
		return res
