import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, convert_string_to_date, create_log

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ContractGroupExam(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/contract", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_create_contract(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= API danh sách hợp đồng ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'id',
            'name',
            'company_name',
            'address',
            'source_code',
            'start_date',
            'end_date',
            'invoice_method',
            'stage'
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }
        if str(body['invoice_method']) not in ['1','2','3','4']:
            return {
                'stage': 1,
                'message': "Hình thức thu tiền phải là chỉ nhận giá trị 1,2,3,4"
            }
        value = {
            'id_ehc': int(body['id']),
            'name': body['name'],
            'company_name': body['company_name'],
            'address': body['address'],
            'source_code': body['source_code'],
            'start_date': convert_string_to_date(body['start_date']),
            'end_date': convert_string_to_date(body['end_date']),
            'invoice_method': str(body['invoice_method']),
            'stage': str(body['stage'])
        }
        contract = request.env['crm.hh.ehc.contract.group.exam'].sudo().create(value)
        if contract:
            create_log(model_name=contract._name, input=body, id_record=contract.id,
                       response=False,
                       type_log=str(0),
                       name_log='Tạo hợp đồng khám đoàn',
                       url=False,
                       header=False, status_code=False)
            return {
                'stage': 0,
                'message': 'Cap nhat hop dong kham doan thanh cong!!!'
            }
        else:
            return {
                'stage': 1,
                'message': 'Cap nhat hop dong kham doan thất bại!!!'
            }