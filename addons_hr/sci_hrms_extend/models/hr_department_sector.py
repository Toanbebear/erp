# -*- coding: utf-8 -*-
###################################################################################
from odoo import models, fields, api, _


class HrDepartmentSector(models.Model):
    _inherit = 'hr.department.sector'

    company_ids = fields.Many2many('res.company', string='Công ty')


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    company_ids = fields.Many2many('res.company', string='Công ty')
    parent_id = fields.Many2one('hr.department', string='Parent Department', index=True,
                                domain="[('company_ids', 'parent_of', company_ids), ('id', '!=', id)]",
                                ondelete='cascade')
    manager_id = fields.Many2one('hr.employee', string='Manager', tracking=True,
                                 domain="[('company_id', 'in', company_ids)]")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sector_id = fields.Many2one('hr.department.sector', string='Khối',
                                domain="[('company_ids', 'parent_of', company_id)]", readonly=False)
    department_id = fields.Many2one('hr.department', string='Phòng/Bàn',
                                    domain="[('company_ids', 'parent_of', company_id), ('sector_id', '=', sector_id)]")
    team_id = fields.Many2one('hr.team', string="Nhóm", domain="[('department_id', '=', department_id)]")

    @api.onchange('sector_id')
    def onchange_sector(self):
        self.department_id = False
        self.sector_id = False
        self.job_id = False
        self.team_id = False
