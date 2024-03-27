"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import logging
from odoo.exceptions import AccessError

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.addons.sci_seeding.controllers.common import seeding_validate_token
from odoo.http import request

_logger = logging.getLogger(__name__)


class GetProductController(http.Controller):

    @seeding_validate_token
    @http.route("/api/seeding/v1/get-his-service", type="http", auth="none", methods=["GET"], csrf=False)
    def v1_seeding_get_product(self, **payload):
        """ API get product"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        fields = ['default_code', 'name', 'product_id', 'service_category']
        data = request.env['sh.medical.health.center.service'].sudo().search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return invalid_response('Error')