import json
import logging
from datetime import datetime, timedelta

import requests

from odoo import api, tools
from odoo import models, fields

_logger = logging.getLogger(__name__)


class InheritSHealthReExam(models.Model):
    _inherit = 'sh.medical.reexam'

    def action_confirm_reexam(self):
        # Ngày [Date_Recheck], quý khách có lịch hẹn tái khám tại Nha khoa Paris -[Company], [Location_Shop]. Xin cảm ơn!
        res = super(InheritSHealthReExam, self).action_confirm_reexam()
        for rec in self:
            content_company = None
            content = None
            if rec.company:
                for item_sms_script in rec.company.script_sms_id:
                    if item_sms_script.type == 'NLTK' and item_sms_script.run:
                        content = content_company = item_sms_script.content
            if content:
                for item in rec.days_reexam:
                    # check sinh sms tái khám
                    if item.name_phone and item.type in ['ReCheck4', 'ReCheck5', 'ReCheck6', 'ReCheck7', 'ReCheck8']:
                        content = content.replace('[Date_Recheck]', item.date_recheck_print.strftime('%d/%m/%Y'))
                        content = content.replace('[Company]', rec.company.name)
                        content = content.replace('[Location_Shop]', rec.company.location_shop)
                        self.env['crm.sms'].sudo().create({
                            'name': item.name_phone + ' - %s' % rec.walkin.booking_id.name,
                            'contact_name': rec.walkin.booking_id.contact_name,
                            'partner_id': rec.walkin.booking_id.partner_id.id,
                            'phone': rec.walkin.booking_id.phone,
                            'company_id': rec.company.id,
                            'company2_id': [(6, 0, rec.walkin.booking_id.company2_id.ids)],
                            'crm_id': rec.walkin.booking_id.id,
                            'send_date': item.date_recheck_print - timedelta(days=1),
                            'desc': content,
                            'id_reexam': item.id
                        })
                        content = content_company
        return res


class InheritScriptSMS(models.Model):
    _inherit = 'script.sms'

    type = fields.Selection(selection_add=[('NLTK', 'Nhắc lịch tái khám')])
