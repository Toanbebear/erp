# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.restful.common import extract_arguments
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token, response
from odoo.http import request

from odoo import http

_logger = logging.getLogger(__name__)


class PatientController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/patient", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_labconn_get_patient(self, **payload):
        """
            1.3 Danh sách bệnh nhân
        """
        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = []
        results = request.env['sh.medical.patient'].sudo().search(domain, offset, limit)
        data = []
        for rec in results:
            value = {
                'id': rec.id,
                'code': rec.code_customer if rec.code_customer else '',
                'name': rec.name,
            }
            data.append(value)
        if data:
            status = 0
            message = "Thành công"
        else:
            status = 1
            message = "Thất bại"
        return response(data, message_type=1, message_content=message, status=status)