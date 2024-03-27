# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class InheritEmployee(models.Model):
    _inherit = 'hr.employee'

    discipline_count = fields.Integer(compute="_compute_discipline_count")

    def _compute_discipline_count(self):
        all_actions = self.env['disciplinary.action'].read_group([
            ('employee_name', 'in', self.ids),
            ('state', '=', 'action')], fields=['employee_name'], groupby=['employee_name'])
        mapping = dict([(action['employee_name'][0], action['employee_name_count']) for action in all_actions])
        for employee in self:
            employee.discipline_count = mapping.get(employee.id, 0)

class CategoryDiscipline(models.Model):
    _name = 'discipline.category'
    _description = 'Reason Category'

    # Discipline Categories

    code = fields.Char(string="Code", required=True, help="Category code")
    name = fields.Char(string="Name", required=True, help="Category name")
    description = fields.Text(string="Mô tả", help="Details for this category")


class DisciplinaryAction(models.Model):
    _name = 'disciplinary.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Disciplinary Action"

    state = fields.Selection([
        ('draft', 'Dự Thảo'),
        ('explain', 'Giải Thích'),
        ('action', 'Xác nhận'),
        ('cancel', 'Cancelled'),

    ], default='draft', string="Trạng thái", track_visibility='onchange')

    name = fields.Char(string='Mã tham chiếu', required=True, copy=False, readonly=True,
                       default=lambda self: _('No.'))

    employee_name = fields.Many2one('hr.employee', string='Nhân viên', required=True, help="Employee name", domain="[('company_id', '=', company_id)]")
    department_name = fields.Many2one('hr.department', string='Phòng ban', readonly=True, help="Department name")
    job = fields.Many2one('hr.job', 'Chức vụ', readonly=True)
    discipline_reason = fields.Many2one('discipline.category', string='Nhóm kỷ luật', required=True, help="Choose a disciplinary reason")
    explanation = fields.Text(string="Nhân viên giải thích", help='Employee have to give Explanation'
                                                                     'to manager about the violation of discipline')
    read_only = fields.Boolean(compute="get_user", default=True)
    warning_letter = fields.Html(string="Thư cảnh báo")
    warning = fields.Integer(default=False)
    action_details = fields.Text(string="Action Details", help="Give the details for this action")
    attachment_ids = fields.Many2many('ir.attachment', string="File đính kèm",
                                      help="Employee can submit any documents which supports their explanation")
    note = fields.Text(string="Ghi chú")
    joined_date = fields.Date(string="Ngày vào làm", help="Employee joining date", readonly=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, help="Company")

    @api.onchange('employee_name')
    def set_join_date(self):
        self.joined_date = self.employee_name.joining_date if self.employee_name.joining_date else ''
        self.department_name = self.employee_name.department_id if self.employee_name.department_id else ''
        self.job = self.employee_name.job_id if self.employee_name.job_id else ''

    # assigning the sequence for the record
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('disciplinary.action')
        return super(DisciplinaryAction, self).create(vals)

    # Check the user is a manager or employee
    @api.depends('read_only')
    def get_user(self):
        if self.env.user.has_group('hr.group_hr_manager'):
            self.read_only = True
        else:
            self.read_only = False

    @api.onchange('employee_name')
    @api.depends('employee_name')
    def onchange_employee_name(self):

        department = self.env['hr.employee'].search([('name', '=', self.employee_name.name)])
        self.department_name = department.department_id.id

        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    @api.onchange('discipline_reason')
    @api.depends('discipline_reason')
    def onchange_reason(self):
        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    def assign_function(self):

        for rec in self:
            rec.state = 'explain'

    def cancel_function(self):
        for rec in self:
            rec.state = 'cancel'

    def set_to_function(self):
        for rec in self:
            rec.state = 'draft'

    def action_function(self):
        for rec in self:
            rec.state = 'action'
