from calendar import monthrange
from datetime import date, timedelta, datetime
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
    valid_response_once,
)
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ShMedicalSurgery83Controller(http.Controller):

    @http.route("/api/83/v1/get-surgery-ids/<phone>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_surgery_ids(self, phone=None, **payload):
        if phone:
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
            if partner:
                patient = request.env['sh.medical.patient'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                if patient:
                    surgery_ids = request.env['sh.medical.surgery'].sudo().search([('patient', '=', patient.id), ('state', '=', 'Done')])
                    if surgery_ids:
                        data = []
                        for surgery_id in surgery_ids:
                            data.append({
                                'walkin_id': surgery_id.walkin.id,
                                'walkin_name': surgery_id.walkin.name,
                                'surgery_id': surgery_id.id,
                                'surgery_name': surgery_id.name,
                                'service_patient_erp': ', '.join(surgery_id.services.mapped('name')),
                                'name_patient_erp': surgery_id.patient.name + '' + '-' + '' + (surgery_id.patient.birth_date and surgery_id.patient.birth_date.strftime('%Y') or ''),
                                'surgery_date': surgery_id.surgery_date,
                            })
                        return valid_response(data)
                    else:
                        return valid_response([])
                else:
                    return invalid_response("ERROR", "Khong tim thay benh nhan !!!")
            else:
                return invalid_response("ERROR", "Khong tim thay khach hang !!!")
        else:
            return invalid_response("ERROR", "Khong tim thay so dien thoai !!!")

    @http.route("/api/83/v1/get-surgery/<id>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_surgery(self, id=None, **payload):
        if id:
            surgery = request.env['sh.medical.surgery'].sudo().browse(int(id))
            if surgery:
                data = {
                    'id': surgery.id,
                    'name': surgery.name,
                    'date_requested': surgery.date_requested.strftime('%Y-%m-%d %H:%M:%S') if surgery.date_requested else '',
                    'surgery_date': surgery.surgery_date.strftime('%Y-%m-%d %H:%M:%S') if surgery.surgery_date else '',
                    'surgery_end_date': surgery.surgery_end_date.strftime('%Y-%m-%d %H:%M:%S') if surgery.surgery_end_date else '',
                    'surgery_length': surgery.surgery_length if surgery.surgery_length else '',
                    'surgeon_code': surgery.surgeon.employee_id.employee_code if surgery.surgeon else '',
                    'surgeon_name': surgery.surgeon.employee_id.name if surgery.surgeon else '',
                    'anesthetist_code': surgery.anesthetist.employee_id.employee_code if surgery.anesthetist else '',
                    # 'anesthetist_type': dict(surgery._fields['anesthetist_type'].selection).get(surgery.anesthetist_type),
                    'anesthetist_type':  surgery.anesthetist_type if surgery.anesthetist_type else '',
                    'anesthetist_name': surgery.anesthetist.employee_id.name if surgery.anesthetist else '',
                    'pathology_code': surgery.pathology.code if surgery.pathology else '',
                    'pathology_name': surgery.pathology.name if surgery.pathology else '',
                    'surgery_type': surgery.surgery_type if surgery.surgery_type else '',
                }

                supplies = []
                supplies_code = []
                for sup in surgery.supplies:
                    if sup.supply.default_code:
                        supplies_code.append(sup.supply.default_code)
                    supplies.append({
                        'supply_name': sup.supply.name_use if sup.supply else '',
                        'supply_code': sup.supply.default_code if sup.supply else '',
                        'qty_used': sup.qty_used if sup.qty_used else '',
                        'uom': sup.uom_id.name if sup.uom_id else '',
                    })
                data['supplies'] = supplies
                data['supplies_code'] = supplies_code

                return valid_response_once(data)
            else:
                return invalid_response("ERROR", "Khong tim thay phieu thu thuat co id = %s !!!" % id)
        else:
            return invalid_response("ERROR", "Khong nhan duoc id !!!")