import json
import logging
from datetime import datetime, timedelta

import requests
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc, get_company_bvhh

from odoo import fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

TYPE_PATIENT = [('0', 'Khám bệnh'), ('1', 'Ngoại trú'), ('2', 'Nội trú')]


class MedicalRecordEHC(models.Model):
	_name = 'crm.hh.ehc.medical.record'
	_inherits = {'crm.lead': 'booking_id'}
	_description = 'Medical record EHC'

	type_patient = fields.Selection(TYPE_PATIENT, string='Loại bệnh nhân')
	is_insurance = fields.Boolean(string='Bảo hiểm y tế', default=False)
	patient_birth_date = fields.Date(string='Ngày sinh bệnh nhân')
	patient_address = fields.Char('Địa chỉ')
	status = fields.Selection([('0', 'Chưa đến'), ('1', 'Đã đến'), ('2', 'Đã thực hiện'), ('3', 'Đã ra viện')],
							  'Trạng thái', track_visibility='always')

	patient_code = fields.Char(string='Mã bệnh nhân', related='patient_id.patient_code', store=True)
	patient_name = fields.Char(string='Tên bệnh nhân', related='patient_id.name')

	processing_time = fields.Char('Thời gian xử trí')
	treatment_form = fields.Char('Hình thức xử trí')

	amount_paid = fields.Integer('Tổng tiền đã thu')
	amount_due = fields.Integer('Tiền chi phí')
	amount_discount = fields.Integer('Tổng tiền miễn giảm')

	reception_date = fields.Date(string='Ngày vào viện')
	in_date = fields.Date(string='Ngày nhập viện')
	out_date = fields.Date(string='Ngày ra viện')
	appointment_date = fields.Date(string='Ngày hẹn')
	date_cut = fields.Datetime(string='Ngày thay băng cắt chỉ')

	day_process = fields.Datetime('Day process')
	bol_process = fields.Boolean('Check process', default=False)
	day_exam = fields.Datetime('Ngày tái khám')
	bol_exam = fields.Boolean('Check exam', default=False)
	guarantee_day = fields.Datetime('Day guarantee')
	bol_guarantee = fields.Boolean('check guarantee', default=False)

	booking_id = fields.Many2one('crm.lead', string='Booking EHC', auto_join=True, ondelete="cascade", required=True)
	patient_id = fields.Many2one('crm.hh.ehc.patient', string='Bệnh nhân' , tracking=True)
	crm_hh_ehc_medical_record_line_ids = fields.One2many('crm.hh.ehc.medical.record.line', 'crm_hh_ehc_medical_record_line_id',
														 string='Bệnh án theo phòng')

	vs_hm = fields.Boolean(string='Vô sinh hiếm muộn')
	pt_tm = fields.Boolean(string='Phẫu thuật thẩm mỹ và LGBT')
	da_khoa = fields.Boolean(string='Đa khoa')
	script_pc = fields.Text('Kịch bản phone call', default='/')

	def create_sms(self, booking_id):
		if booking_id:
			sms = self.env['crm.sms'].sudo().search(
				[('crm_id', '=', booking_id.id), ('name', 'ilike', 'Cảm ơn Khách hàng làm dịch vụ')], limit=1)
			if not sms:
				script_sms = booking_id.company_id.script_sms_id
				for item in script_sms:
					if item.run:
						if item.type == 'COKHLDV':
							content_sms = item.content.replace('[Ten_KH]', booking_id.partner_id.name)
							sms = self.env['crm.sms'].sudo().create({
								'name': 'Cảm ơn Khách hàng làm dịch vụ',
								'contact_name': booking_id.contact_name,
								'partner_id': booking_id.partner_id.id,
								'phone': booking_id.phone,
								'company_id': booking_id.company_id.id,
								'company2_id': [(6, 0, booking_id.company2_id.ids)],
								'crm_id': booking_id.id,
								'send_date': datetime.now(),
								'desc': content_sms,
								'id_reexam': False
							})

	def write(self, vals):
		res = super(MedicalRecordEHC, self).write(vals)
		for rec in self:
			if rec.status == '1':
				# cập nhật trạng thái booking
				if rec.booking_id.customer_come == 'no':
					rec.booking_id.customer_come = 'yes'
					rec.booking_id.stage_id = self.env.ref('crm_base.crm_stage_confirm').id

				if not rec.booking_id.arrival_date:
					rec.booking_id.arrival_date = datetime.now()

				# bệnh án chuyển trạng thái đã đến sẽ đẩy payment đặt cọc
				_logger.info("post payment")
				list_payment = request.env['account.payment'].sudo().search(
					[('company_id', '=', get_company_bvhh().id), ('crm_id', '=', rec.booking_id.id),
					 ('internal_payment_type', '=', 'tai_don_vi'), ('state', '=', 'posted')])
				_logger.info("list_payment: %s" % list_payment)
				for payment in list_payment:
					token = get_token_ehc()
					url = get_url_ehc()
					api_code = get_api_code_ehc()

					url = url + '/api/votepayment?api=%s' % api_code

					headers = {
						'Content-Type': 'application/json',
						'Authorization': 'Bearer %s' % token,
					}
					date = payment.payment_date
					payment_date = date.strftime("%Y") + date.strftime("%m") + date.strftime("%d") + '000000'

					user_ehc = self.env['crm.hh.ehc.user'].sudo().search([('user_name', 'ilike', 'Quản Trị Hệ Thống')])

					payload = {
						"booking_code": payment.crm_id.name,
						"payment_code": payment.name,
						"amount": int(payment.amount),
						"currency_id": payment.currency_id.name,
						"payment_date": payment_date,
						"communication": payment.communication,
						"user_name": payment.partner_id.name,
						"user_code": user_ehc.user_code if user_ehc else ''
					}
					_logger.info("======== payload ===========")
					_logger.info(payload)
					r = requests.request("POST", url=url, data=json.dumps(payload), headers=headers)
					response = r.json()
					_logger.info("response: %s" % response)
				_logger.info("post payment done")
			# đóng bệnh án
			if vals.get('status') == '3':
				# check nếu booking có tiền thì chuyển trạng thái won và sinh sms, pc
				if rec.booking_id.statement_payment_ehc_ids:
					rec.booking_id.stage_id = self.env.ref('crm.stage_lead4').id
					rec.booking_id.effect = 'expire'
					# sinh PC
					if rec.booking_id.type_crm_id.id == self.env.ref(
							'crm_ehc.type_oppor_re_exam_ehc').id or rec.booking_id.category_source_id.code == 'TPM':
						pass
					else:
						self.create_sms(booking_id=rec.booking_id)
						# dịch vụ pttm
						for crm_line in rec.booking_id.crm_line_ids:
							if crm_line.service_id.days_reexam and not crm_line.create_phone_call:
								for rec_pc_config in crm_line.service_id.days_reexam:
									pc = self.env['crm.phone.call'].create({
										'name': '%s - %s' % (rec_pc_config.script_id.name, rec.booking_id.name),
										'subject': 'Chăm sóc sau dịch vụ',
										'partner_id': rec.booking_id.partner_id.id,
										'phone': rec.booking_id.partner_id.phone,
										'direction': 'out',
										'company_id': rec.booking_id.company_id.id,
										'crm_id': rec.booking_id.id,
										'country_id': rec.booking_id.country_id.id,
										'street': rec.booking_id.street,
										'type_crm_id': self.env.ref('crm_base.type_phone_call_after_service_care').id,
										'booking_date': rec.booking_id.booking_date,
										'call_date': rec.out_date + timedelta(days=int(
											rec_pc_config.after_service_date)) if rec.out_date else datetime.now() + timedelta(
											days=int(rec_pc_config.after_service_date))
									})
									if pc:
										crm_line.create_phone_call = True
						# ==================================================
						# check dịch vụ theo nhóm
						config = self.env['ir.config_parameter'].sudo()
						nhom_vshm = eval(config.get_param('nhom_vshm'))
						nhom_da_khoa = eval(config.get_param('nhom_da_khoa'))
						list_line = []
						list_service = []
						for crm_line in rec.booking_id.crm_line_ids:
							if crm_line.product_id.default_code not in list_service:
								list_service.append(crm_line.product_id.default_code)
								list_line.append(crm_line)

						for crm_line in list_line:
							# check vshm
							if crm_line.product_id.service_code_ehc in nhom_vshm and not crm_line.create_phone_call:
								call_date1 = vals.get('out_date') + timedelta(
									days=int(config.get_param('date_first_vshm'))) if vals.get(
									'out_date') else datetime.now() + timedelta(
									days=int(config.get_param('date_first_vshm')))
								pc1 = self.env['crm.phone.call'].create({
									'name': 'Chăm sóc SDV VSHM lần 1',
									'subject': 'Chăm sóc sau dịch vụ',
									'partner_id': rec.booking_id.partner_id.id,
									'phone': rec.booking_id.partner_id.phone,
									'direction': 'out',
									'company_id': rec.booking_id.company_id.id,
									'crm_id': rec.booking_id.id,
									'country_id': rec.booking_id.country_id.id,
									'street': rec.booking_id.street,
									'type_crm_id': self.env.ref('crm_base.type_phone_call_after_service_care').id,
									'booking_date': rec.booking_id.booking_date,
									'call_date': call_date1
								})
								call_date2 = vals.get('out_date') + timedelta(
									days=int(config.get_param('date_second_vshm'))) if vals.get(
									'out_date') else datetime.now() + timedelta(
									days=int(config.get_param('date_second_vshm')))
								pc2 = self.env['crm.phone.call'].create({
									'name': 'Chăm sóc SDV VSHM lần 2',
									'subject': 'Chăm sóc sau dịch vụ',
									'partner_id': rec.booking_id.partner_id.id,
									'phone': rec.booking_id.partner_id.phone,
									'direction': 'out',
									'company_id': rec.booking_id.company_id.id,
									'crm_id': rec.booking_id.id,
									'country_id': rec.booking_id.country_id.id,
									'street': rec.booking_id.street,
									'type_crm_id': self.env.ref('crm_base.type_phone_call_after_service_care').id,
									'booking_date': rec.booking_id.booking_date,
									'call_date': call_date2
								})
								if pc1 and pc2:
									for crm_line in rec.booking_id.crm_line_ids:
										crm_line.create_phone_call = True
							# check da_khoa
							if crm_line.product_id.service_code_ehc in nhom_da_khoa and not crm_line.create_phone_call:
								call_date1 = vals.get('out_date') + timedelta(
									days=int(config.get_param('date_first_da_khoa_'))) if vals.get(
									'out_date') else datetime.now() + timedelta(
									days=int(config.get_param('date_first_da_khoa')))
								pc1 = self.env['crm.phone.call'].create({
									'name': 'Chăm sóc SDV Đa khoa lần 1',
									'subject': 'Chăm sóc sau dịch vụ',
									'partner_id': rec.booking_id.partner_id.id,
									'phone': rec.booking_id.partner_id.phone,
									'direction': 'out',
									'company_id': rec.booking_id.company_id.id,
									'crm_id': rec.booking_id.id,
									'country_id': rec.booking_id.country_id.id,
									'street': rec.booking_id.street,
									'type_crm_id': self.env.ref('crm_base.type_phone_call_after_service_care').id,
									'booking_date': rec.booking_id.booking_date,
									'call_date': call_date1
								})
								call_date2 = vals.get('out_date') + timedelta(
									days=int(config.get_param('date_second_da_khoa'))) if vals.get(
									'out_date') else datetime.now() + timedelta(
									days=int(config.get_param('date_second_da_khoa')))
								pc2 = self.env['crm.phone.call'].create({
									'name': 'Chăm sóc SDV Đa khoa lần 2',
									'subject': 'Chăm sóc sau dịch vụ',
									'partner_id': rec.booking_id.partner_id.id,
									'phone': rec.booking_id.partner_id.phone,
									'direction': 'out',
									'company_id': rec.booking_id.company_id.id,
									'crm_id': rec.booking_id.id,
									'country_id': rec.booking_id.country_id.id,
									'street': rec.booking_id.street,
									'type_crm_id': self.env.ref('crm_base.type_phone_call_after_service_care').id,
									'booking_date': rec.booking_id.booking_date,
									'call_date': call_date2
								})
								if pc1 and pc2:
									for crm_line in rec.booking_id.crm_line_ids:
										crm_line.create_phone_call = True
				else:
					rec.booking_id.stage_id = self.env.ref('crm_base.crm_stage_out_sold').id
					rec.booking_id.effect = 'expire'
		return res


class InheritCrmLead(models.Model):
	_inherit = 'crm.lead'

	crm_hh_ehc_medical_record_ids = fields.One2many('crm.hh.ehc.medical.record', 'booking_id', string='Medical record')


class MedicalRecordLineEHC(models.Model):
	_name = 'crm.hh.ehc.medical.record.line'
	_description = 'Medical record line EHC'

	crm_hh_ehc_medical_record_line_id = fields.Many2one('crm.hh.ehc.medical.record', string='Bệnh án tổng')
	room_id = fields.Many2one('crm.hh.ehc.department', string='Phòng')
	key_data = fields.Integer('ID bệnh án EHC')

	screening_information = fields.Char('Thông tin sàng lọc')
	reason_for_examination = fields.Char('Lý do khám')
	pathological_process = fields.Char('Quá trình bệnh lý')
	personal_history = fields.Char('Tiền sử bản thân')
	diagnose = fields.Char('Chẩn đoán')
	processing_time = fields.Char('Thời gian xử trí')
	treatment_form = fields.Char('Hình thức xử trí')
	desc_doctor = fields.Text(string='Lời dặn của bác sĩ')
	result = fields.Text(string='Kết quả')
