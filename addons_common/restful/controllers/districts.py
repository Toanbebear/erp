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


class DistrictsController(http.Controller):

    @validate_token
    @http.route("/api/v1/districts", type="http", auth="none", methods=["GET"], csrf=False)
    def get_states(self, state_id=None, **payload):
        """ API 1.9 Danh sách quận/huyện"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(
            request.env['res.country.district'].api_get_data(state_id=int(state_id), offset=offset, limit=limit, order=order))
        domain = []
        if state_id:
            domain += [('state_id', '=', int(state_id))]
        fields = ['id', 'name']
        data = request.env['res.country.district'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/districts/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_district_by_id(self, id=None, **payload):
        """ API 1.10 Chi tiết quận huyện"""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = [("id", "=", _id)]
        # fields = ['id', 'code', 'name']
        data = request.env['res.country.district'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)
