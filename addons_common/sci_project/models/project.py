from odoo import fields, models, api


class SciProject(models.Model):
    _inherit = 'project.task'
    _description = 'SCI Project'

    department_create_uid = fields.Char(string='Bộ phận yêu cầu', compute='_get_department_create_uid')
    department_user_id = fields.Char(string='Bộ phận phụ trách thực hiện', compute='_get_department_user_id')

    @api.depends('create_uid')
    def _get_department_create_uid(self):
        for rec in self:
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            if employee:
                rec.department_create_uid = employee.department_id.name
            else:
                rec.department_create_uid = False

    @api.depends('user_id')
    def _get_department_user_id(self):
        for rec in self:
            employee = self.env['hr.employee'].search([('user_id', '=', rec.user_id.id)], limit=1)
            if employee:
                rec.department_user_id = employee.department_id.name
            else:
                rec.department_user_id = False


class SciProjectProject(models.Model):
    _inherit = 'project.project'
    _description = 'SCI Project'

    department_id = fields.Many2one(string='Phòng ban', related='user_id.employee_ids.department_id')
    department_display = fields.Char(string='Phòng ban tạo', store=True, related='department_id.name')