import datetime
from odoo.exceptions import ValidationError
from odoo import models, fields, api


class DoctorSchedule(models.Model):
    _name = "doctor.schedule"
    _description = "Lịch nghỉ của bác sĩ"
    _rec_name = "physician"
    _order = "start_datetime"

    physician = fields.Many2one('sh.medical.physician', string='Bác sĩ/trợ thủ', required=True)
    company = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.company, domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    start_datetime = fields.Datetime('Ngày bắt đầu', default=datetime.datetime.now())
    end_datetime = fields.Datetime('Ngày kết thúc')
    
    def unlink(self):
        if self.start_datetime <= datetime.datetime.now():
            raise ValidationError('Bạn không thể xóa lịch trực này vào thời điểm hiện tại')
        return super(DoctorSchedule, self).unlink()

    @api.constrains('start_datetime', 'end_datetime')
    def validate_datetime(self):
        for record in self:
            if record.start_datetime and record.end_datetime and record.start_datetime > record.end_datetime:
                raise ValidationError('Ngày kết thúc không thể lớn hơn ngày bắt đầu.')