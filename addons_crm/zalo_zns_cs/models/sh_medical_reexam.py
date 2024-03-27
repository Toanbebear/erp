import json
import logging
from datetime import timedelta

from odoo import models

_logger = logging.getLogger(__name__)


class SHealthReExam(models.Model):
    _inherit = 'sh.medical.reexam'

    def action_confirm_reexam(self):
        res = super(SHealthReExam, self).action_confirm_reexam()
        script_sms = self.company.script_sms_id
        for item in script_sms:
            if item.run and item.type == 'COKHLDV' and item.has_zns and item.zns_template_id:
                if self.company.brand_id == 'KN':
                    content_zns = {
                        'template_id': item.zns_template_id,  # 7158
                        'params': {
                            # "ma_booking": self.walkin.booking_id.name,
                            # Cấu hình trong template là ma_kh
                            "ma_kh": self.walkin.booking_id.name,
                            "customer_name": self.walkin.booking_id.contact_name,
                            "booking_date": self.walkin.booking_id.booking_date.strftime('%d/%m/%Y')
                        }
                    }
                else:
                    content_zns = {
                        'template_id': item.zns_template_id,  # 307064
                        'params': {
                            "customer_name": self.walkin.booking_id.contact_name,
                            "ten_dich_vu": ','.join(self.services.mapped('name')),
                            "reg_date": self.date.strftime('%d/%m/%Y'),
                            "ma_booking": self.walkin.booking_id.name,
                        }
                    }

                zns = {
                    'name': 'Cảm ơn Khách hàng làm dịch vụ',
                    'contact_name': self.walkin.booking_id.contact_name,
                    'partner_id': self.walkin.booking_id.partner_id.id,
                    'phone': self.walkin.booking_id.phone,
                    'company_id': self.company.id,
                    'company2_id': [(6, 0, self.walkin.booking_id.company2_id.ids)],
                    'crm_id': self.walkin.booking_id.id,
                    'send_date': (self.date_out + timedelta(days=1)).replace(hour=2, minute=0, second=0),
                    'desc': json.dumps(content_zns),
                    'id_reexam': self.id,
                    'type': 'zns',
                }
                self.env['crm.sms'].create(zns)
        return res
