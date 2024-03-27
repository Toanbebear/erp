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


class HobbyController(http.Controller):

    @validate_token
    @http.route("/api/v1/hobby", type="http", auth="none", methods=["GET"], csrf=False)
    def get_hobby(self, **payload):
        """ API 1.? Danh sách sở thích"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        fields = ['id', 'name']
        data = request.env['hobbies.interest'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)
