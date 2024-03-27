from odoo import fields, models


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'qrcode.mixin']

    qr_customer_code = fields.Binary(string="QR Customer Code", compute='_generate_qr_customer_code')

    def _generate_qr_customer_code(self):
        for item in self:
            qr_url = '%s/khach-hang/%s' % (self.env['ir.config_parameter'].sudo().get_param('qr_url'), item.id)
            item.qr_customer_code = self.qrcode(qr_url)
