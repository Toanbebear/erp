"""Part of odoo. See LICENSE file for full copyright and licensing details."""
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response
)
from odoo.addons.restful.controllers.main import (
    validate_token
)

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PricelistController(http.Controller):

    @validate_token
    @http.route("/api/v1/price-list", type="http", auth="none", method=['GET'], csrf=False)
    def get_price_list(self, **payload):
        """ API 1.3 Danh sách bảng giá """

        # Thông tin người dùng từ request
        brand_id = request.brand_id

        domain, fields, offset, limit, order = extract_arguments(payload)

        return valid_response(request.env['product.pricelist'].api_get_all_data_product_price_list(brand_id=brand_id,
                                                                      domain=domain,
                                                                      offset=offset,
                                                                      limit=limit,
                                                                      order=order))

    @validate_token
    @http.route("/api/v1/price-list/<id>", type="http", auth="none", method=['GET'], csrf=False)
    def get_price_list_by_id(self, id=None, **payload):
        # TODO
        """ API 1.10 Bảng giá chi tiết """

        # Thông tin người dùng từ request
        brand_id = request.brand_id

        domain, fields, offset, limit, order = extract_arguments(payload)
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "Sai id %s của bảng giá: " % id)
        return valid_response(request.env['product.pricelist'].api_get_all_data_product_price_list(brand_id=brand_id,
                                                                      id=_id,
                                                                      domain=domain,
                                                                      offset=offset,
                                                                      limit=limit,
                                                                      order=order))

    @validate_token
    @http.route("/api/v1/price-list-items/<id>", type="http", auth="none", method=['GET'], csrf=False)
    def get_price_items_list_by_id(self, id=None, **payload):
        """ API 1.5 Lấy chi tiết bảng giá theo ID"""
        domain, fields, offset, limit, order = extract_arguments(payload)

        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        price_list_items = []
        try:
            price_list_info = request.env['product.pricelist'].browse(_id)
            data = [{'info_price_list': {
                'brand': {'id': price_list_info.brand_id.id, 'name': price_list_info.brand_id.name},
                'company': {'id': price_list_info.company_id.id, 'name': price_list_info.company_id.name}}},
                {'info_price_list_item': price_list_items}]
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain = [('pricelist_id', '=', _id)]
        price_list_item_info = request.env['product.pricelist.item'].search(domain)

        if len(price_list_item_info) > 0:
            product_info = request.env['product.product']
            for element in price_list_item_info:
                if element.applied_on == '0_product_variant':  # Biến thể sản phẩm
                    product = element.product_id
                    val = {
                        'id': product.id,
                        'product': {'id': product.id, 'name': product.name},
                        'min_quantity': element.min_quantity,
                        'currency_id': element.currency_id.name,
                        'price': element.price,
                        'date_start': element.date_start,
                        'date_end': element.date_end,
                    }
                    price_list_items.append(val)
                elif element.applied_on == '1_product':  # Sản phẩm
                    for point in element.product_tmpl_id.product_variant_ids:
                        product = point
                        val = {
                            'id': product.id,
                            'product': {'id': product.id, 'name': product.name},
                            'min_quantity': element.min_quantity,
                            'currency_id': element.currency_id.name,
                            'price': element.price,
                            'date_start': element.date_start,
                            'date_end': element.date_end,
                        }
                        price_list_items.append(val)
                elif element.applied_on == '2_product_category':  # Nhóm sản phẩm/dịch vụ
                    for point in product_info.search([('categ_id', '=', element.categ_id.id)]):
                        product = point
                        val = {
                            'id': product.id,
                            'product': {'id': product.id, 'name': product.name},
                            'min_quantity': element.min_quantity,
                            'currency_id': element.currency_id.name,
                            'price': element.price,
                            'date_start': element.date_start,
                            'date_end': element.date_end,
                        }
                        price_list_items.append(val)
                else:  # Tất cả sản phẩm/dịch vụ
                    for point in product_info.search([]):
                        product = point
                        val = {
                            'id': product.id,
                            'product': {'id': product.id, 'name': product.name},
                            'min_quantity': element.min_quantity,
                            'currency_id': element.currency_id.name,
                            'price': element.price,
                            'date_start': element.date_start,
                            'date_end': element.date_end,
                        }
                        price_list_items.append(val)

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

