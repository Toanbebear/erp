from odoo import api, fields, models


class SurveySendMailSms(models.Model):
    _name = 'survey.send.mail.sms'
    _description = 'Cấu hình gửi mail phản ánh/góp ý cho Quản lý'

    employee_id = fields.Many2one('hr.employee', 'Nhân viên')
    company_ids = fields.Many2many('res.company', string='Chi nhánh')
    phone = fields.Char('Số điện thoại')