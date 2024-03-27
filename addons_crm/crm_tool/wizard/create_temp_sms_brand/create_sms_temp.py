from odoo.addons.custom_partner.models.script_sms import TYPE

from odoo import models, fields


class CreateSMSTemp(models.TransientModel):
    _name = 'create.sms.temp'
    _description = 'Create sms temp'

    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    type = fields.Selection(TYPE, string='Tên SMS')
    time_send = fields.Char('Thời gian gửi')
    content = fields.Text('Nội dung')
    note = fields.Text('Ghi chú')
    run = fields.Boolean('Hoạt động', default=True)

    def create_temp_sms(self):
        company_ids = self.env['res.company'].search([('brand_id', '=', self.brand_id.id)])
        if company_ids:
            for company_id in company_ids:
                sms = self.env['script.sms'].create({
                    'type': self.type,
                    'time_send': self.time_send,
                    'content': self.content,
                    'company_id': company_id.id,
                    'note': self.note,
                    'run': self.run,
                })
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = 'Đã tạo xong mẫu sms cho các công ty thuộc thương hiệu %s' % self.brand_id.name
            return {
                'name': 'THÔNG BÁO THÀNH CÔNG',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }
