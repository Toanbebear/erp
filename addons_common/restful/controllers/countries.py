"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    valid_response,
)
from odoo.addons.restful.controllers.main import (
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class CountriesController(http.Controller):

    @validate_token
    @http.route("/api/v1/countries", type="http", auth="none", methods=["GET"], csrf=False)
    def get_countries(self, **payload):
        """ API 1.? Danh sách quốc gia"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['res.country'].api_get_data(domain=domain,
                                                                      offset=offset,
                                                                      limit=limit,
                                                                      order=order))
        fields = ['id', 'name', 'code']
        data = request.env['res.country'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)

