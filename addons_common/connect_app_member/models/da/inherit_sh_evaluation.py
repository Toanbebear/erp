import json
import logging
from datetime import datetime, timedelta
import requests

from odoo import fields, models, api
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class InheritSHEvaluation(models.Model):
    _inherit = 'sh.medical.evaluation'

    # def set_to_completed(self):
    #     res = super(InheritSHEvaluation, self).set_to_completed()
    #     if self.institution.his_company.brand_id.code.lower() == 'da':
    #         params = self.env['ir.config_parameter'].sudo()
    #         domain = params.get_param('config_domain_app_member_da')
    #         if domain:
    #             headers = {'Content-type': 'application/json'}
    #             temp = self.get_temp_notification_reminders_evaluation()
    #             content = temp['content']
    #             # content = content.replace('[Service_name]', str(data.crm_id.crm_line_ids.service_id.mapped('name')))
    #             content = content.replace('[Service_name]', '; '.join(self.evaluation_services.mapped('name')))
    #             content = content.replace('[Date]', self.evaluation_end_date.strftime(
    #                 '%d-%m-%Y') if self.evaluation_end_date else '')
    #             content = content.replace('[Branch_name]', self.institution.his_company.name)
    #             list_service_id = []
    #             services = self.services
    #             id_service = services[0].product_id.id
    #             for rec in services:
    #                 list_service_id.append(rec.product_id.id)
    #             payload = {
    #                 "phone": self.walkin.booking_id.phone,
    #                 # "phone": "0393923233",
    #                 "content": content, "object_id": temp['object_id'],
    #                 "code_company": self.institution.his_company.code,
    #                 "notify_type": 3,
    #                 'update_course': {
    #                     "id": self.id,
    #                     "result": self.notes_complaint if self.notes_complaint else "",
    #                     "doctor": self.doctor.name if self.doctor else "",
    #                     "name": '; '.join(self.evaluation_services.mapped('name')) if self.evaluation_services else "",
    #                     "id_service": id_service if id_service else None,
    #                     "list_is_service": list_service_id if list_service_id else None,
    #                     "date": self.evaluation_end_date.strftime('%Y-%m-%d') if self.evaluation_end_date else "",
    #                     "branch": self.institution.his_company.name if self.institution.his_company else "",
    #                     "comment": self.notes_complaint if self.notes_complaint else "",
    #                     "type": "TK"
    #                 }}
    #             response = requests.post('%s/api/v1/push-noti' % domain, headers=headers,
    #                                      data=json.dumps(payload))
    #         else:
    #             pass
    #
    #     return res

    def get_account_app_member_da(self):
        params = self.env['ir.config_parameter'].sudo()
        domain = params.get_param('config_domain_app_member_da')
        headers = {'Content-type': 'application/json'}
        payload = json.dumps({})
        response = requests.get('%s/api/v1/noti/get-account' % domain, headers=headers, data=payload)
        response = response.json()
        if 'data' in response and response['data'] and int(response['status']) == 0:
            return response['data']

    # def get_temp_notification_reminders_evaluation(self):
    #     params = self.env['ir.config_parameter'].sudo()
    #     domain = params.get_param('config_domain_app_member_da')
    #     response = requests.get('%s/api/v1/noti/get-temp-evaluation-done-reminder' % domain)
    #     _logger.info(response)
    #     response = response.json()
    #     _logger.info(response)
    #     if 'data' in response and response['data'] and int(response['status']) == 0:
    #         return response['data']

    @job
    def sync_record(self, id):
        eva = self.sudo().browse(id)
        # account = self.env['account.app.member'].sudo().search([('phone', '=', eva.walkin.booking_id.phone)])
        # if account:
        brand = eva.institution.his_company.brand_id.code
        params = self.env['ir.config_parameter'].sudo()
        config_domain = 'config_domain_app_member_%s' % brand.lower()
        config_token = 'config_token_app_member_%s' % brand.lower()
        config_sync = 'sync_app_member_%s' % brand.lower()
        sync = params.get_param(config_sync)
        if sync == 'True':
            domain = params.get_param(config_domain)
            token = params.get_param(config_token)
            if domain and token:
                services = eva.services
                for service in services:
                    team_member = []
                    for member in eva.evaluation_team:
                        value_member = {
                            'doctor_name': member.team_member.name,
                            'speciality': member.team_member.speciality.name,
                            'role': member.role.name,
                            'erp_id': member.id,
                        }
                        team_member.append(value_member)
                    surgery_history_ids = []
                    for surgery_history_id in eva.surgery_history_ids:
                        value_surgery = {
                            'main_doctor': ','.join(surgery_history_id.main_doctor.mapped('name')),
                            'speciality_main_doctor': ','.join(
                                surgery_history_id.main_doctor.speciality.mapped('name')),
                            'sub_doctor': ','.join(surgery_history_id.sub_doctor.mapped('name')),
                            'service_performances': surgery_history_id.service_performances.name,
                            'speciality_sub_doctor': None,
                            'surgery_date': surgery_history_id.surgery_date.strftime(
                                "%m/%d/%Y, %H:%M:%S") if surgery_history_id.surgery_date else None,
                            'erp_id': surgery_history_id.id,
                        }
                        surgery_history_ids.append(value_surgery)
                    body = {
                        'id': eva.id,
                        'name': eva.name,
                        'walkin_id': eva.walkin.name,
                        'institution': eva.institution.his_company.code,
                        'ward': eva.ward.name,
                        'room': eva.room.name,
                        'evaluation_start_date': eva.evaluation_start_date.strftime("%m/%d/%Y, %H:%M:%S"),
                        'evaluation_end_date': eva.evaluation_end_date.strftime(
                            "%m/%d/%Y, %H:%M:%S") if eva.evaluation_end_date else None,
                        'next_appointment_date': eva.next_appointment_date.strftime(
                            "%m/%d/%Y, %H:%M:%S") if eva.next_appointment_date else None,
                        'warranty_appointment_date': eva.warranty_appointment_date.strftime(
                            "%m/%d/%Y, %H:%M:%S") if eva.next_appointment_date else None,
                        'services': service.name,
                        'patient_level': eva.patient_level,
                        'evaluation_services': service.name,
                        'doctor': eva.doctor.name,
                        'doctor_bh': eva.doctor_bh.name if eva.doctor_bh else None,
                        'chief_complaint': eva.chief_complaint,
                        'notes_complaint': eva.notes_complaint,
                        'team_member': team_member,
                        'surgery_history_ids': surgery_history_ids,
                        'id_services': service.product_id.id,
                        'state': eva.state
                    }

                    url = domain + '/api/v1/sync-evaluation'
                    headers = {
                        'Authorization': token,
                        'Content-Type': 'application/json'
                    }
                    response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    @api.model
    def create(self, vals):
        res = super(InheritSHEvaluation, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_app_member_eva').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(InheritSHEvaluation, self).write(vals)
        if res:
            for evaluation in self:
                if evaluation.id:
                    evaluation.sudo().with_delay(priority=0, channel='sync_app_member_eva').sync_record(id=evaluation.id)
        return res
