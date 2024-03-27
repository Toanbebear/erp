"""Part of odoo. See LICENSE file for full copyright and licensing details."""
from odoo.addons.restful.common import (
    valid_response
)
from odoo.addons.restful.controllers.main import (
    validate_token
)

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ProductController(http.Controller):
    @validate_token
    @http.route("/api/v1/services", type="http", auth="none", method=['GET'], csrf=False)
    def get_products(self, company_id=None, pricelist_id=None, code=None, **payload):
        if not pricelist_id or not code:
            return valid_response([])
        # Tách mã dịch vụ bằng dấu phẩy
        codes = code.split(',')
        return valid_response(request.env['product.product'].api_get_data_product(int(pricelist_id), codes))
