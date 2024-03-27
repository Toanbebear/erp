# -*- coding: utf-8

from odoo import fields, models, _
from odoo.exceptions import ValidationError
import requests


class website_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    recaptcha_site_key = fields.Char(related='website_id.recaptcha_site_key', string='reCAPTCHA site Key', store=True, readonly=False)
    recaptcha_private_key = fields.Char(related='website_id.recaptcha_private_key', string='reCAPTCHA Private Key', store=True, readonly=False)

class website(models.Model):
    _inherit = 'website'

    recaptcha_site_key = fields.Char('reCAPTCHA Site Key', default='6LeducgUAAAAAG6X0XFj-dfaSC32_a5yiR3V9lM-', store=True, readonly=False)
    recaptcha_private_key = fields.Char('reCAPTCHA Private Key', default='6LeducgUAAAAAKrBJZ7y7jzmcbXwzZ-DYtcGUSFz', store=True, readonly=False)

    def is_captcha_valid(self, response):
        for website in self:
            get_res = {'secret': website.recaptcha_private_key,
                       'response': response}
            try:
                response = requests.get('https://www.google.com/recaptcha/api/siteverify', params=get_res)
            except Exception:
                raise ValidationError(_('Invalid Data!.'))
            res_con = response.json()
            if res_con.get('success'):
                return True
        return False
