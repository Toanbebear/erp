"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    valid_response,
    valid_response_once,
)
from odoo.addons.restful.controllers.main import (
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class StageController(http.Controller):

    @validate_token
    @http.route("/api/v1/stage", type="http", auth="none", methods=["GET"], csrf=False)
    def get_stage_crm(self, **payload):
        """ API 1.11 Danh sách trạng thái CRM"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = [('rest_api', '=', True)]
        fields = ['id', 'name']
        data = request.env['crm.stage'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response_once({})


    @validate_token
    @http.route("/api/v1/type-phone-call", type="http", auth="none", methods=["GET"], csrf=False)
    def get_type_phone_call(self, **payload):
        """ API  Danh sách loại phone call"""

        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = [('phone_call', '=', True)]
        fields = ['id', 'name']
        data = request.env['crm.type'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response_once({})