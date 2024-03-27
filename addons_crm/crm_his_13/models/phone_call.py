from odoo import fields, api, models


class PhoneCall(models.Model):
    _inherit = 'crm.phone.call'

    NOTE = [
        ('Check', 'Chăm sóc lần 1'),
        ('Check1', 'Chăm sóc lần 2'),
        ('Check2', 'Chăm sóc lần 3'),
        ('Check3', 'Chăm sóc lần 4'),
        ('Check8', 'Chăm sóc lần 5'),
        ('Check4', 'Chăm sóc kết thúc liệu trình lần 1'),
        ('Check5', 'Chăm sóc kết thúc liệu trình lần 2'),
        ('Check6', 'Chăm sóc kết thúc liệu trình lần 3'),
        ('Check7', 'Chăm sóc kết thúc liệu trình lần 4'),
        ('Check8', 'Chăm sóc kết thúc liệu trình lần 5'),
        ('Change', 'Thay băng lần 1'),
        ('Change1', 'Thay băng lần 2'),
        ('Change2', 'Thay băng lần 3'),
        ('Change3', 'Thay băng lần 4'),
        ('Change4', 'Thay băng lần 5'),
        ('Change5', 'Thay băng lần 6'),
        ('ReCheck', 'Cắt chỉ'),
        ('ReCheck1', 'Hút dịch'),
        ('ReCheck2', 'Rút ống mũi'),
        ('ReCheck3', 'Thay nẹp mũi'),
        ('ReCheck4', 'Tái khám lần 1'),
        ('ReCheck5', 'Tái khám lần 2'),
        ('ReCheck6', 'Tái khám lần 3'),
        ('ReCheck7', 'Tái khám lần 4'),
        ('ReCheck8', 'Tái khám lần 5'),
        ('ReCheck11', 'Tái khám lần 6'),
        ('ReCheck9', 'Tái khám định kì'),
        ('ReCheck10', 'Nhắc liệu trình'),
        ('Return', 'Tái khai thác KH cũ'),
        ('Sale1', 'Chăm sóc bán lần 1'),
        ('Sale2', 'Chăm sóc bán lần 2'),
        ('Potential', 'Khai thác dịch vụ tiềm năng')
    ]

    date_re_exam = fields.Datetime("Date re exam")
    date_warranty = fields.Datetime("Ngày bảo hành")
    desc_doctor = fields.Char('Desc doctor')
    date_out_location = fields.Datetime('Date out')
    date = fields.Datetime('Ngày làm dịch vụ')
    medical_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    service_id = fields.Many2many('sh.medical.health.center.service',
                                  'sh_medical_health_center_service_crm_phone_call_rel',
                                  'service_id', 'phone_call_id', string='DV trên phiếu khám',
                                  compute='get_service_walkin')
    type_pc = fields.Selection(NOTE, 'Loại')
    physician = fields.Many2one('sh.medical.physician', string='Bác sĩ/Trợ thủ')

    @api.depends('medical_id')
    def get_service_walkin(self):
        for rec in self:
            rec.service_id = [(6, 0, rec.medical_id.service.ids)]
