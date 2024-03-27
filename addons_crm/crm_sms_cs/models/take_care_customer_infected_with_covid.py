import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import api, tools
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ScriptSMS(models.Model):
    _inherit = 'script.sms'

    type = fields.Selection(selection_add=[('CSKHDTCOVID', 'Chăm sóc khách hàng mắc Covid')])


class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    def write(self, vals):
        res = super(InheritCrmLead, self).write(vals)
        if self.tested_positive_date:
            try:
                # sinh sms
                config = self.env['ir.config_parameter'].sudo()
                # get link chăm sóc sức khỏe khách hàng mắc covid
                if self.brand_id:
                    brand_code = self.brand_id.code.lower()
                    key_link_manual = 'sms_survey_link_cancel_%s' % brand_code
                    link_manual = config.get_param(key_link_manual)
                script_sms = self.company_id.script_sms_id
                content_sms = ''
                if vals.get('people_infected_with_covid') and vals.get(
                        'tested_positive_date') and self.id and link_manual and script_sms:
                    for item in script_sms:
                        if item.run:
                            if item.type == 'CSKHDTCOVID':
                                content_sms = item.content.replace('[LINK]', link_manual)
                                break
                    if content_sms:
                        # set ngày gửi SMS: 9h ngày hôm sau (sau ngày KH cancel bk)
                        send_date = datetime.now()
                        tested_positive_date = self.tested_positive_date + timedelta(days=3, hours=2)
                        send_date = send_date.replace(day=tested_positive_date.day, month=tested_positive_date.month,
                                                      year=tested_positive_date.year, hour=9, minute=0, second=0)

                        sms = self.env['crm.sms'].sudo().create({
                            'name': "SMS Chăm sóc Khách hàng dương tính với Covid",
                            'partner_id': self.partner_id.id,
                            'contact_name': self.partner_id.name,
                            'phone': self.phone,
                            'company_id': self.company_id.id,
                            'company2_id': [(6, 0, self.company2_id.ids)] if self.id else None,
                            'crm_id': self.id if self.id else None,
                            'send_date': send_date,
                            'desc': content_sms,
                        })

                # sinh pc sau 1 ngày dương tính covid
                call_date = datetime.now()
                tested_positive_date = self.tested_positive_date + timedelta(days=1, hours=9)
                call_date = call_date.replace(day=tested_positive_date.day, month=tested_positive_date.month,
                                              year=tested_positive_date.year, hour=9, minute=0, second=0)
                self.create_phone_call_covid(date=call_date)

                # sinh pc sau 7 ngày dương tính covid
                tested_positive_date = self.tested_positive_date + timedelta(days=7, hours=9)
                call_date = call_date.replace(day=tested_positive_date.day, month=tested_positive_date.month,
                                              year=tested_positive_date.year, hour=9, minute=0, second=0)
                self.create_phone_call_covid(date=call_date)
            except Exception as e:
                _logger.info('============================= error ======================')
                _logger.info(e)
                pass
        return res

    def create_phone_call_covid(self, date):
        pc = self.env['crm.phone.call'].sudo().create({
            'name': 'PHONECALL CHĂM SÓC KHÁCH HÀNG DƯƠNG TÍNH COVID - %s' % self.name,
            'subject': 'Chăm sóc khách hàng %s dương tính với COVID' % self.partner_id.name,
            'partner_id': self.partner_id.id,
            'phone': self.phone,
            'direction': 'out',
            'company_id': self.company_id.id,
            'crm_id': self.id,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'street': self.street,
            'type_crm_id': self.env.ref('crm_base.type_phone_call_customer_care_positive_covid').id,
            'call_date': date,
            'care_type': 'DVKH',
        })
        return pc


