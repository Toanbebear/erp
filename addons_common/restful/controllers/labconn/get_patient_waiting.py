# Part of odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
import logging
from datetime import timedelta

from odoo import http
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token
from odoo.http import request

_logger = logging.getLogger(__name__)


class PatientWaitingController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/patient-waiting", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_labconn_get_patient_waiting(self, **payload):
        """
            1.7 Danh sách bệnh nhân chờ
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 1.7 Danh sách bệnh nhân chờ ===========================')
        _logger.info("body: %s" % body)
        _logger.info('=================================================================================')

        key_required = ['start_date', 'end_date', 'company', 'stage']
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
        start_date = datetime.datetime.strptime(body['start_date'], '%d-%m-%Y')
        end_date = datetime.datetime.strptime(body['end_date'], '%d-%m-%Y') + timedelta(days=1)
        domain = [('date', '>=', start_date),
                  ('date', '<=', end_date),
                  ('institution', '=', institution.id)]
        _logger.info("domain: %s" % domain)
        # if int(body['stage']) in [0, 1]:
        #     if int(body['stage']) == 0:
        #         domain.append(('state', 'in', ['WaitPayment', 'Scheduled']))
        #     else:
        #         domain.append(('state', '=', 'InProgress'))
        # else:
        #     return {
        #         'stage': False,
        #         'message': "Trường stage chỉ nhận 2 giá trị 0 và 1, đang truyền vào là %s" % body['stage']
        #     }
        # offset = 0
        # limit = 10
        # if 'offset' in body:
        #     offset = int(body['offset'])
        # if 'limit' in body:
        #     limit = int(body['limit'])

        # walkines = request.env['sh.medical.appointment.register.walkin'].sudo().search(domain, offset=offset,
        #                                                                                 limit=limit)

        walkines = request.env['sh.medical.appointment.register.walkin'].sudo().search(domain)
        _logger.info("==================================")
        _logger.info("walkines: %s" % walkines)
        data_walkines_valid = []
        for rec in walkines:
            _logger.info("rec: %s" % rec)
            len_lab = len(rec.lab_test_ids)
            len_lab_check = 0
            _logger.info("len_lab: %s" % len_lab)
            for rec_lab in rec.lab_test_ids:
                if rec_lab.state in ['Test In Progress', 'Completed']:
                    len_lab_check += 1
            _logger.info("len_lab_check: %s" % len_lab)
            if len_lab != len_lab_check:
                data_walkines_valid.append(rec)
        _logger.info("==================================")
        data = []
        gender = {
            'male': 'Nam',
            'female': 'Nữ',
            'transguy': 'Transguy',
            'transgirl': 'Transgirl',
            'other': 'Khác'
        }
        for record in data_walkines_valid:
            if record.lab_test_ids:
                address = ''
                if record.patient.street:
                    address += record.patient.street + ','
                if record.patient.state_id:
                    address += record.patient.state_id.name

                # list_lab_test_code = []
                # for lab_tests in record.lab_test_ids:
                #     list_lab_test_code.append(lab_tests.name)

                value = {
                    'walkin_code': record.name,
                    'date_requested': (record.date + timedelta(hours=7)).strftime(
                        "%Y/%m/%d %H:%M:%S") if record.date else '',
                    'payment_code': '',
                    'patient_code': record.patient.code_customer if record.patient.code_customer else '',
                    'patient_name': record.patient.name,
                    'address': address if address else '',
                    'birth_date': record.patient.birth_date.strftime(
                            "%Y/%m/%d") if record.patient.birth_date else '',
                    'gender': gender[record.patient.gender],
                    'diagnosis': record.pathology if record.pathology else record.info_diagnosis,
                    'group_patient_code': "1",
                    'group_patient_name': "1",
                    # 'list_lab_test_code': list_lab_test_code,
                    # 'perform_room_code': record.perform_room.code,
                    # 'perform_room_name': record.perform_room.name,
                    # 'requestor_code': record.requestor.employee_id.employee_code if record.requestor else '',
                    # 'requestor_name': record.requestor.employee_id.name if record.requestor else '',
                    'stage': int(body['stage'])
                }
                data.append(value)
        if data:
            return {
                'stage': True,
                'message': 'Thành công!!!',
                'data': data
            }
        else:
            return {
                'stage': False,
                'message': 'Thất bại!!!'
            }
