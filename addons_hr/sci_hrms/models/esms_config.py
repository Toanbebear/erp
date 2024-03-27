# -*- coding: utf-8

from odoo import api, fields, models

class esms_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    esms_api_key = fields.Char(string='Api Key', default='EBBFE4FAB83DAB680B5D8E89B5A2F5')
    esms_secret_key = fields.Char(string='Secret Key', default='A7EC27C47EED25904F446DC7A9FF71')
    esms_url = fields.Char(string='URL', default='http://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_get')
    esms_brand_name = fields.Char(string='Brand Name', default='Baotrixemay')

    @api.model
    def get_values(self):
        res = super(esms_config_settings, self).get_values()

        res['esms_api_key'] = self.env['ir.config_parameter'].sudo().get_param('esms.esms_api_key', default='EBBFE4FAB83DAB680B5D8E89B5A2F5')
        res['esms_secret_key'] = self.env['ir.config_parameter'].sudo().get_param('esms.esms_secret_key', default='A7EC27C47EED25904F446DC7A9FF71')
        res['esms_url'] = self.env['ir.config_parameter'].sudo().get_param('esms.esms_url', default='http://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_get')
        res['esms_brand_name'] = self.env['ir.config_parameter'].sudo().get_param('esms.esms_brand_name', default='Baotrixemay')

        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('esms.esms_api_key', self.esms_api_key)
        self.env['ir.config_parameter'].sudo().set_param('esms.esms_secret_key', self.esms_secret_key)
        self.env['ir.config_parameter'].sudo().set_param('esms.esms_url', self.esms_url)
        self.env['ir.config_parameter'].sudo().set_param('esms.esms_brand_name', self.esms_brand_name)

        super(esms_config_settings, self).set_values()