# -*- coding: utf-8 -*-

import datetime
import logging
from urllib.request import urlopen
from xml.etree.ElementTree import parse

import requests

from odoo import fields, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    auto_update = fields.Boolean('Tự động cập nhật tỷ giá')


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    @api.model
    def _get_currency_rate(self):
        url = 'https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx'
        # response = requests.get(url)
        xml_doc = parse(urlopen(url))
        root = xml_doc.getroot()

        values = []
        # lấy danh sách cty
        # companies = self.env['res.company'].search([])
        companies = self.env['res.company'].search_read([('active', '=', True)], ['id'])
        currencies = self.env['res.currency'].search_read([('active', '=', True),
                                                           ('auto_update', '=', True)],
                                                          ['id', 'name'])

        # currency_allow = {'USD': 2, 'EUR': 1, 'JPY': 25, 'AUD': 21, 'CNY': 7}
        for currency in currencies:
            data = root.findall(".//Exrate[@CurrencyCode='%s']" % currency['name'])
            date_rate = root.findtext(".//DateTime")
            date_rate = datetime.datetime.strptime(
                date_rate, '%m/%d/%Y %I:%M:%S %p'
            )

            for child in data:
                # currency_code = child.get('CurrencyCode')
                buy = child.get('Buy')
                # transfer = child.get('Transfer')
                # sell = child.get('Sell')
                buy = buy.replace(',', '')
                for company in companies:
                    name = date_rate.strftime("%Y-%m-%d")
                    value = {
                        'name': name,
                        'rate': 1 / float(buy),
                        'currency_id': currency['id'],
                        'company_id': company['id'],
                    }
                    count = self.search_count(
                        [('name', '=', name), ('currency_id', '=', currency['id']), ('company_id', '=', company['id'])])

                    if not count:
                        values.append(value)
        try:
            self.create(values)
            _logger.info('Cron::::: Lấy tỉ giá từ tự động... Done')
        except Exception:
            _logger.info('Cron::::: Đã cập nhật tỉ giá')
            raise UserError('Đã cập nhật tỉ giá ngày : {}'.format(date_rate.strftime("%d-%m-%Y")))
