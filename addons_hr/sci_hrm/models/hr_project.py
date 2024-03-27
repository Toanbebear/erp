# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HRProject(models.Model):
    _inherit = 'project.task'

    internal = fields.Boolean('Internal')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_display_id = fields.Char(string='Người thực hiện', store=True, compute='_get_employee_default')

    @api.depends('internal', 'employee_id')
    def _get_employee_default(self):
        for rec in self:
            if not rec.internal:
                employee = self.env['hr.employee'].search([('user_id', '=', rec.user_id.id)], limit=1)
                rec.employee_display_id = employee.name
            elif rec.employee_id:
                rec.employee_display_id = rec.employee_id.name
            else:
                rec.employee_display_id = None

