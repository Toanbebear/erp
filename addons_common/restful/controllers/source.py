"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo.addons.restful.common import (
    extract_arguments,
    valid_response,
    valid_response_once
)
from odoo.addons.restful.controllers.main import (
    validate_token
)

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SourceController(http.Controller):

    @validate_token
    @http.route("/api/v1/source-category", type="http", auth="none", methods=["GET"], csrf=False)
    def get_source_category(self, **payload):
        """ API 1.5 Danh sách nhóm nguồn CRM"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        data = request.env['crm.category.source'].api_get_source_category(domain=domain,
                                                                          fields=fields,
                                                                          offset=offset,
                                                                          limit=limit,
                                                                          order=order)
        if data:
            return valid_response(data)
        else:
            return valid_response_once({})

    @validate_token
    @http.route("/api/v1/source", type="http", auth="none", methods=["GET"], csrf=False)
    def get_source(self, **payload):
        """ API 1.6 Danh sách nguồn """
        return valid_response(request.env['utm.source'].api_get_source(brand_code=request.brand_code))
