from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import ast

reason_selection = [('1', 'Đóng trùng KH liệu trình chỉnh nha'), ('2', 'Đóng trùng KH răng sứ'),
                    ('3', 'Đóng trùng KH cắm implant'), ('4', 'Đóng trùng KH gói vệ sinh chăm sóc răng miệng')]

reason_dict = {key: value for key, value in reason_selection}


class BookingGuarantee(models.TransientModel):
    _name = 'close.phone.call.duplicate'
    _description = 'Đóng trùng phone call'

    reason = fields.Selection(reason_selection, string='Lý do đóng trùng')
    phone_call_ids = fields.Char('Phone_call_ids')

    def popup_close_phone_call_duplicate(self):
        if self.reason:
            # view send message
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})

            # Xử lý đóng trùng
            paris_brand = self.env.ref('sci_brand.res_brand_paris').id
            phone_call_ids = self.env['crm.phone.call'].sudo().browse(ast.literal_eval(self.phone_call_ids))
            check_paris_brand = phone_call_ids.filtered(lambda p: p.company_id.brand_id.id != paris_brand)
            if len(check_paris_brand) > 0:
                raise ValidationError('Công ty của phone call không thuộc thương hiệu París')

            phone_call_ids.write({
                'note': reason_dict[self.reason]
            })

            phone_call_ids.action_close_phone_call_duplicate()
            context['message'] = 'Đóng trùng phone call thành công!!'
            return {
                'name': 'Thông báo thành công',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }
