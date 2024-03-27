# -*- coding: utf-8 -*-

from odoo import fields, models

class team(models.Model):
    _name = "hr.team"
    _description = "Nhóm"

    name = fields.Text(string="Nhóm")
    department_id = fields.Many2one('hr.department', string="Phòng ban")
    employee_id = fields.Many2one('hr.employee', string="Nhân viên")
    active = fields.Boolean(string="Lưu trữ", default=True)
    sequence = fields.Integer('Sequence', default=20)



