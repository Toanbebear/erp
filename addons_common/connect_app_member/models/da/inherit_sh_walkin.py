import json
import logging
from datetime import datetime, timedelta
import requests

from odoo import fields, models, api
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class InheritSHWalkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    # def set_to_completed(self):
    #     res = super(InheritSHWalkin, self).set_to_completed()
    #     if self.institution.his_company.brand_id.code.lower() == 'da':
    #         params = self.env['ir.config_parameter'].sudo()
    #         domain = params.get_param('config_domain_app_member_da')
    #         if domain:
    #             headers = {'Content-type': 'application/json'}
    #             temp = self.get_temp_notification_reminders_evaluation()
    #             content = temp['content']
    #             # content = content.replace('[Service_name]', str(data.crm_id.crm_line_ids.service_id.mapped('name')))
    #             content = content.replace('[Service_name]', '; '.join(self.service.mapped('name')))
    #             content = content.replace('[Date]', self.service_date_start.strftime(
    #                 '%d-%m-%Y') if self.service_date_start else '')
    #             content = content.replace('[Branch_name]', self.institution.his_company.name)
    #             service = self.service
    #             list_id_service = []
    #             services = self.service
    #             id_services = services[0].product_id.id
    #             for rec in service:
    #                 id_service = rec.product_id.id
    #                 list_id_service.append(id_service)
    #             payload = {
    #                 "phone": self.booking_id.phone,
    #                 "content": content, "object_id": temp['object_id'],
    #                 "code_company": self.institution.his_company.code,
    #                 "notify_type": 3,
    #                 'update_course': {
    #                     "id": self.id,
    #                     "result": self.note if self.note else "",
    #                     "doctor": self.doctor.name if self.doctor else "",
    #                     "name": '; '.join(self.service.mapped('name')) if self.service else "",
    #                     "id_service": id_services if id_services else None,
    #                     "list_id_service": list_id_service if list_id_service else None,
    #                     "date": self.service_date_start.strftime('%Y-%m-%d') if self.service_date_start else "",
    #                     "branch": self.institution.his_company.name if self.institution.his_company else "",
    #                     "comment": self.note if self.note else "",
    #                     "type": "PK"
    #                 }}
    #             response = requests.post('%s/api/v1/push-noti' % domain, headers=headers,
    #                                      data=json.dumps(payload))
    #         else:
    #             pass
    #     return res

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
        walkin = self.sudo().browse(id)
        # account = self.env['account.app.member'].sudo().search([('phone', '=', walkin.booking_id.phone)])
        # if account:
        brand = walkin.institution.his_company.brand_id.code
        params = self.env['ir.config_parameter'].sudo()
        config_sync = 'sync_app_member_%s' %brand.lower()
        config_domain = 'config_domain_app_member_%s' % brand.lower()
        config_token = 'config_token_app_member_%s' % brand.lower()
        domain = params.get_param(config_domain)
        token = params.get_param(config_token)
        sync = params.get_param(config_sync)
        if sync == 'True':
            date = walkin.date.strftime("%m/%d/%Y")
            service_date = walkin.service_date.strftime("%m/%d/%Y")
            service_date_start = walkin.service_date_start.strftime("%m/%d/%Y") if walkin.service_date_start else None
            services = walkin.service
            for service in services:
                reexam_data = []
                for reexam_id in walkin.reexam_ids:
                    if reexam_id.state == 'Confirmed':
                        reexam_line_ids_data = []
                        for reexam_line in reexam_id.days_reexam_print:
                            type_reexam = reexam_line.type
                            if type_reexam not in ["Check", "Check1", "Check2", "Check3", "Check4", "Check5", "Check6",
                                                   "Check7", "Check8"]:
                                reexam_line_id_data = {
                                    'name': reexam_line.name,
                                    'type': reexam_line.type,
                                    'date_recheck': reexam_line.date_recheck_print.strftime("%m/%d/%Y"),
                                    'for_services': reexam_line.for_service,
                                    'id_services': service.product_id.id,
                                    'erp_id': reexam_line.id
                                }
                                reexam_line_ids_data.append(reexam_line_id_data)
                        reexam_value = {
                            'name_reexam': reexam_id.name,
                            'company_reexem': reexam_id.company.code,
                            'date_reexam': reexam_id.date.strftime("%m/%d/%Y"),
                            'date_out_reexam': reexam_id.date_out.strftime("%m/%d/%Y"),
                            'reexam_ids': reexam_line_ids_data,
                            'info_take_care': reexam_id.info,
                            'walkin': reexam_id.walkin.name,
                            'state': reexam_id.state,
                            'id_services': service.product_id.id,
                            'erp_id': reexam_id.id
                        }
                        reexam_data.append(reexam_value)
                body = {
                    'id': walkin.id,
                    'name': walkin.name,
                    'booking': walkin.booking_id.name,
                    'phone': walkin.booking_id.phone,
                    'institution': walkin.institution.his_company.code,
                    'service_room': walkin.service_room.name,
                    'date': date,
                    'service_date': service_date,
                    'service_date_start': service_date_start,
                    'reason_check': walkin.reason_check,
                    'services': service.name,
                    'pathological_process': walkin.pathological_process,
                    'info_diagnosis': walkin.info_diagnosis,
                    'note': walkin.note,
                    'doctor': walkin.doctor.name,
                    'id_services': service.product_id.id,
                    'state': walkin.state,
                    'reexam_ids': reexam_data,
                }
                url = domain + '/api/v1/sync-walkin'
                headers = {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                }
                response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)

    @api.model
    def create(self, vals):
        res = super(InheritSHWalkin, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_app_member_walkin').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(InheritSHWalkin, self).write(vals)
        if res:
            for walkin in self:
                if walkin.id:
                    walkin.sudo().with_delay(priority=0, channel='sync_app_member_walkin').sync_record(id=walkin.id)
        return res
