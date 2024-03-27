from odoo import fields, models

class department(models.Model):
    _inherit = "hr.department"

    team_ids = fields.One2many('hr.team', 'department_id', string="Nhóm")
    sequence = fields.Integer('Sequence', default=20)