import json

import requests

from odoo import fields, api, models
from odoo.addons.queue_job.job import job


class HrGroupJob(models.Model):
    _inherit = 'hr.group.job'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_giaoviec')
        group_id = self.env['hr.group.job'].sudo().browse(id)
        if group_id:
            url = url_root + '/api/v1/sync_hr_group_job'

            payload = json.dumps({
                'erp_id': id,
                'name': group_id.name,
                'code': group_id.code,
                'active': 1 if group_id.active else ''
            })
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)

    @api.model
    def create(self, vals):
        res = super(HrGroupJob, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_hr_group_job').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(HrGroupJob, self).write(vals)
        if res:
            for hgj in self:
                if hgj.id:
                    hgj.sudo().with_delay(priority=0, channel='sync_hr_group_job').sync_record(id=hgj.id)
        return res


class HrJob(models.Model):
    _inherit = 'hr.job'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_giaoviec')
        job_id = self.env['hr.job'].sudo().browse(id)
        if job_id:
            url = url_root + '/api/v1/sync_hr_job'

            payload = json.dumps({
                'erp_id': id,
                'name': job_id.name,
                'company_id': job_id.company_id.id if job_id.company_id else '',
                'active': 1 if job_id.active else '',
                'employee_id': job_id.hr_responsible_id.id if job_id.hr_responsible_id else '',
                'department_id': job_id.department_id.id if job_id.department_id else ''
            })
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)

    @api.model
    def create(self, vals):
        res = super(HrJob, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_hr_job').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(HrJob, self).write(vals)
        if res:
            for hj in self:
                if hj.id:
                    hj.sudo().with_delay(priority=0, channel='sync_hr_job').sync_record(id=hj.id)
        return res
