# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vnpay_qrcode_active = fields.Boolean("Sử dụng cổng thanh toán VNPAY-QR", implied_group='sale.group_auto_done_setting', readonly=False)
    vnpay_qrcode_url_create_qr = fields.Char("URL Create QR", implied_group='sale.group_auto_done_setting')

    # vnpay_qrcode_app_id = fields.Char("App ID", implied_group='sale.group_auto_done_setting')
    # vnpay_qrcode_secret_key = fields.Char("Secret Key", implied_group='sale.group_auto_done_setting')
    # vnpay_qrcode_merchant_name = fields.Char("Merchant Name", implied_group='sale.group_auto_done_setting')
    # vnpay_qrcode_qr_tool_url = fields.Char("Url QR Tool", implied_group='sale.group_auto_done_setting')
    vnpay_qrcode_check_trans_url = fields.Char("Url Check Trans", implied_group='sale.group_auto_done_setting')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res.update(
            vnpay_qrcode_active=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_active'),
            vnpay_qrcode_url_create_qr=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_url_create_qr'),
            # vnpay_qrcode_app_id=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_app_id'),
            # vnpay_qrcode_secret_key=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_secret_key'),
            # vnpay_qrcode_merchant_name=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_merchant_name'),
            # vnpay_qrcode_qr_tool_url=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_qr_tool_url'),
            vnpay_qrcode_check_trans_url=self.env['ir.config_parameter'].sudo().get_param('payment_vnpay.vnpay_qrcode_check_trans_url')
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_active', self.vnpay_qrcode_active)
        self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_url_create_qr', self.vnpay_qrcode_url_create_qr)
        # self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_app_id', self.vnpay_qrcode_app_id)
        # self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_secret_key', self.vnpay_qrcode_secret_key)
        # self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_merchant_name', self.vnpay_qrcode_merchant_name)
        # self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_qr_tool_url', self.vnpay_qrcode_qr_tool_url)
        self.env['ir.config_parameter'].set_param('payment_vnpay.vnpay_qrcode_check_trans_url', self.vnpay_qrcode_check_trans_url)
        return res
