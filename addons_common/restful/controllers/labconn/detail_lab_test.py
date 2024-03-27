# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from datetime import timedelta

from odoo import http
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token
from odoo.http import request

_logger = logging.getLogger(__name__)


class LabTestDetailController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/lab-test-detail", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_labconn_get_lab_test_detail(self, **payload):
        """
            1.8: Danh sách chỉ định chi tiết của từng bệnh nhân
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))

        key_required = ['walkin_code', 'company', 'stage']
        for key in key_required:
            if key not in body.keys():
                return {
                    'stage': False,
                    'message': "Thiếu tham số %s" % key
                }
        institution = request.env['sh.medical.health.center'].sudo().search(
            [('his_company.code', '=', body['company'])])
        if not institution:
            return {
                'stage': False,
                'message': "Chi nhánh không hợp lệ"
            }
        domain = [('name', '=', body['walkin_code']), ('institution', '=', institution.id)]
        if not int(body['stage']) in [0, 1]:
            return {
                'stage': False,
                'message': "Trường stage chỉ nhận 2 giá trị 0 và 1, đang truyền vào là %s" % body['stage']
            }
        walkin = request.env['sh.medical.appointment.register.walkin'].sudo().search(domain, limit=1)
        gender = {
            'male': 'Nam',
            'female': 'Nữ',
            'transguy': 'Transguy',
            'transgirl': 'Transgirl',
            'other': 'Khác'
        }
        stage_name = {
            'Draft': 'Chưa tiếp nhận',
            'Test In Progress': 'Đang thực hiện'
        }
        stage_code = {
            'Draft': 0,
            'Test In Progress': 1
        }
        stage_code_revert = {
            '0': 'Draft',
            '1': 'Test In Progress'
        }
        if walkin:
            data = []
            for lab_test in walkin.lab_test_ids:
                if lab_test.state == stage_code_revert[str(body['stage'])]:
                    address = ''
                    if lab_test.patient.street:
                        address += lab_test.patient.street + ','
                    if lab_test.patient.state_id:
                        address += lab_test.patient.state_id.name
                    value = {
                        'walkin_code': walkin.name,
                        'lab_test_code': lab_test.name,
                        'service_code': lab_test.test_type.default_code,
                        'service_name': lab_test.test_type.name,
                        'payment_code': '',
                        'patient_code': lab_test.patient.code_customer if lab_test.patient.code_customer else '',
                        'date_requested': (lab_test.date_requested + timedelta(hours=7)).strftime(
                            "%Y/%m/%d %H:%M:%S") if lab_test.date_requested else '',
                        'date_done': (lab_test.date_done + timedelta(hours=7)).strftime(
                            "%Y/%m/%d %H:%M:%S") if lab_test.date_done else '',
                        'patient_name': lab_test.patient.name,
                        'address': address if address else '',
                        'birth_date': lab_test.patient.birth_date.strftime(
                            "%Y/%m/%d") if lab_test.patient.birth_date else '',
                        'gender': gender[lab_test.patient.gender],
                        'diagnosis': lab_test.walkin.pathology if lab_test.walkin.pathology else lab_test.walkin.info_diagnosis,
                        'group_patient_code': "1",
                        'group_patient_name': "1",
                        'perform_room_code': lab_test.perform_room.code,
                        'perform_room_name': lab_test.perform_room.name,
                        'requestor_code': lab_test.requestor.employee_id.employee_code if lab_test.requestor else '',
                        'requestor_name': lab_test.requestor.employee_id.name if lab_test.requestor else '',
                        'email': lab_test.patient.email if lab_test.patient.email else '',
                        'phone': lab_test.patient.phone if lab_test.patient.phone else '',
                        'stage_name': stage_name[lab_test.state],
                        'stage_code': stage_code[lab_test.state],
                    }
                    data.append(value)
            return {
                    'stage': True,
                    'message': 'Thành công!!!',
                    'data': data
                }
        else:
            return {
                'stage': False,
                'message': 'Thất bại!!!',
                'data': ''
            }

# @labconn_validate_token
# @http.route("/api/v1/lab-test-detail", methods=["POST"], type="json", auth="none", csrf=False)
# def v1_labconn_get_lab_test_detail(self, **payload):
#     """
#         1.8: Danh sách chỉ định chi tiết của từng bệnh nhân
#     """
#     # get body
#     body = json.loads(request.httprequest.data.decode('utf-8'))
#
#     key_required = ['lab_test_code', 'company', 'stage']
#     for key in key_required:
#         if key not in body.keys():
#             return {
#                 'stage': False,
#                 'message': "Thiếu tham số %s" % key
#             }
#     institution = request.env['sh.medical.health.center'].sudo().search(
#         [('his_company.code', '=', body['company'])])
#     if not institution:
#         error_not_institution = "Chi nhánh không hợp lệ"
#         return error_not_institution
#     domain = [('name', '=', body['lab_test_code']), ('institution', '=', institution.id)]
#     if int(body['stage']) in [0, 1]:
#         if int(body['stage']) == 0:
#             domain.append(('state', '=', 'Draft'))
#         else:
#             domain.append(('state', '=', 'Test In Progress'))
#     else:
#         return {
#             'stage': False,
#             'message': "Trường stage chỉ nhận 2 giá trị 0 và 1, đang truyền vào là %s" % body['stage']
#         }
#     lab_test = request.env['sh.medical.lab.test'].sudo().search(domain, limit=1)
#     if lab_test:
#         address = ''
#         if lab_test.patient.street:
#             address += lab_test.patient.street + ','
#         if lab_test.patient.state_id:
#             address += lab_test.patient.state_id.name
#         gender = 'Nam'
#         if lab_test.patient.gender == 'female':
#             gender = 'Nữ'
#         elif lab_test.patient.gender == 'transguy':
#             gender = 'Transguy'
#         elif lab_test.patient.gender == 'transgirl':
#             gender = 'Transgirl'
#         elif lab_test.patient.gender == 'other':
#             gender = 'Khác'
#         value = {
#             'lab_test_code': lab_test.name,
#             'barcode': lab_test.name,
#             'service_code': lab_test.test_type.default_code,
#             'service_name': lab_test.test_type.name,
#             'payment_code': '',
#             'patient_code': lab_test.patient.code_customer,
#             'date_requested': (lab_test.date_requested + timedelta(hours=7)).strftime(
#                 "%d/%m/%Y, %H:%M:%S") if lab_test.date_requested else '',
#             'patient_name': lab_test.patient.name,
#             'address': address if address else '',
#             'year_of_birth': lab_test.patient.birth_date.strftime("%d/%m/%Y") if lab_test.patient.birth_date else '',
#             'gender': gender,
#             'diagnosis': lab_test.walkin.pathology if lab_test.walkin.pathology else lab_test.walkin.info_diagnosis,
#             'group_patient_code': 'group_patient_code',
#             'perform_room_code': lab_test.perform_room.code,
#             'requestor_code': lab_test.requestor.employee_id.employee_code if lab_test.requestor else '',
#             'requestor_name': lab_test.requestor.employee_id.name if lab_test.requestor else '',
#             'email': lab_test.patient.email if lab_test.patient.email else '',
#             'phone': lab_test.patient.phone if lab_test.patient.phone else '',
#             'stage': int(body['stage'])
#         }
#         if value:
#             return {
#                 'stage': True,
#                 'message': 'Thành công!!!',
#                 'data': value
#             }
#     else:
#         return {
#             'stage': False,
#             'message': 'Thất bại!!!'
#         }
