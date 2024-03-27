# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, datetime, date
from dateutil import relativedelta


class JobWelfare(models.Model):
    _name = "hr.job.welfare"
    _description = 'Human Resource job welfare'

    name = fields.Char("Name", required=True)
    icon = fields.Char("Icon", required=True)
    color = fields.Integer(string='Color Index', default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class JobPosition(models.Model):
    _name = "hr.job.position"
    _description = 'Human resource job position'

    name = fields.Char("Name", required=True)
    group_id = fields.Many2one('hr.group.job', string='Bộ phận', help='Chọn bộ phận nhóm vị trí', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name,group_id)', "Tên của chức vụ đã tồn tại trong bộ phận!"),
    ]


class HRJob(models.Model):
    _inherit = 'hr.job'

    position_id = fields.Many2one('hr.job.position', string='Chức vụ')
    address_location = fields.Text(string='Địa điểm làm việc')
    total_payroll = fields.Integer(string='Tổng định biên', default=1,
                                   groups='hr_recruitment.group_hr_recruitment_manager')
    point_kpi = fields.Float('Hệ số điểm', digits=(16, 1), default=1,
                             groups='hr_recruitment.group_hr_recruitment_manager')
    group_job = fields.Many2one('hr.group.job', string='Bộ phận', help='Chọn bộ phận nhóm vị trí',
                                related='position_id.group_id', store=True)
    categ_ids = fields.Many2many('hr.applicant.category', string="Job tags")
    welfare_ids = fields.Many2many('hr.job.welfare', string="Phúc lợi")
    date_open = fields.Date("Từ Ngày", default=fields.Date.today())
    date_closed = fields.Date("Đến Ngày")
    type_id = fields.Many2one('hr.recruitment.degree', "Bằng Cấp")
    experience = fields.Selection(
        [('0', 'Chưa có kinh nghiệm'), ('1', 'Có kinh nghiệm'), ('2', 'Không yêu cầu kinh nghiệm')], default='1')
    experience_from = fields.Float("Years", digits=(16, 1))
    experience_to = fields.Float("Years", digits=(16, 1))
    salary_type = fields.Selection([('usd', 'USD'), ('vnd', 'VNĐ'), ('ltt', 'Lương thỏa thuận'), ('lct', 'Cạnh tranh')],
                                   default='vnd')
    salary_proposed = fields.Integer("Proposed Salary")
    salary_proposed_extra = fields.Integer("Proposed Salary Extra")
    job_industry = fields.Many2one('hr.industry.job', "Ngành nghề")
    hr_responsible_id = fields.Many2one('hr.employee', 'Quản lý',
                                        domain="[('department_id', 'child_of', department_id)]")
    description = fields.Html(string='Job Description')
    req_job = fields.Html(string='Job requirements')

    state = fields.Selection(default='open', compute='_get_state', compute_sudo=False, store=True)
    website_published = fields.Boolean(compute='_get_state', compute_sudo=False)
    is_published = fields.Boolean(compute='_get_state', compute_sudo=False, store=True)
    no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
                                       help='Number of new employees you expect to recruit.', default=0)

    no_of_recruitment2 = fields.Integer(string='Nhân sự thiếu', compute='_get_no_of_recruitment', store=True)
    ratio = fields.Integer(string='Tỷ lệ(%)', compute='get_ratio', digits=(16, 2))

    periods = fields.One2many('hr.recruitment.period', 'job_position', 'Recruitment history')

    emp_ids_2 = fields.Many2many('hr.employee', 'sci_emp_job_rel', 'emp_id', 'job_id', 'Nhân viên kiêm nhiệm')

    # fields for reporting, should be remove if report template is made
    no_of_employee_at_time = fields.Integer('Employee at time', compute='_get_employee_moves')
    employees_in = fields.Integer('Employees move in', compute='_get_employee_moves')
    employees_out = fields.Integer('Employees move out', compute='_get_employee_moves')
    employees_out_name = fields.Char('NS nghỉ - ngày nghỉ', compute='_get_employee_moves')
    no_of_employee_name = fields.Char("NS nhận - ngày nhận", compute='compute_employees_name')
    employees_kn = fields.Char('NS kiêm nhiệm', compute='compute_employee_kn')

    job_source = fields.One2many('hr.recruitment.source', 'job_id', 'Nguồn tuyển dụng')
    highlight = fields.Boolean(string="Tin nổi bật", default=False)
    # root_department = fields.Many2one('hr.department.brand', string="Khối (Thương hiệu)",
    #                         related='department_id.root_parent', store=True)
    root_department = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id',
                                      store=True)

    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('name_company_uniq', 'Check(1=1)', 'The name of the job position must be unique per department in company!'),
    ]

    @api.constrains('no_of_employee', 'total_payroll')
    def change_state(self):
        for item in self:
            if item.total_payroll == item.no_of_employee:
                item.state = 'open'

    def name_get(self):
        return [
            (template.id, '%s%s' % (template.group_job.name and '[%s] ' % template.group_job.name or '', template.name))
            for template in self.sudo()]

    @api.depends('no_of_recruitment', 'employee_ids.job_id', 'emp_ids_2', 'employee_ids.active')
    def _compute_employees(self):
        employee_data = self.env['hr.employee'].read_group([('job_id', 'in', self.ids)], ['job_id'], ['job_id'])
        result = dict((data['job_id'][0], data['job_id_count']) for data in employee_data)
        for job in self:
            job.no_of_employee = result.get(job.id, 0) + len(job.emp_ids_2)
            job.expected_employees = job.no_of_employee + job.no_of_recruitment

    @api.depends('no_of_employee_name')
    def compute_employees_name(self):
        for job in self:
            employee_data = self.env['hr.employee'].search([('job_id', '=', job.id)])
            st = ""
            for data in employee_data:
                if st == "":
                    st += data.name
                    if data.joining_date: st += " - " + str(datetime.strftime(data.joining_date, '%d-%m-%Y'))
                else:
                    st += "; " + data.name
                    if data.joining_date: st += " - " + str(datetime.strftime(data.joining_date, '%d-%m-%Y'))
            job.no_of_employee_name = st

    @api.depends('employees_kn')
    def compute_employee_kn(self):
        for job in self:
            employee_data = self.env['hr.employee'].search([('job_ids', 'in', job.id)])
            st = ""
            for data in employee_data:
                if st == "":
                    st += data.name
                else:
                    st += "; " + data.name
            job.employees_kn = st

    @api.constrains('salary_proposed', 'salary_proposed_extra')
    def _check_salary_value(self):
        for item in self:
            if item.salary_proposed_extra < item.salary_proposed:
                raise ValidationError("Mức lương đề xuất không hợp lệ!!!")

    @api.constrains('experience_from', 'experience_to')
    def _check_value(self):
        for item in self:
            if item.experience_to < item.experience_from:
                raise ValidationError("Yêu cầu kinh nghiệm không hợp lệ!!!")

    @api.onchange('department_id')
    def _onchange_department(self):
        self.hr_responsible_id = self.department_id.manager_id

    @api.onchange('position_id')
    def _onchange_position_id(self):
        self.name = self.position_id.name

    def _get_employee_moves(self):
        at_date = self.env.context.get('employee_at_date')
        for record in self:
            if at_date:
                employee_out_data = self.env['hr.resignation'].search(
                    [('expected_revealing_date', '>=', at_date), ('state', '=', 'approved'), ('job', '=', record.id)])
                record.employees_out = len(employee_out_data)
                record.employees_in = self.env['hr.employee'].search_count(
                    [('joining_date', '>=', at_date), ('job_id', '=', record.id)])
                record.no_of_employee_at_time = record.no_of_employee + record.employees_out - record.employees_in
                st = ""
                for data in employee_out_data:
                    if st == "":
                        st += data.employee_id.name
                        if data.expected_revealing_date:
                            st += " - " + str(datetime.strftime(data.expected_revealing_date, '%d-%m-%Y'))
                    else:
                        st += "; " + data.employee_id.name
                        if data.expected_revealing_date:
                            st += " - " + str(datetime.strftime(data.expected_revealing_date, '%d-%m-%Y'))
                record.employees_out_name = st
            else:
                record.employees_in = 0
                record.employees_out = 0
                record.no_of_employee_at_time = record.no_of_employee

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(HRJob, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                            lazy=lazy)
        for line in res:
            jobs = self.env['hr.job']
            if '__domain' in line:
                jobs = self.search(line['__domain'])
            if 'employees_in' in fields:
                line['employees_in'] = sum(jobs.mapped('employees_in'))
            if 'employees_out' in fields:
                line['employees_out'] = sum(jobs.mapped('employees_out'))
            if 'no_of_employee_at_time' in fields:
                line['no_of_employee_at_time'] = sum(jobs.mapped('no_of_employee_at_time'))
            # if 'ratio' in fields:
            #     line['ratio'] = sum(jobs.mapped('ratio'))
        return res

    @api.depends('periods', 'periods.end_date')
    def _get_state(self):
        # Todo: check back later with HR to see if they want to auto close recruitment or not
        for record in self:
            if not record.periods:
                record.state = 'open'
                record.website_published = False
                record.is_published = False
            elif record.periods and record.periods[-1].end_date and (
                    record.periods[-1].end_date < datetime.now().date()):
                record.state = 'open'
                record.website_published = False
                record.is_published = False
            else:
                record.state = 'recruit'
                record.website_published = True
                record.is_published = True

    @api.depends('no_of_employee', 'total_payroll')
    def _get_no_of_recruitment(self):
        for record in self:
            record.no_of_recruitment2 = record.total_payroll - record.no_of_employee

    @api.depends('no_of_employee', 'no_of_recruitment2')
    def get_ratio(self):
        for record in self:
            if record.total_payroll != 0 and record.no_of_recruitment2 != 0:
                record.ratio = record.no_of_recruitment2 / record.total_payroll * 100
            else:
                record.ratio = 0

    @api.constrains('point_kpi')
    def _check_number(self):
        for record in self:
            number = record.point_kpi
            if number and number < 0:
                raise ValidationError('Hệ số điểm phải > 0')

    @api.onchange('department_id')
    def _onchange_address_full(self):
        if self.department_id:
            self.address_location = self.department_id.address_location

    def start_recruitment_period(self):
        self.ensure_one()
        if self.state == 'open':
            if self.no_of_employee >= self.total_payroll:
                raise UserError(_('Number of employees is at limit.'))
            if self.periods.filtered(lambda p: p.start_date == fields.date.today()):
                self.periods.filtered(lambda p: p.start_date == fields.date.today()).sudo().unlink()
            return {
                'name': _('Start recruitment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.recruitment.period',
                'view_id': self.env.ref('sci_hrms.hr_recruitment_period_popup').id,
                'target': 'new',
                'context': {'default_job_position': self.id},
            }

    # @api.one
    def end_recruitment_period(self):
        for item in self:
            if item.state == 'recruit':
                item.write({'state': 'open',
                            'website_published': False})
                if item.periods and not item.periods[-1].end_date:
                    item.periods[-1].sudo().write({'end_date': fields.Date.today()})

    def _compute_application_count(self):
        if self._context.get('is_recruitment'):
            read_group_result = self.env['hr.applicant'].read_group([('job_id', 'in', self.ids), ('emp_id', '=', None)],
                                                                    ['job_id'], ['job_id'])
            result = dict((data['job_id'][0], data['job_id_count']) for data in read_group_result)
            for job in self:
                job.application_count = result.get(job.id, 0)
        else:
            super(HRJob, self)._compute_application_count()


class GroupJob(models.Model):
    _name = "hr.group.job"
    _description = "Nhóm vị trí"

    name = fields.Text(string="Bộ phận")
    code = fields.Char(string='Mã bộ phận')


class IndustryJob(models.Model):
    _name = "hr.industry.job"
    _description = "Ngành nghề"

    name = fields.Text(string="Ngành nghề")


class EmployeeEntryDocuments(models.Model):
    _inherit = 'employee.checklist'

    group_job_ids = fields.Many2many('hr.group.job', string="Bộ phận")


class RecruitmentPeriod(models.Model):
    _name = "hr.recruitment.period"
    _description = 'Recruitment history'

    job_position = fields.Many2one('hr.job', 'Job position', ondelete='cascade')
    department = fields.Many2one('hr.department', 'Department', related='job_position.department_id')
    start_date = fields.Date('Start date', default=datetime.now().date())
    end_date = fields.Date('End date', default=datetime.now().date() + relativedelta.relativedelta(months=+1))
    expected_recruitment = fields.Integer('Expected recruitment', default=1)
    applicants = fields.One2many('hr.applicant', 'recruit_period', 'Applicants', context={'active_test': False})
    applicants_num = fields.Integer('Number of applicants', compute='_get_nums', store=True)
    employees_num = fields.Integer('Hired employees', compute='_get_nums', store=True)
    success_rate = fields.Float('Success rate', compute='_get_nums', store=True, group_operator='avg')
    to_recruit = fields.Integer('To recruit')
    _sql_constraints = [
        ('_recruitment_period_start_before_end', 'check (end_date > start_date)',
         'Ngày bắt đầu phải nhỏ hơn ngày kết thúc.')
    ]

    # @api.multi
    def name_get(self):
        return [(record.id, record.job_position.name + ' - ' + record.start_date.strftime('%d/%m/%Y')) for record in
                self]

    @api.depends('applicants', 'applicants.emp_id')
    def _get_nums(self):
        for record in self:
            record.applicants_num = len(record.applicants)
            record.employees_num = len(record.applicants.filtered(lambda a: a.emp_id))
            record.success_rate = record.employees_num / record.expected_recruitment * 100 if record.applicants_num > 0 else 0

    @api.depends('employees_num', 'expected_recruitment')
    def _get_end_date(self):
        for record in self:
            if record.employees_num == record.expected_recruitment:
                record.end_date = fields.Date.today()
                # self.env['hr.job'].sudo().browse(self.job_position.id).write({'state': 'open'})
                # self.job_position.state = 'open'

    @api.constrains('expected_recruitment')
    def constrain_expected_recruitment(self):
        for record in self:
            if record.expected_recruitment > (record.job_position.total_payroll - record.job_position.no_of_employee):
                raise UserError('Số nhân viên đã vượt quá định biên.')

    @api.model
    def create(self, vals):
        if not vals.get('start_date'):
            vals['start_date'] = fields.Date.today()
        res = super(RecruitmentPeriod, self).create(vals)
        res.job_position.write({'state': 'recruit',
                                'website_published': True,
                                'no_of_recruitment': vals.get('expected_recruitment'),
                                'date_open': vals.get('start_date'),
                                'date_closed': vals.get('end_date')})
        return res

    def action_save(self):
        number = self.expected_recruitment
        if number <= 0:
            raise ValidationError('Số lượng tuyển phải > 0')
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
