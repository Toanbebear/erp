import json
import logging
from datetime import timedelta, datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class CRMLoyaltyRank(models.Model):
    _inherit = 'crm.loyalty.rank'

    gift_zns = fields.Text('Quà ZNS')


class CRMLoyaltyCard(models.Model):
    _inherit = 'crm.loyalty.card'

    def cron_send_zns_cmsn_pr(self):
        now = datetime.now().date()
        brand = self.env['res.brand'].search([('code', '=', 'PR')], limit=1)
        query = ''' SELECT clc.id FROM crm_loyalty_card clc 
        where 
        clc.partner_id in (select id  from res_partner rp where EXTRACT(month FROM rp.birth_date) = %s and EXTRACT(day FROM rp.birth_date) = %s) 
        and brand_id = %s and company_id is not NULL
        ''' % (now.month, now.day, brand.id)
        self.env.cr.execute(query)
        loyalty_ids = self.env.cr.fetchall()
        datas = []
        for rec in loyalty_ids:
            loyalty = self.env['crm.loyalty.card'].browse(int(rec[0]))
            script_sms = loyalty.company_id.script_sms_id
            template_id = 0
            for item in script_sms:
                if item.run and item.type == 'CMSN' and item.has_zns and item.zns_template_id:
                    template_id = item.zns_template_id
                    break
            if template_id != 0:
                if loyalty.rank_id:
                    content_zns = {
                        'template_id': template_id,
                        'params': {
                            "customer_name": loyalty.partner_id.name,
                            "ma_khach_hang": loyalty.partner_id.code_customer,
                            "qua_hang_the": loyalty.rank_id.gift_zns
                        }
                    }
                    data = {
                        'name': 'Paris - Chúc mừng sinh nhật',
                        'contact_name': loyalty.partner_id.name,
                        'partner_id': loyalty.partner_id.id,
                        'phone': loyalty.partner_id.phone,
                        'company_id': loyalty.company_id.id,
                        'company2_id': False,
                        'crm_id': False,
                        'send_date': datetime.now().replace(hour=2, minute=0, second=0),
                        'desc': json.dumps(content_zns),
                        'id_reexam': False,
                        'type': 'zns',
                    }
                    self.env['crm.sms'].with_user(1).create(data)
                    # datas.append(data)
                else:
                    content_zns = {
                        'template_id': template_id,
                        'params': {
                            "customer_name": loyalty.partner_id.name,
                            "ma_khach_hang": loyalty.partner_id.code_customer,
                            "qua_hang_the": self.env.ref('zalo_zns_cs.crm_loyalty_rank_normal_paris').gift_zns
                        }
                    }
                    data = {
                        'name': 'Paris - Chúc mừng sinh nhật',
                        'contact_name': loyalty.partner_id.name,
                        'partner_id': loyalty.partner_id.id,
                        'phone': loyalty.partner_id.phone,
                        'company_id': loyalty.company_id.id,
                        'company2_id': False,
                        'crm_id': False,
                        'send_date': datetime.now().replace(hour=2, minute=0, second=0),
                        'desc': json.dumps(content_zns),
                        'id_reexam': False,
                        'type': 'zns',
                    }
                    self.env['crm.sms'].with_user(1).create(data)
                    # datas.append(data)
                # if datas:
                #     self.env['crm.sms'].with_user(1).create(datas)
