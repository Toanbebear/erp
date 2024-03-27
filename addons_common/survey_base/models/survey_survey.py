# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
phone_number_validator = re.compile("^[0-9/]*$")
_logger = logging.getLogger(__name__)


class Survey(models.Model):
    _inherit = 'survey.survey'

    company_id = fields.Many2one('res.company', string='Công ty')
    brand_logo = fields.Binary('Logo thương hiệu', required=True)
    qr = fields.Binary(string="QR Code", compute='generate_qr', store=True)

    # crm_lead = fields.One2many('crm.lead', 'survey_id', string='CRM Lead')

    @api.depends('public_url')
    def generate_qr(self):
        for record in self:
            if qrcode and base64 and record.public_url:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.public_url)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                record.qr = qr_image

    def print_qr(self):
        return self.env.ref('survey_base.print_qr').report_action(self, data={'data': self.id})

    def unlink(self):
        for record in self:
            if self.env['survey.user_input'].search([('survey_id', '=', record.id)], limit=1):
                raise UserError(_('You can not delete this survey. Survey already have answers!'))
        return super(Survey, self).unlink()

    def _create_answer_crm_lead(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True,
                                booking=False, **additional_vals):
        """ Main entry point to get a token back or create a new one. This method
        does check for current user access in order to explicitely validate
        security.
          :param user: target user asking for a token; it might be void or a
                       public user in which case an email is welcomed;
          :param email: email of the person asking the token is no user exists;
        """
        self.check_access_rights('read')
        self.check_access_rule('read')
        answers = self.env['survey.user_input']
        for survey in self:
            if partner and not user and partner.user_ids:
                user = partner.user_ids[0]

            invite_token = additional_vals.pop('invite_token', False)
            survey._check_answer_creation(user, partner, email, test_entry=test_entry, check_attempts=check_attempts,
                                          invite_token=invite_token)

            answer_vals = {
                'survey_id': survey.id,
                'test_entry': test_entry,
                'question_ids': [(6, 0, survey._prepare_answer_questions().ids)]
            }
            if booking:
                crm_lead = self.env['crm.lead'].search([('id', '=', booking)])
                answer_vals['crm_lead'] = [(4, crm_lead.id)]
            if user and not user._is_public():
                answer_vals['partner_id'] = user.partner_id.id
                answer_vals['email'] = user.email
            elif partner:
                answer_vals['partner_id'] = partner.id
                answer_vals['email'] = partner.email
            else:
                answer_vals['email'] = email

            if invite_token:
                answer_vals['invite_token'] = invite_token
            elif survey.is_attempts_limited and survey.access_mode != 'public':
                answer_vals['invite_token'] = self.env['survey.user_input']._generate_invite_token()
            answer_vals.update(additional_vals)
            answers += answers.create(answer_vals)

        return answers
