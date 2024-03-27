from odoo import fields, models, api


class CrmLeadInherit(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead', 'qrcode.mixin']

    qr_id = fields.Binary(string="QR ID", compute='_generate_qr_code')
    hotline_brand = fields.Char(string='Hotline liên hệ:', compute="_compute_phone")
    qr_code_id = fields.Binary(string="QR Code", compute='_generate_qr_code_id')

    @api.depends('brand_id')
    def _compute_phone(self):
        if self.brand_id:
            self.hotline_brand = self.brand_id.phone

    def _generate_qr_code(self):
        for item in self:
            base_url = '%s/web#id=%d&action=631&view_type=form&model=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                item.id,
                item._name)
            item.qr_id = self.qrcode(base_url)

    def _generate_qr_code_id(self):
        for item in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/web#id=%d&action=634&view_type=form&model=%s' % (item.id, item._name)
            item.qr_code_id = self.qrcode(base_url)


