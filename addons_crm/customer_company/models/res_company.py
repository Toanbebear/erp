from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    script_sms_id = fields.One2many('script.sms', 'company_id')
    location_shop = fields.Char('Địa chỉ gửi SMS')
    map_shop = fields.Char('Bản đồ đi đường')


class ScriptSMS(models.Model):
    _name = 'script.sms'
    _description = "Script SMS"

    type = fields.Selection([('XNLH', 'Xác nhận lịch hẹn'), ('NHKHL1', 'Nhắc hẹn KH lần 1'),
                             ('NHKHL2', 'Nhắc hẹn KH lần 2'), ('COKHLDV', 'Cảm ơn KH làm DV'),
                             ('SDVKNM', 'SDV không nghe máy'),
                             ('CMSN', 'SMS chúc mừng sinh nhật KH'), ('CTKH', 'SMS chúc tết KH')],
                            string='Tên SMS')
    time_send = fields.Char('Thời gian gửi')
    content = fields.Text('Nội dung')
    company_id = fields.Many2one('res.company', string='Công ty')
    note = fields.Text('Ghi chú')
    run = fields.Boolean('Hoạt động', default=False)
