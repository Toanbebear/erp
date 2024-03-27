import json
import logging
from datetime import datetime, timedelta
import requests

from odoo import fields, models, api
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class InheritLoyaltyCard(models.Model):
    _inherit = 'crm.loyalty.card'

    @job
    def sync_record(self, id):
        card = self.sudo().search([('id', '=', id)])
        brand = card.brand_id.code
        params = self.env['ir.config_parameter'].sudo()
        config_domain = 'config_domain_app_member_%s' % brand.lower()
        config_token = 'config_token_app_member_%s' % brand.lower()
        config_sync = 'sync_app_member_%s' % brand.lower()
        sync = params.get_param(config_sync)
        domain = params.get_param(config_domain)
        token = params.get_param(config_token)
        if sync == 'True':
            if domain and token:
                reward_ids = []
                if card.reward_ids:
                    for reward in card.reward_ids:
                        reward_ids.append(
                            {
                                'id': reward.id,
                                'name': reward.name,
                                'type_reward': reward.type_reward,
                                'product_id': None,
                                'quantity': reward.quantity,
                                'number_use': reward.number_use,
                                'stage': reward.stage,
                            }
                        )
                date_special = []
                if card.date_special:
                    for ds in card.date_special:
                        date_special.append(
                            {
                                'id': ds.id,
                                'name': ds.name,
                                'type': ds.type,
                                'date': ds.date,
                                'month': ds.month,
                            }
                        )

                body = {
                    'name': card.name,
                    'rank_id': card.rank_id.name,
                    'phone': card.partner_id.phone,
                    'amount': card.amount,
                    'bonus': card.bonus,
                    'reward_ids': reward_ids,
                    'date_special': date_special,
                    'date_interaction': card.date_interaction.strftime("%m/%d/%Y, %H:%M:%S"),
                    'validity_card': card.validity_card,
                    'time_active': card.time_active,
                    'due_date': card.due_date.strftime("%m/%d/%Y, %H:%M:%S"),
                    'money_reward': card.money_reward,
                }
                url = domain + '/api/v1/sync-loyalty'
                headers = {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                }
                response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    def write(self, vals):
        res = super(InheritLoyaltyCard, self).write(vals)
        if res:
            for loyalty in self:
                if loyalty.id:
                    loyalty.sudo().with_delay(priority=0, channel='sync_app_member_loyalty').sync_record(id=loyalty.id)
        return res

    def create(self, vals):
        res = super(InheritLoyaltyCard, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_app_member_loyalty').sync_record(id=res.id)
        return res
