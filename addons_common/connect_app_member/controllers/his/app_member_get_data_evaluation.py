# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import datetime
from odoo.addons.connect_app_member.controllers.app_member_common import app_member_validate_token, response
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)


class GetDataValuationAppMemberController(http.Controller):
    @app_member_validate_token
    @http.route("/api/app-member/v1/get-evaluation", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_evaluation_app_member(self, **payload):
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
            evaluation_ids = partner.evaluation_ids
            for evaluation_id in evaluation_ids:
                center_service = evaluation_id.services
                if evaluation_id.institution.his_company.brand_id.code == body['brand_code'].upper():
                    for ret in center_service:
                        value = {
                            'id': evaluation_id.id,
                            'state': evaluation_id.state,
                            'name': evaluation_id.name,
                            'walkin': evaluation_id.walkin.name,
                            'institution': evaluation_id.institution.his_company.code,
                            'patient_level': evaluation_id.patient_level,
                            'services': ret.product_id.name,
                            'id_services': ret.product_id.id,
                            'ward': evaluation_id.ward.name,
                            'room': evaluation_id.room.name,
                            'next_appointment_date': evaluation_id.next_appointment_date if evaluation_id.next_appointment_date else '',
                            'doctor_bh': evaluation_id.doctor_bh if evaluation_id.doctor_bh else '',
                            'warranty_appointment_date': evaluation_id.warranty_appointment_date,
                            'chief_complaint': evaluation_id.chief_complaint if evaluation_id.chief_complaint else '',
                            'doctor': evaluation_id.doctor.name,
                            'evaluation_services': ','.join(evaluation_id.evaluation_services.mapped('name')),
                            'notes_complaint': evaluation_id.notes_complaint,
                            'evaluation_start_date': evaluation_id.evaluation_start_date,
                            'evaluation_end_date': evaluation_id.evaluation_end_date
                        }
                        team_member = []
                        for member in evaluation_id.evaluation_team:
                            value_member = {
                                'doctor_name': member.team_member.name,
                                'speciality': member.team_member.speciality.name,
                                'role': member.role.name,
                                'service_performances': ','.join(member.service_performances.mapped('name')),
                            }
                            team_member.append(value_member)
                        value['team_member'] = team_member

                        surgery_history_ids = []
                        for surgery_history_id in evaluation_id.surgery_history_ids:
                            if surgery_history_id.service_performances.name == ret.product_id.name:
                                value_surgery_history = {
                                    'main_doctor': surgery_history_id.main_doctor.mapped('name'),
                                    'speciality_main_doctor': surgery_history_id.main_doctor.speciality.name,
                                    'sub_doctor': surgery_history_id.sub_doctor.name,
                                    'speciality_sub_doctor': surgery_history_id.sub_doctor.speciality.name,
                                    'surgery_date': surgery_history_id.surgery_date,
                                    'service_performances': surgery_history_id.service_performances.name,
                                }
                                surgery_history_ids.append(value_surgery_history)
                        value['surgery_history_ids'] = surgery_history_ids
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
    @http.route("/api/app-member/v1/get-evaluation-1", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_evaluation_app_member_1(self, **payload):
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
            evaluation_ids = partner.evaluation_ids
            for evaluation_id in evaluation_ids:
                center_service = evaluation_id.services
                if evaluation_id.institution.his_company.brand_id.code == body['brand_code'].upper():
                    for ret in center_service:
                        value = {
                            'id': evaluation_id.id,
                            'state': evaluation_id.state,
                            'name': evaluation_id.name,
                            'walkin': evaluation_id.walkin.name,
                            'institution': evaluation_id.institution.his_company.code,
                            'patient_level': evaluation_id.patient_level,
                            'services': ret.product_id.name,
                            'id_services': ret.product_id.id,
                            'ward': evaluation_id.ward.name,
                            'room': evaluation_id.room.name,
                            'next_appointment_date': evaluation_id.next_appointment_date if evaluation_id.next_appointment_date else '',
                            'doctor_bh': evaluation_id.doctor_bh if evaluation_id.doctor_bh else '',
                            'warranty_appointment_date': evaluation_id.warranty_appointment_date,
                            'chief_complaint': evaluation_id.chief_complaint if evaluation_id.chief_complaint else '',
                            'doctor': evaluation_id.doctor.name,
                            'evaluation_services': ','.join(evaluation_id.evaluation_services.mapped('name')),
                            'notes_complaint': evaluation_id.notes_complaint,
                            'evaluation_start_date': evaluation_id.evaluation_start_date,
                            'evaluation_end_date': evaluation_id.evaluation_end_date
                        }
                        team_member = []
                        for member in evaluation_id.evaluation_team:
                            value_member = {
                                'doctor_name': member.team_member.name,
                                'speciality': member.team_member.speciality.name,
                                'role': member.role.name,
                                'service_performances': ','.join(member.service_performances.mapped('name')),
                                'erp_id': member.id,
                            }
                            team_member.append(value_member)
                        value['team_member'] = team_member

                        surgery_history_ids = []
                        for surgery_history_id in evaluation_id.surgery_history_ids:
                            if surgery_history_id.service_performances.name == ret.product_id.name:
                                value_surgery_history = {
                                    'main_doctor': ','.join(surgery_history_id.main_doctor.mapped('name')),
                                    'speciality_main_doctor': ','.join(
                                        surgery_history_id.main_doctor.speciality.mapped('name')),
                                    'sub_doctor': ','.join(surgery_history_id.sub_doctor.mapped('name')),
                                    'speciality_sub_doctor': ','.join(
                                        surgery_history_id.sub_doctor.speciality.mapped('name')),
                                    'surgery_date': surgery_history_id.surgery_date,
                                    'service_performances': surgery_history_id.service_performances.name,
                                    'erp_id': surgery_history_id.id,
                                }
                                surgery_history_ids.append(value_surgery_history)
                        value['surgery_history_ids'] = surgery_history_ids
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
    @http.route("/api/app-member/v1/get-consultation", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_consultation_app_member(self, **payload):
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
            crm_ids = partner.crm_ids
            for crm_id in crm_ids:
                if crm_id.company_id.brand_id.code == body['brand_code'].upper():
                    for ticket in crm_id.consultation_ticket_ids:
                        for advise in ticket:
                            for rec in advise.consultation_detail_ticket_ids:
                                value = {
                                    'id': crm_id.id,
                                    'name': advise.name,
                                    'service': rec.service_id.name,
                                    'id_service': rec.service_id.product_id.id,
                                    'price': rec.service_id.product_id.list_price,
                                    'schedule': rec.schedule,
                                    'state_customer': rec.health_status,
                                    'required_customer': rec.desire,
                                    'service_date_advise': rec.create_date,
                                    'branch': crm_id.company_id.code,
                                    'doctor': advise.sh_medical_physician_id.name,
                                    'reception': advise.consultation_reception.name
                                }
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
                'data': None
            }

    @app_member_validate_token
    @http.route("/api/app-member/v1/get-sale-order", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_sale_order(self, **payload):
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
            sale_orders = request.env['sale.order'].sudo().search(
                [('partner_id', '=', partner.id), ('state', '=', 'sale')])
            for sale_order in sale_orders:
                if sale_order.brand_id.code == body['brand_code'].upper():
                    for order_line in sale_order.order_line:
                        for rec in order_line:
                            value = {
                                'name': rec.product_id.name,
                                'id_service': rec.product_id.id,
                                'order_line_id': rec.id,
                                'so': sale_order.name,
                                'date': sale_order.date_order,
                                'price': rec.price_subtotal,
                                'phone': sale_order.phone_customer
                            }
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
