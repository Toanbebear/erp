from odoo import models, fields

TYPE = [('XNLH', 'Xác nhận lịch hẹn'), ('NHKHL1', 'Nhắc hẹn KH lần 1'),
        ('NHKHL2', 'Nhắc hẹn KH lần 2'), ('COKHLDV', 'Cảm ơn KH làm DV'),
        ('SDVKNM', 'SDV không nghe máy'),
        ('CMSN', 'SMS chúc mừng sinh nhật KH'), ('CTKH', 'SMS chúc tết KH'), ('CI', 'Check in')]


class ScriptSMS(models.Model):
    _name = 'script.sms'
    _description = "Script SMS"

    type = fields.Selection(TYPE, string='Tên SMS')
    time_send = fields.Char('Thời gian gửi')
    content = fields.Text('Nội dung')
    company_id = fields.Many2one('res.company', string='Công ty')
    note = fields.Text('Ghi chú')
    run = fields.Boolean('Hoạt động', default=False)


