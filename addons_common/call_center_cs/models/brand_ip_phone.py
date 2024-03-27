from odoo import api, fields, models


class BrandIPPhone(models.Model):
    _name = 'brand.ip.phone'
    _description = 'Lưu trữ IP của các thương hiệu'

    user_id = fields.Many2one('res.users', 'Người dùng')
    ip_phone = fields.Char('IP phone')
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')

    def write(self, vals):
        res = super(BrandIPPhone, self).write(vals)
        if res:
            if 'ip_phone' in vals:
                cs_voice_token = self.env['api.access.token.cs'].sudo().search([('user_id', '=', self.user_id.id)])
                cs_voice_token.sudo().unlink()
        return res

