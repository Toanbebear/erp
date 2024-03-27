from odoo import api, models, fields
from odoo.addons.queue_job.job import job
from .. import common
import json
import requests


class EhcPaymentInherit(models.Model):
    _inherit = 'crm.hh.ehc.statement.payment'

    @job
    def sync_record_channel_job_update_payment(self, id):
        payment = self.sudo().browse(id)
        if payment.booking_id.collaborators_id:
            url = common.get_url()
            token = common.get_token()
            headers = {
                'authorization': token,
                'Content-Type': 'application/json'
            }
            payload = {
                "id_ehc": payment.invoice_id,
                "booking_code": payment.booking_id.name,
                "patient_code": payment.patient_code,
                "contact_name": payment.booking_id.partner_id.name,
                "phone": payment.booking_phone,
                "date": payment.invoice_date.strftime('%Y-%m-%d'),
                "amount": payment.amount_paid,
                "stage": payment.invoice_status,
                "type": payment.invoice_type,
                "method": payment.invoice_method,
            }
            response = requests.request('POST', url=url + '/api/v1/post-payment', data=json.dumps(payload), headers=headers)
        else:
            return False

    @api.model
    def create(self, vals_list):
        res = super(EhcPaymentInherit, self).create(vals_list)
        if res:
            self.sudo().with_delay(priority=0,
                                   channel='channel_job_update_payment').sync_record_channel_job_update_payment(
                id=res.id)
        return res

    def write(self, vals_list):
        res = super(EhcPaymentInherit, self).write(vals_list)
        if res and vals_list:
            self.sudo().with_delay(priority=0,
                                   channel='channel_job_update_payment').sync_record_channel_job_update_payment(
                id=self.id)
        return res
