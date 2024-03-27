# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from datetime import datetime
from odoo.addons.connect_app_member.controllers.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class GetDataWalkinAppMemberController(http.Controller):
    @app_member_validate_token
    @http.route("/api/app-member/v1/get-walkin", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_walkin_app_member(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        field_require = [
            'phone',
            'brand_code',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thiếu tham số %s' % field,
                }
            if not body[field]:
                return {
                    'stage': 1,
                    'message': 'Thiếu tham số %s đang rỗng' % field,
                }

        partner = request.env['res.partner'].sudo().search(
            ['|', ('phone', '=', body['phone']), ('mobile', '=', body['phone'])])
        data = []
        if partner:
            info_take_care = ''
            walkin_ids = partner.walkin_ids
            for walkin_id in walkin_ids:
                if walkin_id.institution.his_company.brand_id.code == body['brand_code'].upper():
                    for ret in walkin_id.service:
                        value = {
                            'id': walkin_id.id,
                            'name': walkin_id.name,
                            'state': walkin_id.state,
                            'booking': walkin_id.booking_id.name,
                            'institution': walkin_id.institution.his_company.code,
                            'service_room': walkin_id.service_room.name,
                            'date': walkin_id.date,
                            'service_date': walkin_id.service_date,
                            'service_date_start': walkin_id.service_date_start,
                            'reason_check': walkin_id.reason_check,
                            'services': ret.name,
                            'id_services': ret.product_id.id,
                            'pathological_process': walkin_id.pathological_process,
                            'info_diagnosis': walkin_id.info_diagnosis,
                            'note': walkin_id.note,
                            'doctor': walkin_id.doctor.name,
                            'reception_nurse': walkin_id.reception_nurse.name,
                        }
                        reexam_data = []
                        for reexam_id in walkin_id.reexam_ids:
                            if reexam_id.state == 'Confirmed':
                                reexam_line_ids_data = []
                                for reexam_line in reexam_id.days_reexam_phone:
                                    type_reexam = reexam_line.type
                                    if type_reexam not in (
                                            'Check', 'Check1', 'Check2', 'Check3', 'Check4', 'Check5', 'Check6',
                                            'Check7',
                                            'Check8'):
                                        for service in reexam_line.for_service_phone:
                                            if service.product_id.id == ret.product_id.id:
                                                reexam_line_id_data = {
                                                    'name': reexam_line.name_phone,
                                                    'type': reexam_line.type,
                                                    'date_recheck': reexam_line.date_recheck_phone + timedelta(days=1),
                                                    'for_services': ret.name,
                                                }
                                                reexam_line_ids_data.append(reexam_line_id_data)
                                reexam_value = {
                                    'name_reexam': reexam_id.name,
                                    'company_reexem': reexam_id.company.code,
                                    'date_reexam': reexam_id.date,
                                    'date_out_reexam': reexam_id.date_out,
                                    'services': ret.name,
                                    'reexam_ids': reexam_line_ids_data,
                                    'info_take_care': ret.info if ret.info else None,
                                }
                                reexam_data.append(reexam_value)
                        value['reexam_data'] = reexam_data
                        data.append(value)
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Thất bại',
                'data': {}
            }

    @app_member_validate_token
    @http.route("/api/app-member/v1/get-walkin-1", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_walkin_app_member_1(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        field_require = [
            'phone',
            'brand_code',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thiếu tham số %s' % field,
                }
            if not body[field]:
                return {
                    'stage': 1,
                    'message': 'Thiếu tham số %s đang rỗng' % field,
                }

        partner = request.env['res.partner'].sudo().search(
            ['|', ('phone', '=', body['phone']), ('mobile', '=', body['phone'])], limit=1)
        data = []
        if partner:
            info_take_care = ''
            walkin_ids = partner.walkin_ids
            for walkin_id in walkin_ids:
                if walkin_id.institution.his_company.brand_id.code == body['brand_code'].upper():
                    for ret in walkin_id.service:
                        value = {
                            'id': walkin_id.id,
                            'name': walkin_id.name,
                            'state': walkin_id.state,
                            'booking': walkin_id.booking_id.name,
                            'institution': walkin_id.institution.his_company.code,
                            'service_room': walkin_id.service_room.name,
                            'date': walkin_id.date,
                            'service_date': walkin_id.service_date,
                            'service_date_start': walkin_id.service_date_start,
                            'reason_check': walkin_id.reason_check,
                            'services': ret.name,
                            'id_services': ret.product_id.id,
                            'pathological_process': walkin_id.pathological_process,
                            'info_diagnosis': walkin_id.info_diagnosis,
                            'note': walkin_id.note,
                            'doctor': walkin_id.doctor.name,
                            'reception_nurse': walkin_id.reception_nurse.name,
                            'phone': walkin_id.booking_id.phone
                        }
                        reexam_data = []
                        for reexam_id in walkin_id.reexam_ids:
                            if reexam_id.state == 'Confirmed':
                                reexam_line_ids_data = []
                                for reexam_line in reexam_id.days_reexam_phone:
                                    type_reexam = reexam_line.type
                                    if type_reexam not in (
                                            'Check', 'Check1', 'Check2', 'Check3', 'Check4', 'Check5', 'Check6',
                                            'Check7',
                                            'Check8'):
                                        for service in reexam_line.for_service_phone:
                                            if service.product_id.id == ret.product_id.id:
                                                reexam_line_id_data = {
                                                    'name': reexam_line.name_phone,
                                                    'type': reexam_line.type,
                                                    'date_recheck': reexam_line.date_recheck_phone + timedelta(days=1),
                                                    'for_services': ret.name,
                                                }
                                                reexam_line_ids_data.append(reexam_line_id_data)
                                reexam_value = {
                                    'name_reexam': reexam_id.name,
                                    'company_reexem': reexam_id.company.code,
                                    'date_reexam': reexam_id.date,
                                    'date_out_reexam': reexam_id.date_out,
                                    'services': ret.name,
                                    'reexam_ids': reexam_line_ids_data,
                                    'info_take_care': ret.info if ret.info else None,
                                }
                                reexam_data.append(reexam_value)
                        value['reexam_data'] = reexam_data
                        data.append(value)
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Thất bại',
                'data': {}
            }
