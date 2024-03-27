# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from datetime import timedelta, datetime

from odoo import http
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token
from odoo.http import request

_logger = logging.getLogger(__name__)


class ProgressLabTestController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/progress-lab-test", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_labconn_progress_lab_test(self, **payload):
        """
            1.9 Cập nhật trạng thái đã tiếp nhận và huỷ tiếp nhận
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('======== 1.9 Cập nhật trạng thái đã tiếp nhận và huỷ tiếp nhận ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        key_required = ['lab_test_code', 'company', 'service_code', 'date_requested', 'stage']
        for key in key_required:
            if key not in body.keys():
                message = "Thiếu tham số %s" % key
                return message
        institution = request.env['sh.medical.health.center'].sudo().search(
            [('his_company.code', '=', body['company'])])
        if not institution:
            error_not_institution = "Chi nhánh không hợp lệ"
            return error_not_institution
        if not int(body['stage']) in [0, 1]:
            return {
                'stage': False,
                'message': "Trường stage chỉ nhận 2 giá trị 0 và 1, đang truyền vào là %s" % body['stage']
            }
        # date_requested = datetime.strptime(body['date_requested'], "%d/%m/%Y %H:%M:%S") - timedelta(hours=7)
        date_analysis = datetime.strptime(body['date_requested'], "%d/%m/%Y %H:%M:%S") - timedelta(hours=7)

        lab_test = request.env['sh.medical.lab.test'].sudo().search([('name', '=', body['lab_test_code']),
                                                                     ('test_type.default_code', '=',
                                                                      body['service_code']),
                                                                     ('institution', '=', institution.id)], limit=1)
        if lab_test:
            if int(body['stage']) == 1:
                lab_test.state = 'Test In Progress'
                lab_test.date_analysis = date_analysis
            else:
                lab_test.state = 'Draft'
            return {
                'stage': True,
                'message': 'Thành công!!!'
            }
        else:
            return {
                'stage': False,
                'message': 'Thất bại!!!'
            }
