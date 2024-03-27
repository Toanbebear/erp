# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DepartmentEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-department", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_department(self, **payload):
        """
            1.2 API cập nhật phòng khám EHC-HIS
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 1.2 API cập nhật phòng khám EHC-HIS ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'room_id',
            'room_code',
            'room_name',
            'id_department_room',
            'code_department_room',
            'room_type_id',
            'stage',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        department_ehc = request.env['crm.hh.ehc.department'].sudo().search([('room_code', '=', body['room_code'])])

        value = {
            'room_id': body['room_id'],
            'room_code': body['room_code'],
            'room_name': body['room_name'],
            'id_department_room': body['id_department_room'],
            'code_department_room': body['code_department_room'],
            # 'room_type_id': body['room_type_id'],
            'room_stage': str(body['stage']),
        }

        # search khoa
        if 'id_department_room' in body and body['id_department_room']:
            faculty_id = request.env['crm.hh.ehc.faculty'].sudo().search(
                [('id_ehc', '=', int(body['id_department_room']))])
            if faculty_id:
                value['faculty_id'] = faculty_id.id
            else:
                value['faculty_id'] = False

        if department_ehc:
            result = department_ehc.sudo().write(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat phong kham thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat phong kham that bai!!!'
                }
        else:
            result = department_ehc.sudo().create(value)
            if result:
                return {
                    'stage': 0,
                    'message': 'Cap nhat phong kham thanh cong!'
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Cap nhat phong kham that bai!!!'
                }

