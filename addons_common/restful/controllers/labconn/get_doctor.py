# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.restful.common import extract_arguments
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token, response, get_company_code
from odoo.http import request

from odoo import http

_logger = logging.getLogger(__name__)


class DoctorController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/doctor", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_labconn_get_doctor(self, **payload):
        """
            1.1 Danh sách bác sĩ chỉ định
        """
        domain, fields, offset, limit, order = extract_arguments(payload)
        company_code = get_company_code()
        domain = [('company_id.code', 'in', company_code)]
        results = request.env['sh.medical.physician'].sudo().search(domain, offset, limit)
        list_code_check = []
        data = []
        for rec in results:
            if rec.employee_id.employee_code not in list_code_check:
                value = {
                    'id': rec.id,
                    'code': rec.employee_id.employee_code if rec.employee_id.employee_code else '',
                    'name': rec.name,
                    'company': rec.company_id.code
                }
                data.append(value)
                list_code_check.append(rec.employee_id.employee_code)
        if data:
            status = 0
            message = "Thành công"
        else:
            status = 1
            message = "Thất bại"
        return response(data, message_type=1, message_content=message, status=status)