# -*- coding: utf-8 -*-

from odoo import fields, models


class GroupJob(models.Model):
    _name = "hr.group.job"
    _description = "Nhóm vị trí"

    name = fields.Text(string="Bộ phận")
    code = fields.Char(string='Mã bộ phận')
    active = fields.Boolean(string="Lưu trữ", default=True)
    sequence = fields.Integer('Sequence', default=20)


class HRJob(models.Model):
    _inherit = "hr.job"

    sequence = fields.Integer('Sequence', default=20)