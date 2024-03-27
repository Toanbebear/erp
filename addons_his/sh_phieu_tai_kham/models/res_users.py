# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class User(models.Model):
    _inherit = ['res.users']

    # note: a user can only be linked to one employee per company (see sql constraint in ´hr.employee´)
    # employee_ids = fields.One2many('hr.employee', 'user_id', string='Related employee')
    employee_id = fields.Many2one('hr.employee', string="Company employee",
        compute='_compute_company_employee', search='_search_company_employee', store=True)
    room_ids = fields.Many2many('sh.medical.health.center.ot', 'ot_user_rel', string='Phòng')
    # Room bác sĩ phụ trách
    # 'sh.medical.health.center.ot', 'service_rooms_rel'
    # room_ids = fields.Many2many('sh.medical.health.center.ot', 'room_user_related_rel',
    #                            'user_id', 'room_id',
    #                            string='Phòng khám',
    #                            compute="_compute_room_user",
    #                            store=True,
    #                            readonly=True,
    #                            ondelete='cascade')
    #
    # def _compute_room_user(self):
    #     for record in self:
    #         physicians = self.env['sh.medical.physician'].search([('sh_user_id', '=', record.id)])
    #         # Các khoa mà bác sĩ trực thuộc
    #         if physicians:
    #
    #             for d in physicians.department:
    #
    #
    #         physicians = self.env['sh.medical.health.center.ward'].search([('sh_user_id', '=', record.id)])
    #         if record.room and record.room.department and record.room.department.physician and record.room.department.physician.sh_user_id:
    #             record.sh_user_id = [(6, 0, record.room.department.physician.sh_user_id.ids)]
    #         else:
    #             record.sh_user_id = False
    #
    # def _search_company_employee(self, operator, value):
    #     employees = self.env['hr.employee'].search([
    #         ('name', operator, value),
    #         '|',
    #         ('company_id', '=', self.env.company.id),
    #         ('company_id', '=', False)
    #     ], order='company_id ASC')
    #     return [('id', 'in', employees.mapped('user_id').ids)]
