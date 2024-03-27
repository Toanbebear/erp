import json

import requests

from odoo import fields, api, models
from odoo.addons.queue_job.job import job


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_giaoviec')
        employee_id = self.env['hr.employee'].sudo().browse(id)
        if employee_id:
            url = url_root + "/api/v1/sync_hr_employee"

            payload = json.dumps({
                'erp_id': id,
                'name': employee_id.name,
                'employee_code': employee_id.employee_code,
                'company_id': employee_id.company_id.id if employee_id.company_id else '',
                'area': employee_id.area,
                'department_id': employee_id.department_id.id if employee_id.department_id else '',
                'sector_id': employee_id.sector_id.id if employee_id.sector_id else '',
                'job_id': employee_id.job_id.id if employee_id.job_id else '',
                'staff_level': employee_id.staff_level,
                'active': 1 if employee_id.active else '',
                'parent_id': employee_id.parent_id.id if employee_id.parent_id else '',
                'gender': employee_id.gender
            })
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_hr_employee').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        if res:
            for he in self:
                if he.id:
                    he.sudo().with_delay(priority=0, channel='sync_hr_employee').sync_record(id=he.id)
        return res
