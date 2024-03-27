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


class StatesController(http.Controller):

    @validate_token
    @http.route("/api/v1/states", type="http", auth="none", methods=["GET"], csrf=False)
    def get_states(self, **payload):
        """ API 1.8 Danh sách tỉnh thành"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        data = []
        country_id = payload.get("country_id", None)
        if country_id:
            try:
                _id = int(country_id)
            except Exception as e:
                return invalid_response("invalid object id", "invalid literal %s for id with base " % country_id)
            return valid_response(
                request.env['res.country.state'].api_get_data(country_id=_id, offset=offset, limit=limit, order=order))
            domain = [('country_id', '=', _id)]
            fields = ['id', 'name', 'code']
            data = request.env['res.country.state'].search_read(
                domain=domain, fields=fields, offset=offset, limit=limit, order=order,
            )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/states/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_state_by_id(self, id=None, **payload):
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = [("id", "=", _id)]
        # fields = ['id', 'code', 'name']
        data = request.env['res.country.state'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)
