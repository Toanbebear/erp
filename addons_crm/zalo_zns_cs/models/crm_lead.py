import json
import logging
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta

from odoo import models

_logger = logging.getLogger(__name__)


class CRM(models.Model):
    _inherit = 'crm.lead'

    def create_phone_call(self, user=None):
        res = super(CRM, self).create_phone_call(user=None)
        time = datetime.now()
        tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
        tz_database = pytz.timezone('UTC')
        time = tz_database.localize(time)
        time = time.astimezone(tz_current)
        time = time.date()
        if self.ticket_id:
            script_sms = self.company_id.script_sms_id
            for item in script_sms:
                if item.run and item.type == 'XNLH' and item.has_zns and item.zns_template_id:
                    content_zns = {
                        'template_id': item.zns_template_id,  # 7155
                        'params': {
                            "ma_booking": self.name,
                            "customer_name": self.contact_name,
                            "booking_date": self.booking_date.strftime('%d/%m/%Y')
                        }
                    }
                    zns = {
                        'name': 'Xác nhận lịch hẹn - %s' % self.name,
                        'contact_name': self.contact_name,
                        'partner_id': self.partner_id.id,
                        'phone': self.phone,
                        'company_id': self.company_id.id,
                        'company2_id': [(6, 0, self.company2_id.ids)],
                        'crm_id': self.id,
                        'send_date': self.booking_date.replace(hour=2, minute=0, second=0) - relativedelta(days=1),
                        'desc': json.dumps(content_zns),
                        'type': 'zns',
                    }
                    self.env['crm.sms'].create(zns)
        else:
            if self.booking_date.date() > time:
                script_sms = self.company_id.script_sms_id
                for item in script_sms:
                    if item.run and item.type == 'XNLH' and item.has_zns and item.zns_template_id:
                        content_zns = {
                            'template_id': item.zns_template_id,  # 7155
                            'params': {
                                "ma_booking": self.name,
                                "customer_name": self.contact_name,
                                "booking_date": self.booking_date.strftime('%d/%m/%Y')
                            }
                        }
                        zns = {
                            'name': 'Xác nhận lịch hẹn - %s' % self.name,
                            'contact_name': self.contact_name,
                            'partner_id': self.partner_id.id,
                            'phone': self.phone,
                            'company_id': self.company_id.id,
                            'company2_id': [(6, 0, self.company2_id.ids)],
                            'crm_id': self.id,
                            'send_date': self.booking_date.replace(hour=2, minute=0, second=0) - relativedelta(days=1),
                            'desc': json.dumps(content_zns),
                            'type': 'zns',
                        }
                        self.env['crm.sms'].create(zns)
        return res
