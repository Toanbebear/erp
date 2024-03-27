# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.exceptions import AccessDenied


class VoiceConfigurator(models.Model):
    _name = 'voice.configurator'
    _description = 'VOICE Configurator'

    @api.model
    def get_voice_config(self):
        if not self.env.user.has_group('base.group_user'):
            raise AccessDenied()

        get_param = self.env['ir.config_parameter'].sudo().get_param

        return {
            'pbx_ip': get_param('voip.pbx_ip', default='localhost'),
            'wsServer': get_param('voip.wsServer', default='ws://localhost'),
            'login': "123123",
            'password': "123123",
            'debug': self.user_has_groups('base.group_no_one'),
            'external_phone': "101001",
            'always_transfer': True,
            'ignore_incoming': True,
            'mode': get_param('voip.mode', default="prod"),
        }
