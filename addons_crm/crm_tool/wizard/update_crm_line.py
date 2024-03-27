from odoo import models, fields


class UpdateCrmLine(models.TransientModel):
    _name = "update.crm.line"
    _description = 'Cập nhật Line dịch vụ'

    line = fields.Many2one('crm.line', string='Dịch vụ')
    action = fields.Selection([('1', 'Cập nhật đơn giá')], string='Loại hành động', default='1')
    unit_price = fields.Float('Đơn giá')

    def confirm(self):
        if self.action == '1':
            self.line.unit_price = self.unit_price
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = 'Giá đã được cập nhật thành công!!'
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
