# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.restful.common import extract_arguments
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token, response
from odoo.http import request

from odoo import http

_logger = logging.getLogger(__name__)


class LabtestController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/labtest", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_labconn_get_labtest(self, **payload):
        """
            1.4 Danh sách các loại xét nghiệm
        """
        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = []
        results = request.env['sh.medical.labtest.types'].sudo().search(domain, offset, limit)
        data = []
        for rec in results:
            if rec.has_child:
                value = {
                    'parent_labtest_code': '',
                    'code': rec.default_code,
                    'name': rec.name,
                    'unit': ''
                }
                data.append(value)
                for rec_lab_criteria in rec.lab_criteria:
                    value = {
                        'parent_labtest_code': rec.default_code,
                        'code': rec.default_code + '-' + str(rec_lab_criteria.sequence),
                        'name': rec_lab_criteria.name,
                        'unit': rec_lab_criteria.units.name if rec_lab_criteria.units else ''
                    }
                    data.append(value)
            else:
                value = {
                    'parent_labtest_code': '',
                    'code': rec.default_code,
                    'name': rec.name,
                    'unit': ''
                }
                data.append(value)
        if data:
            status = 0
            message = "Thành công"
        else:
            status = 1
            message = "Thất bại"
        return response(data, message_type=1, message_content=message, status=status)
