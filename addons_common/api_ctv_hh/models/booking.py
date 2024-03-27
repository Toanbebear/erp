from odoo import api, models, fields
from odoo.addons.queue_job.job import job
from .. import common
import json
import requests
import logging

_logger = logging.getLogger(__name__)


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    @job
    def sync_record_channel_job_update_crm_lead(self, id):
        hh_company = self.env.ref('shealth_all_in_one.hh_hn_nnd_company').id
        booking = self.sudo().search([('id', '=', id), ('company_id', '=', hh_company), ('type', '=', 'opportunity'),
                                      ('collaborators_id', '!=', False)])
        if booking:
            url = common.get_url() + "/api/v1/create-booking"
            token = common.get_token()
            headers = {
                'authorization': token,
                'Content-Type': 'application/json'
            }
            services = {}
            if booking.crm_line_ids:
                for rec in booking.crm_line_ids:
                    # services.update({
                    #     'id' : rec.id,
                    #     'name' : rec.service_id.name,
                    #     'quantity' : rec.quantity,
                    #     'unit_price' : rec.unit_price,
                    #     'status' : rec.service_status
                    # })
                    services[str(rec.id)] = {
                        'name': rec.service_id.name,
                        'quantity': rec.quantity,
                        'unit_price': rec.unit_price,
                        'status': rec.service_status
                    }
            value = {
                "code_collaborator": booking.collaborators_id.code_collaborators if booking.collaborators_id.code_collaborators else '',
                "name_collaborator": booking.collaborators_id.name if booking.collaborators_id.name else '',
                "phone_collaborator": booking.collaborators_id.phone if booking.collaborators_id.phone else '',
                "gender_collaborator": booking.collaborators_id.sex if booking.collaborators_id.sex else '',
                "address_collaborator": booking.collaborators_id.address if booking.collaborators_id.address else '',
                "code_booking": booking.name if booking.name else '',
                "phone": booking.phone if booking.phone else '',
                "patient_code": booking.crm_hh_ehc_medical_record_ids[
                    0].patient_code if booking.crm_hh_ehc_medical_record_ids else '',
                "partner_code": booking.partner_id.code_customer if booking.partner_id.code_customer else '',
                "partner_name": booking.partner_id.name if booking.partner_id.name else '',
                "arrival_date": booking.arrival_date.strftime("%Y-%m-%d") if booking.arrival_date else '',
                "status": booking.crm_hh_ehc_medical_record_ids[
                    0].status if booking.crm_hh_ehc_medical_record_ids else '',
                "reception_date": booking.crm_hh_ehc_medical_record_ids[
                    0].reception_date.strftime("%Y-%m-%d") if booking.crm_hh_ehc_medical_record_ids[
                    0].reception_date else '',
                "in_date": booking.crm_hh_ehc_medical_record_ids[
                    0].in_date.strftime("%Y-%m-%d") if booking.crm_hh_ehc_medical_record_ids[
                    0].in_date else '',
                "out_date": booking.crm_hh_ehc_medical_record_ids[
                    0].out_date.strftime("%Y-%m-%d") if booking.crm_hh_ehc_medical_record_ids[
                    0].out_date else '',
                "total_amount": booking.crm_hh_ehc_medical_record_ids[
                    0].amount_paid if booking.crm_hh_ehc_medical_record_ids[
                    0].amount_paid else '',
                "total_expense": booking.crm_hh_ehc_medical_record_ids[
                    0].amount_due if booking.crm_hh_ehc_medical_record_ids[
                    0].amount_due else '',
                "total_discount": booking.crm_hh_ehc_medical_record_ids[
                    0].amount_discount if booking.crm_hh_ehc_medical_record_ids[
                    0].amount_discount else '',
                "services": services
            }
            payload = json.dumps(value)
            response = requests.request('POST', url=url, data=payload, headers=headers)
            response = response.json()
        else:
            return False

    @api.model
    def create(self, vals_list):
        res = super(CrmLeadInherit, self).create(vals_list)
        if res:
            self.sudo().with_delay(priority=0,
                                   channel='channel_job_create_crm_lead').sync_record_channel_job_update_crm_lead(
                id=res.id)
            # self.sudo().sync_record_channel_job_update_crm_lead(res.id)
        return res

    def write(self, vals_list):
        res = super(CrmLeadInherit, self).write(vals_list)
        if res and vals_list:
            self.sudo().with_delay(priority=0,
                                   channel='channel_job_create_crm_lead').sync_record_channel_job_update_crm_lead(
                id=self.id)
            # self.sudo().sync_record_channel_job_update_crm_lead(self.id)
        return res
