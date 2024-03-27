import logging
from datetime import timedelta
from datetime import datetime
from odoo.addons.connect_app_member.controllers.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class GetDataProduct(http.Controller):
    @app_member_validate_token
    @http.route("/api/app-member/v1/get-service-group", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_service__group_app_member(self, **payload):
        data = []
        code = ''
        body = json.loads(request.httprequest.data.decode('utf-8'))
        if body['brand_code'] == 'kn':
            list_service_group = request.env['sh.medical.health.center.service.category'].sudo().search(
                [('code', 'ilike', 'KN%')])
            for rec in list_service_group:
                value = {
                    'erp_id': rec.id,
                    'code': rec.code,
                    'name': rec.name
                }
                data.append(value)
        if body['brand_code'] == 'pr':
            list_service_group = request.env['sh.medical.health.center.service.category'].sudo().search(
                [('code', 'ilike', 'P%')])
            for rec in list_service_group:
                default_code = rec.code
                if default_code[0] == 'P':
                    value = {
                        'erp_id': rec.id,
                        'code': rec.code,
                        'name': rec.name
                    }
                    data.append(value)
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Không có dữ liệu',
                'data': None
            }

    @app_member_validate_token
    @http.route("/api/app-member/v1/get-service", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_service_app_member(self, **payload):
        data = []
        body = json.loads(request.httprequest.data.decode('utf-8'))
        if body['brand_code'] == 'kn':
            list_service = request.env['sh.medical.health.center.service'].sudo().search(
                [('default_code', 'like', 'KN%')])
            for rec in list_service:
                default_code = rec.default_code
                if default_code[0] == 'K':
                    value = {
                        'id_service': rec.id,
                        'name': rec.name,
                        'default_code': rec.default_code,
                        'service_type': rec.his_service_type,
                        'id_service_group': rec.service_category.id,
                        'product_id': rec.product_id.id
                    }
                    data.append(value)
        if body['brand_code'] == 'pr':
            list_service = request.env['sh.medical.health.center.service'].sudo().search(
                [('default_code', 'like', 'P%')])
            for rec in list_service:
                default_code = rec.default_code
                if default_code[0] == 'P' and rec.his_service_type != False:
                    value = {
                        'id_service': rec.id,
                        'name': rec.name,
                        'default_code': rec.default_code,
                        'service_type': rec.his_service_type,
                        'id_service_group': rec.service_category.id,
                        'product_id': rec.product_id.id
                    }
                    data.append(value)
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Không có dữ liệu',
                'data': None
            }

    @app_member_validate_token
    @http.route("/api/app-member/v1/get-list-price", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_list_price_app_member(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        data = []
        code = ''
        if body['brand_code'] == 'kn':
            code = 'KN'
        if body['brand_code'] == 'pr':
            code = 'PR'
        brand = request.env['res.brand'].sudo().search([('code', '=', code)])
        price_list = request.env['product.pricelist'].sudo().search(
            [('brand_id', '=', brand.id), ('type', '=', 'service')])
        for rec in price_list:
            for item in rec.item_ids:
                value_price = {
                    'service_name': item.product_id.name,
                    'product_id': item.product_id.id,
                    'price': item.fixed_price
                }
                data.append(value_price)
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Không có dữ liệu',
                'data': None
            }
