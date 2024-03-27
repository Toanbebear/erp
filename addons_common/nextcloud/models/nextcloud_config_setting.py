from odoo import api, models, fields


class NextcloudConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    nextcloud_username = fields.Char(string='Tài khoản', readonly=False,
        help='Tài khoản',config_parameter='nextcloud.nextcloud_username')
    nextcloud_password = fields.Char(string='Mật khẩu', readonly=False,
        help='Mật khẩu',config_parameter='nextcloud.nextcloud_password')
