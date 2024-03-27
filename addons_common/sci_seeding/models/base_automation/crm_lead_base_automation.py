# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json

import requests

from odoo import models, fields, api, _
from odoo.addons.sci_seeding.models.common import get_token_sale, retry, get_source_seeding, get_source_ctv, \
    get_url_sale


class CRMBaseAutomation(models.Model):
    _inherit = 'crm.lead'

    @retry()
    def check_source(self):
        seeding_sources = get_source_seeding()
        ctv_sources = get_source_ctv()
        if self.source_id in seeding_sources:
            if self.type == 'lead':
                self.push_data_lead(type='seeding')
            else:
                self.push_data_booking(type='seeding')
        if self.source_id in ctv_sources:
            if self.type == 'lead':
                self.push_data_lead(type='ctv')
            else:
                self.push_data_booking(type='ctv')

    def push_data_lead(self, type=None):
        token = get_token_sale()
        # url = get_url_sale() + '/api/v1/create-booking'
        # headers = {
        #     'Content-Type': 'application/json',
        #     'access-token': token
        # }
        #
        # data = {
        #     "name": "Dinh Nam 1234321",
        #     "customer_classification": "4",
        #     "phone_1": "01245678",
        #     "contact_name": "Nam Đình",
        #     "sex": "man",
        #     "city_id": "VN-HN",
        #     "country_id": "VN",
        #     "category_source_id": "1",
        #     "source_id": "1",
        #     "stage_id": "2",
        #     "type_data_partner": "new_customer",
        #     "booking_date": "2022-10-30 08:00:00",
        #     "expected_day": "weekday",
        #     "effect": "effect",
        #     "day_expire": "2022-10-31 08:00:00",
        #     "custom_come": "no",
        #     "company_id": "KN.HCM.01",
        #     "price_list_id": "23",
        #     "currency_id": "VND",
        #     "seeding_user_id": "US0000002",
        #     "check": "seeding",
        #     "line_ids": [
        #         {
        #             "his_service_id": "1",
        #             "stage": "new",
        #             "odontology": "True"
        #         },
        #         {
        #             "his_service_id": "1",
        #             "stage": "new",
        #             "odontology": "True"
        #         }]
        # }
        #
        # response = requests.post(url=url, data=json.dumps(data), headers=headers)
        # print(response)

    def push_data_booking(self, type=None):
        token = get_token_sale()
        url = get_url_sale() + '/api/v1/create-booking'
        headers = {
            'Content-Type': 'application/json',
            'access-token': token
        }

        data = {
            "name": self.name,
            "customer_classification": self.customer_classification,
            "phone_1": self.phone,
            "contact_name": self.contact_name,
            "sex": self.gender,
            "city_id": "VN-HN",
            "country_id": "VN",
            "category_source_id": self.category_source_id,
            "source_id": self.source_id,
            "stage_id": "2",
            "type_data_partner": self.type_data_partner,
            "booking_date": "2022-10-30 08:00:00",
            "expected_day": "",
            "effect": self.effect,
            "day_expire": "2022-10-31 08:00:00",
            "custom_come": self.custom_come,
            "company_id": self.company_id.code,
            "price_list_id": "",
            "currency_id": "",
            "seeding_user_id": "US0000002",
            "check": type,
        }

        response = requests.post(url=url, data=json.dumps(data), headers=headers)
        print(response)
