# -*- coding: utf-8 -*-

import logging

from werkzeug import urls

from odoo import fields, models, api
import uuid

_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = 'hr.employee'

    def _get_default_token(self):
        return str(uuid.uuid4())

    name_relative = fields.Char(string='Họ và tên người thân')
    relationship = fields.Selection([('father', 'Bố'),
                                     ('mother', 'Mẹ'),
                                     ('son', 'Con trai'),
                                     ('wife', 'Vợ'),
                                     ('daughter', 'Con gái'),
                                     ('husband', 'Chồng'),
                                     ('other', 'Khác')], string='Quan hệ với nhân viên')
    hr_source_id = fields.Many2one('utm.source', string='Nguồn tuyển dụng')
    social_insurance = fields.Char(string='Số sổ BHXH')
    personal_income_tax = fields.Char(string='Mã số thuế cá nhân')
    token = fields.Char('Access Token', default=lambda self: self._get_default_token(), copy=False)

    def update_information(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Update information",
            'target': 'new',
            'url': '/welcome-employee/%s' % self.token
        }

    employee_qr = fields.Binary(string="QR code", compute='generate_qr_information')
    employee_url = fields.Char(string="Information employee URL", compute='generate_qr_information')

    @api.depends('employee_code')
    def generate_qr_information(self):
        for record in self:
            record.employee_qr = False
            base_url = '/' if self.env.context.get('relative_url') else \
                self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if type(record.id) is int:
                employee_url = urls.url_join \
                    (base_url, "welcome-employee/%s" % record.token)
                record.employee_url = employee_url
            else:
                employee_url = ''
            if employee_url:
                record.employee_qr = self.qrcode(employee_url)
