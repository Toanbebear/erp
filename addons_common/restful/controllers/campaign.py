"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.addons.restful.controllers.main import (
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class CampaignController(http.Controller):

    @validate_token
    @http.route("/api/v1/campaign", type="http", auth="none", methods=["GET"], csrf=False)
    def get_campaign(self, **payload):
        """ API 1.? Danh sách chiến dịch"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['utm.campaign'].api_get_data_campaign(request.brand_id,
                                                                           offset=offset,
                                                                           limit=limit,
                                                                           order=order))

    # @validate_token
    # @http.route("/api/v1/campaign", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_campaign(self, **payload):
    #     # TODO
    #     """ API 1.? Danh sách chiến dịch"""
    #
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #     brand_id = request.brand_id
    #     domain = [('campaign_status', '!=', 3), ('brand_id', '=', brand_id)]
    #     fields = ['id', 'name', 'brand_id']
    #     data = request.env['utm.campaign'].search_read(
    #         domain=domain, fields=fields, offset=offset, limit=limit, order=order,
    #     )
    #     if data:
    #         return valid_response(data)
    #     else:
    #         return valid_response(data)

    @validate_token
    @http.route("/api/v1/campaign/<id>", type="http", auth="none", method=['GET'], csrf=False)
    def get_campaign_by_id(self, id=None, **payload):
        """ API 1.3 Lấy danh sách chiến dịch theo ID"""

        domain, fields, offset, limit, order = extract_arguments(payload)

        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        return valid_response(request.env['utm.campaign'].api_get_data(request.brand_id, _id,
                                                                       offset=offset,
                                                                       limit=limit,
                                                                       order=order))
        domain.append(('id', '=', _id))

        data = request.env['utm.campaign'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order)

        if data:
            return valid_response(data)
        else:
            return valid_response(data)
