from odoo import fields, models


class CrmEHCAddPatientCode(models.TransientModel):
	_name = 'crm.ehc.add.patient.code'
	_description = 'Add patient code'

	booking_id = fields.Many2one('crm.lead', string='Booking')
	partner_id = fields.Many2one('res.partner', string='Khách hàng', related='booking_id.partner_id')
	patient_code = fields.Char('Mã bệnh nhân')

	def add_patient_code(self):
		patient = self.env['crm.hh.ehc.patient'].search([('patient_code', '=', str(self.patient_code))], limit=1)
		if not patient:
			patient = self.env['crm.hh.ehc.patient'].create({
				'patient_code': self.patient_code,
				'partner_id': self.booking_id.partner_id.id,
				'phone': self.booking_id.phone,
				'name': self.booking_id.contact_name,
			})
		if self.booking_id.crm_hh_ehc_medical_record_ids:
			record = self.booking_id.crm_hh_ehc_medical_record_ids[0]
			record.patient_id = patient.id
		else:
			self.env['crm.hh.ehc.medical.record'].create({
				'booking_id': self.booking_id.id,
				'patient_id': patient.id if patient else False,
				'status': '0'
			})


class InheritCRM(models.Model):
	_inherit = 'crm.lead'

	def open_form_add_patinet_code(self):
		return {
			'name': 'Cập nhật bệnh nhân EHC',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': self.env.ref('crm_ehc.view_form_add_patient_code_ehc').id,
			'res_model': 'crm.ehc.add.patient.code',
			'context': {
				'default_booking_id': self.id,
			},
			'target': 'new'
		}
