from odoo import fields, models, api
import logging
import psycopg2

_logger = logging.getLogger(__name__)


class PatientEHC(models.Model):
	_name = "crm.hh.ehc.patient"
	_description = 'Patient EHC'

	name = fields.Char('Tên bệnh nhân')
	partner_id = fields.Many2one('res.partner', 'Partner')
	phone = fields.Char('SĐT EHC')
	patient_code = fields.Char('Mã bệnh nhân')

	@api.model
	def fields_get(self, allfields=None, attributes=None):
		fields = super(PatientEHC, self).fields_get(allfields, attributes=attributes)

		# Xử lý không cho xuất số điện thoại
		for field_name in fields:
			if field_name in ['phone']:
				fields[field_name]['exportable'] = False

		return fields

	def cron_get_patient_code(self):
		config = self.env['ir.config_parameter'].sudo()
		id_index = int(config.get_param('id_index_get_patient_code'))
		conn = psycopg2.connect(host="118.70.128.33", database="bvhongha", user="postgres", password="bvhh@123", port="5432")
		cur = conn.cursor()
		query = """ select patientcode,patientphone, patientname, patientid from tb_patientrecord tp where tp.patientphone is not null and tp.patientphone <> '' and tp.patientid > %s order by patientid asc limit 1000""" % id_index
		cur.execute(query)
		conn.commit()
		result = cur.fetchall()
		_logger.info('====================================================')
		_logger.info('result: %s' % len(result))
		i = 1
		id_index_new = 0
		for rec in result:
			patient_code = rec[0]
			patient_phone = rec[1]
			patient_name = rec[2]
			id_index_new = int(rec[3])
			patient = self.env['crm.hh.ehc.patient'].sudo().search([('patient_code', '=', patient_code)], limit=1)
			if patient_phone.isdigit():
				_logger.info('stt: %s' % i)
				i += 1
				if len(patient_phone) > 10:
					count = len(patient_phone) - 10
					phone = patient_phone[count:]
				else:
					phone = patient_phone
				_logger.info('phone: %s' % phone)
				if patient:
					partner = self.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
					if partner:
						patient.write({
							'name': patient_name,
							'patient_code': patient_code,
							'partner_id': partner.id,
							'phone': patient_phone,
						})
					else:
						partner = self.env['res.partner'].sudo().create({
							'name': patient_name,
							'phone': phone,
						})
						patient.write({
							'name': patient_name,
							'patient_code': patient_code,
							'partner_id': partner.id,
							'phone': patient_phone,
						})
				else:
					partner = self.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
					if partner:
						self.env['crm.hh.ehc.patient'].sudo().create({
							'name': patient_name,
							'patient_code': patient_code,
							'partner_id': partner.id,
							'phone': patient_phone,
						})
					else:
						partner = self.env['res.partner'].sudo().create({
							'name': patient_name,
							'phone': phone,
						})
						self.env['crm.hh.ehc.patient'].sudo().create({
							'name': patient_name,
							'patient_code': patient_code,
							'partner_id': partner.id,
							'phone': patient_phone,
						})
				_logger.info('create patient code done')
		var = config.set_param('id_index_get_patient_code', id_index_new)
		_logger.info('================== done ==============================')