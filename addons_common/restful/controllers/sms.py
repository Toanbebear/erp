"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.addons.restful.controllers.main import (
    validate_token
)

_logger = logging.getLogger(__name__)


class SmsController(http.Controller):

    @validate_token
    @http.route("/api/v1/sms", type="http", auth="none", methods=["GET"], csrf=False)
    def get_sms(self, **payload):
        """ API 6.1 Lấy sms"""

        # TODO Mô tả chức năng nhiệm vụ
