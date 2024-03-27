# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TypeServiceEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-type-service", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_type_service(self, **payload):
        """
            5.2 API cập nhật loại dịch vụ EHC-HIS
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 5.2 API cập nhật loại dịch vụ EHC-HIS ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'type_id',
            'type_code',
            'type_name',
            'group_master_id',
            'group_master_code',
            'stage',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        product_category_ehc = request.env['product.category'].sudo().search([('code', '=', body['type_code'])])
        value = {
            'type_ehc_id': body['type_id'],
            'stage': str(body['stage']),
            'name': body['type_name'],
        }
        group_master_id = request.env['crm.hh.ehc.group.master.service'].sudo().search(
            [('group_master_code', '=', body['group_master_code']),
             ('group_master_id', '=', int(body['group_master_id']))])
        if group_master_id:
            value['group_master_id'] = group_master_id.id
        else:
            group_master_id = request.env['crm.hh.ehc.group.master.service'].sudo().create({
                'name': body['type_name'],
                'code': body['type_code'],
                'group_master_id': body['group_master_id'],
                'group_master_code': body['group_master_code'],
            })
            if group_master_id:
                value['group_master_id'] = group_master_id.id
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat loai dich vu that bai!!!'
                }
        if product_category_ehc:
            result = product_category_ehc.sudo().write(value)
            if result:
                TypeServiceEHCController.update_type_service_his_erp(self=self, type_service=product_category_ehc, type=1)
                return {
                    'stage': 0,
                    'message': 'Cap nhat loai dich vu thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat loai dich vu that bai!!!'
                }
        else:
            value['code'] = body['type_code']
            result = product_category_ehc.sudo().create(value)
            if result:
                TypeServiceEHCController.update_type_service_his_erp(self=self, type_service=result, type=0)
                return {
                    'stage': 0,
                    'message': 'Cap nhat loai dich vu thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat loai dich vu that bai!!!'
                }

    def update_type_service_his_erp(self, type_service, type):
        # 0: tạo mới
        # khác 0: cập nhật
        if type_service:
            data = {
                'product_cat_id': type_service.id,
                'name': type_service.name,
                'complete_name': type_service.complete_name if type_service.complete_name else type_service.name,
            }
            if type == 0:
                service_category_his = request.env['sh.medical.health.center.service.category'].sudo().create(data)
            else:
                service_category_his = request.env['sh.medical.health.center.service.category'].sudo().write(data)