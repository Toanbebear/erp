from odoo import fields, models


class InheritPartnerQRcode(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'qrcode.mixin']

    qr_id = fields.Binary(string="QR ID", compute='_generate_qr_code')

    def _generate_qr_code(self):
        for item in self:
            base_url = '%s/web#id=%d&action=554&view_type=form&model=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                item.id,
                item._name)
            item.qr_id = self.qrcode(base_url)
