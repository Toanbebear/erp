# Part of odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
import logging
from datetime import datetime, timedelta

from odoo import http
from odoo.addons.restful.controllers.labconn.labconn_common import labconn_validate_token
from odoo.http import request

_logger = logging.getLogger(__name__)


class GetResultLabTestController(http.Controller):
    @labconn_validate_token
    @http.route("/api/v1/get-result-lab-test", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_labconn_get_result_lab_test(self, **payload):
        '''
            1.10 API cập nhật kết quả xét nghiệm
        '''
        '''
            Xét nghiệm không có xét nghiệm con
            body = {
                "lab_test_code": "XN-2021-000342",
                "service_labtest_code": "SH01",
                "company": "KN.HCM.01",
                "patient_code": "CUS307923",
                "result_lab_test": [
                    {
                        "code": "SH01",
                        "result": "6.0",
                        "unit": "",
                        "stat": 1
                    }
                ],
                "time_return_result": "07/05/2022 12:30",
                "doctor_conclusion": "oke",
                "machine_code": "TB01"
            }
        '''
        '''
            Xét nghiệm có xét nghiệm con
            {
                "lab_test_code": "XN-2022-038995",
                "service_labtest_code": "DM01",
                "company": "KN.HCM.01",
                "patient_code": "CUS307923",
                "result_lab_test": [
                    {
                        "code": "DM01-1",
                        "result": "DM01-1",
                        "unit": "",
                        "stat": 1
                    },
                    {
                        "code": "DM01-2",
                        "result": "DM01-2",
                        "unit": "",
                        "stat": 1
                    },
                    {
                        "code": "DM01-3",
                        "result": "DM01-3",
                        "unit": "",
                        "stat": 1
                    }
                ],
                "time_return_result": "07/05/2022 12:30",
                "doctor_conclusion": "oke",
                "machine_code": "TB01"
            }
        '''
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 1.10 API cập nhật kết quả xét nghiệm ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'lab_test_code',
            'type',
            'company',
            'service_labtest_code',
            'patient_code',
            'result_lab_test',
            'time_return_result',
            'doctor_conclusion',
            'machine_code',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': True,
                    'message': 'Thiếu tham số %s!!!' % field
                }
        if body['type'] in ['0', '1']:
            # 0: cập nhật kết quả xét nghiệm
            # 1: hủy kết quả xét nghiệm
            if body['type'] == '0':
                if body['lab_test_code']:
                    # tìm phiếu xét nghiệm
                    labtest = request.env['sh.medical.lab.test'].sudo().search(
                        [('name', '=', body['lab_test_code']), ('institution.his_company.code', '=', body['company'])])
                    if labtest:
                        if labtest.state == 'Test In Progress':
                            date_done = datetime.strptime(body['time_return_result'], '%d/%m/%Y %H:%M')
                            date_done = date_done - timedelta(hours=7, minutes=00)
                            # search bác sĩ chỉ định
                            if 'requestor' in body and body['requestor']:
                                requestor = request.env['sh.medical.physician'].sudo().search(
                                    [('employee_id.employee_code', '=', body['requestor'])])
                                if requestor:
                                    labtest.sudo().write({
                                        'requestor': requestor.id,
                                    })
                                else:
                                    return {
                                        'stage': False,
                                        'message': 'Không tìm thấy bác sĩ có mã %s, liên hệ với admin để hỗ trợ!' %
                                                   body['requestor']
                                    }

                            # check dịch vụ xét nghiệm có thông số con hay ko
                            if labtest.has_child:
                                # if len(labtest.test_type.lab_criteria) == len(body['result_lab_test']):
                                result_lab_test_list = body['result_lab_test']
                                dict_result_lab_test_list = {}
                                # tạo dict lưu giá trị kết quả xét nghiệm, key là id xét nghiệm
                                for rec_result_lab_test_list in result_lab_test_list:
                                    labtest_criteria = request.env['sh.medical.labtest.criteria'].sudo().search(
                                        [('code_labtest_criteria', '=', rec_result_lab_test_list['code'])])
                                    dict_result_lab_test_list['%s' % labtest_criteria.id] = \
                                        rec_result_lab_test_list[
                                            'result']

                                # cập nhật kết quả
                                for rec_result_lab_test_his in labtest.lab_test_criteria:
                                    id_labtest_criteria = rec_result_lab_test_his.lab_test_criteria_id.id
                                    if str(id_labtest_criteria) in dict_result_lab_test_list:
                                        rec_result_lab_test_his.write({
                                            'result': dict_result_lab_test_list['%s' % id_labtest_criteria]
                                        })

                                labtest.sudo().write({
                                    # 'doctor_note': body['doctor_conclusion'],
                                    'date_done': date_done,
                                })

                                if 'pathologist' in body and body['pathologist']:
                                    pathologist = request.env['sh.medical.physician'].sudo().search(
                                        [('employee_id.employee_code', '=', body['pathologist'])])
                                    if pathologist:
                                        labtest.write({
                                            'pathologist': pathologist.id,
                                        })

                                # check phiếu xn điền đủ KQ chưa
                                check_lab_test_criteria = 0
                                for rec_lab_test_criteria in labtest.lab_test_criteria:
                                    if rec_lab_test_criteria.result:
                                        check_lab_test_criteria += 1

                                if len(labtest.lab_test_criteria) == check_lab_test_criteria:
                                    labtest.write({
                                        'enough_results': True,
                                    })
                                # check hoàn thành phiếu
                                walkin = labtest.walkin
                                len_lab_test = len(walkin.lab_test_ids)
                                len_check = 0
                                for rec_lab_test in walkin.lab_test_ids:
                                    if rec_lab_test.enough_results:
                                        len_check += 1
                                if len_lab_test == len_check:
                                    for rec_lab_test in walkin.lab_test_ids:
                                        rec_lab_test.sudo().write({
                                            'state': 'Completed'
                                        })
                                    # mở khóa 1 phiếu XN để add vật tư tiêu hao
                                    walkin.lab_test_ids[0].sudo().write({
                                        'state': 'Test In Progress'
                                    })
                                return {
                                    'stage': True,
                                    'message': 'Cập nhật kết quả xét nghiệm thành công!'
                                }
                            # else:
                            #     return {
                            #         'stage': False,
                            #         'message': 'Kiểm tra lại số lượng thông số của xét nghiệm!!! LIST: %s thông số' % len(
                            #             body['result_lab_test'])
                            #     }
                            else:
                                if len(body['result_lab_test']) == 1:
                                    result_lab_test = body['result_lab_test'][0]
                                    labtest.sudo().write({
                                        'results': str(result_lab_test['result']),
                                        'date_done': date_done,
                                        'enough_results': True,
                                        'doctor_note': body['doctor_conclusion']
                                    })
                                    # check phiếu xn điền đủ KQ chưa
                                    check_lab_test_criteria = 0
                                    for rec_lab_test_criteria in labtest.lab_test_criteria:
                                        if rec_lab_test_criteria.result:
                                            check_lab_test_criteria += 1

                                    if len(labtest.lab_test_criteria) == check_lab_test_criteria:
                                        labtest.write({
                                            'enough_results': True,
                                        })
                                    # check hoàn thành phiếu
                                    walkin = labtest.walkin
                                    len_lab_test = len(walkin.lab_test_ids)
                                    len_check = 0
                                    for rec_lab_test in walkin.lab_test_ids:
                                        if rec_lab_test.enough_results:
                                            len_check += 1
                                    if len_lab_test == len_check:
                                        for rec_lab_test in walkin.lab_test_ids:
                                            rec_lab_test.sudo().write({
                                                'state': 'Completed'
                                            })
                                        # mở khóa 1 phiếu XN để add vật tư tiêu hao
                                        walkin.lab_test_ids[0].sudo().write({
                                            'state': 'Test In Progress'
                                        })
                                    return {
                                        'stage': True,
                                        'message': 'Cập nhật kết quả xét nghiệm thành công!'
                                    }
                                else:
                                    return {
                                        'stage': False,
                                        'message': 'Dịch vụ xét nghiệm đang truyền vào không có xét nghiệm con, kết quả xét '
                                                   'nghiệm chỉ nhận 1 đối tượng!!! '
                                    }

                        elif labtest.state == 'Draft':
                            return {
                                'stage': False,
                                'message': 'Phiếu %s đang ở trạng thái Nháp, không thể cập nhật kết quả xét nghiệm! Hãy chuyển trạng thái phiếu xét nghiệm trước!!!' % labtest.name
                            }
                        else:
                            return {
                                'stage': False,
                                'message': 'Phiếu %s đã Hoàn thành, không thể cập nhật kết quả xét nghiệm! Liên hệ ADMIN để mở lại phiếu xét nghiệm trước khi cập nhật lại kết quả xét nghiệm' % labtest.name
                            }
                    else:
                        return {
                            'stage': False,
                            'message': 'Không tìm thấy mã phiếu chỉ định trên HIS, liên hệ với admin để hỗ trợ!!!'
                        }
                else:
                    return {
                        'stage': False,
                        'message': 'Chưa truyền mã phiếu chỉ định!!!'
                    }
            else:
                # tìm phiếu xét nghiệm
                labtest = request.env['sh.medical.lab.test'].sudo().search(
                    [('name', '=', body['lab_test_code']), ('institution.his_company.code', '=', body['company'])])
                if labtest:
                    if labtest.state == 'Completed':
                        if labtest.has_child:
                            for rec_result_lab_test_his in labtest.lab_test_criteria:
                                rec_result_lab_test_his.sudo().write({
                                    'result': None,
                                })
                            labtest.sudo().write({
                                'state': 'Test In Progress',
                            })
                        else:
                            labtest.sudo().write({
                                'results': None,
                                'state': 'Test In Progress',
                            })
                        return {
                            'stage': True,
                            'message': 'Hủy kết quả xét nghiệm thành công!'
                        }
                    else:
                        return {
                            'stage': False,
                            'message': 'Phiếu %s chưa ở trạng thái Hoàn thành, không thể hủy kết quả xét nghiệm!!!' %
                                       body['lab_test_code']
                        }
                else:
                    return {
                        'stage': False,
                        'message': 'Không tìm thấy mã phiếu chỉ định trên HIS, liên hệ với admin để hỗ trợ!!!'
                    }
        else:
            return {
                'stage': False,
                'message': 'Param type chỉ nhận 2 giá trị 0 và 1!!!'
            }
