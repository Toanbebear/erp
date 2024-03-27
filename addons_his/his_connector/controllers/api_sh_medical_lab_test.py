from calendar import monthrange
from datetime import date, timedelta, datetime
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
    valid_response_once
)
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ShMedicalLabTest83Controller(http.Controller):

    @http.route("/api/83/v1/get-lab-test-ids/<phone>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_lab_test_ids(self, phone=None, **payload):
        if phone:
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
            if partner:
                patient = request.env['sh.medical.patient'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                if patient:
                    lab_test_ids = request.env['sh.medical.lab.test'].sudo().search(
                        [('patient', '=', patient.id), ('state', '=', 'Completed')])
                    if lab_test_ids:
                        data = []
                        for lab_test_id in lab_test_ids:
                            data.append({
                                'walkin_id': lab_test_id.walkin.id,
                                'walkin_name': lab_test_id.walkin.name,
                                'lab_test_id': lab_test_id.id,
                                'lab_test_name': lab_test_id.name,
                            })
                        return valid_response(data)
                    else:
                        return valid_response([])
                else:
                    return invalid_response("ERROR", "Khong tim thay benh nhan !!!")
            else:
                return invalid_response("ERROR", "Khong tim thay khach hang !!!")
        else:
            return invalid_response("ERROR", "Khong nhan duoc so dien thoai !!!")

    @http.route("/api/83/v1/get-lab-test/<id>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_lab_test(self, id=None, **payload):
        if id:
            lab_test = request.env['sh.medical.lab.test'].sudo().browse(int(id))
            if lab_test:
                data = {
                    'id': lab_test.id,
                    'name': lab_test.name if lab_test.name else '',
                    'requestor_code': lab_test.requestor.employee_id.employee_code if lab_test.requestor else '',
                    'requestor_name': lab_test.requestor.employee_id.name if lab_test.requestor else '',
                    'pathologist_code': lab_test.pathologist.employee_id.employee_code if lab_test.pathologist else '',
                    'pathologist_name': lab_test.pathologist.employee_id.name if lab_test.pathologist else '',
                    'date_requested': lab_test.date_requested.strftime(
                        '%Y-%m-%d %H:%M:%S') if lab_test.date_requested else '',
                    'date_analysis': lab_test.date_analysis.strftime(
                        '%Y-%m-%d %H:%M:%S') if lab_test.date_analysis else '',
                    'date_done': lab_test.date_done.strftime('%Y-%m-%d %H:%M:%S') if lab_test.date_done else '',
                    'abnormal': lab_test.abnormal,
                }
                lab_test_cases = []
                for ltc in lab_test.lab_test_criteria:
                    lab_test_cases.append({
                        'name': ltc.name,
                        'result': ltc.result if ltc.result else '',
                        'normal_range': ltc.normal_range if ltc.normal_range else '',
                        'abnormal': ltc.abnormal if ltc.abnormal else '',
                        'units': ltc.units.name if ltc.units else '',
                    })
                data['lab_test_cases'] = lab_test_cases

                materials = []
                materials_code = []
                for material in lab_test.lab_test_material_ids:
                    materials.append({
                        'product_name': material.product_id.name if material.product_id else '',
                        'product_code': material.product_id.default_code if material.product_id else '',
                        'init_quantity': material.init_quantity if material.init_quantity else '',
                        'quantity': material.quantity if material.quantity else '',
                        'uom_id': material.uom_id.name if material.uom_id else '',
                        'notes': material.notes if material.notes else '',
                    })
                    if material.product_id and material.product_id.default_code:
                        materials_code.append(material.product_id.default_code)
                data['materials'] = materials
                data['materials_code'] = materials_code
                data['results'] = lab_test.results if lab_test.results else ''
                return valid_response_once(data)
            else:
                return invalid_response("ERROR", "Khong tim thay phieu xet nghiem co id = %s !!!" % id)
        else:
            return invalid_response("ERROR", "Khong nhan duoc id !!!")
