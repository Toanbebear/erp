# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.restful.controllers.app_member.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class GetDataLoyaltyAppMemberController(http.Controller):
    @app_member_validate_token
    @http.route("/api/v1/get-loyalty-app-member", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_loyalty_app_member(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        if 'phone' in body and 'brand_code' in body and body['brand_code'] and body['phone']:
            loyalty = request.env['crm.loyalty.card'].sudo().search([('phone', '=', body['phone']), ('brand_id.code', '=', body['brand_code'].upper())])
            if loyalty:
                reward_ids = []
                date_special = []
                if loyalty.reward_ids:
                    for reward in loyalty.reward_ids:
                        reward_ids.append(
                            {
                                'id': reward.id,
                                'name': reward.name,
                                'type_reward': reward.type_reward,
                                'product_id': reward.product_id.name,
                                'quantity': reward.quantity,
                                'number_use': reward.number_use,
                                'stage': reward.stage,
                            }
                        )
                if loyalty.date_special:
                    for ds in loyalty.date_special:
                        date_special.append(
                            {
                                'id': ds.id,
                                'name': ds.name,
                                'type': ds.type,
                                'date': ds.date,
                                'month': ds.month,
                            }
                        )
                data = {
                    'loyalty_code': loyalty.name,
                    'rank_id': loyalty.rank_id.name,
                    'amount': loyalty.amount,
                    'bonus': loyalty.bonus,
                    'reward_ids': reward_ids,
                    'date_special': date_special,
                    'due_date': loyalty.due_date,
                    'date_interaction': loyalty.date_interaction,
                    'validity_card': loyalty.validity_card,
                    'time_active': loyalty.time_active,
                    'money_reward': loyalty.money_reward,
                }
                return {
                    'stage': 0,
                    'message': 'Có thông tin Thẻ thành viên trên hệ thống ERP',
                    'data': data
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Không có Thẻ thành viên trên ERP',
                    'data': {}
                }

    @app_member_validate_token
    @http.route("/api/v1/get-loyalty-app-member-1", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_loyalty_app_member_1(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        if 'list_phone' in body and 'brand_code' in body and body['brand_code'] and body['list_phone']:
            list_data = []
            for phone in body['list_phone']:
                loyalty = request.env['crm.loyalty.card'].sudo().search(
                    [('phone', '=', phone), ('brand_id.code', '=', body['brand_code'].upper())])
                reward_ids = []
                date_special = []
                if loyalty:
                    if loyalty.reward_ids:
                        for reward in loyalty.reward_ids:
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
                    if loyalty.date_special:
                        for ds in loyalty.date_special:
                            date_special.append(
                                {
                                    'id': ds.id,
                                    'name': ds.name,
                                    'type': ds.type,
                                    'date': ds.date,
                                    'month': ds.month,
                                }
                            )
                    data = {
                        'phone': phone,
                        'loyalty_code': loyalty.name,
                        'rank_id': loyalty.rank_id.name if loyalty.rank_id.name else None,
                        'amount': loyalty.amount,
                        'bonus': loyalty.bonus,
                        'reward_ids': reward_ids,
                        'date_special': date_special,
                        'due_date': loyalty.due_date,
                        'date_interaction': loyalty.date_interaction,
                        'validity_card': loyalty.validity_card,
                        'time_active': loyalty.time_active,
                        'money_reward': loyalty.money_reward,

                    }
                    list_data.append(data)
            if list_data:
                return {
                    'stage': 0,
                    'message': 'Có thông tin Thẻ thành viên trên hệ thống ERP',
                    'data': list_data
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Không có Thẻ thành viên trên ERP',
                    'data': {}
                }
