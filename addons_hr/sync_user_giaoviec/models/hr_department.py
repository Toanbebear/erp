import json

import requests

from odoo import fields, api, models
from odoo.addons.queue_job.job import job


class HrDepartmentSector(models.Model):
    _inherit = 'hr.department.sector'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_giaoviec')
        sector_id = self.env['hr.department.sector'].sudo().browse(id)
        if sector_id:
            url = url_root + "/api/v1/sync_hr_department_sector"

            payload = json.dumps({
                "erp_id": id,
                "name": sector_id.name,
                "code": sector_id.code
            })
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)

    @api.model
    def create(self, vals):
        res = super(HrDepartmentSector, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_hr_department_sector').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(HrDepartmentSector, self).write(vals)
        if res:
            for hd in self:
                if hd.id:
                    hd.sudo().with_delay(priority=0, channel='sync_hr_department_sector').sync_record(id=hd.id)
        return res


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @job
    def sync_record(self, id):
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_giaoviec')
        department = self.env['hr.department'].sudo().browse(id)
        if department:
            url = url_root + "/api/v1/sync_hr_department"

            payload = json.dumps({
                "erp_id": id,
                'name': department.name,
                'root_code': department.root_code,
                'company_id': department.company_id.id if department.company_id else '',
                'manager_id': department.manager_id.id if department.manager_id else '',
                'sector_id': department.sector_id.id if department.sector_id else '',
                'parent_id': department.parent_id.id if department.parent_id else '',
                'active': 1 if department.active else ''
            })
            headers = {
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)

    @api.model
    def create(self, vals):
        res = super(HrDepartment, self).create(vals)
        if res:
            self.sudo().with_delay(priority=0, channel='sync_hr_department').sync_record(id=res.id)
        return res

    def write(self, vals):
        res = super(HrDepartment, self).write(vals)
        if res:
            for hd in self:
                if hd.id:
                    hd.sudo().with_delay(priority=0, channel='sync_hr_department').sync_record(id=hd.id)
        return res
