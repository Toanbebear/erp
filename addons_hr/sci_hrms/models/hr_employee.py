# -*- coding: utf-8 -*-

import base64
import calendar
import logging
import time
from datetime import datetime, date
from io import BytesIO

import pytz
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api
from odoo.exceptions import ValidationError, Warning
from odoo.tools.translate import _

from .mailmerge import MailMerge

_logger = logging.getLogger(__name__)


class HrSalaryHistory(models.Model):
    _name = 'hr.salary.history'
    _description = 'HR Salary History'

    employee_id = fields.Many2one('hr.employee', string="Nhân viên", required=1)

    basic_salary_old = fields.Integer('Lương CB cũ')
    allowance_old = fields.Integer('Phụ cấp cũ')
    KPI_salary_old = fields.Integer('Lương KPI cũ')
    wage_old = fields.Integer('Tổng thu nhập cũ')
    salary_kd = fields.Boolean(string='Lương kinh doanh')

    basic_salary = fields.Integer('Lương cơ bản', required=True)
    allowance = fields.Integer('Phụ cấp')
    KPI_salary = fields.Integer('Lương KPI')
    wage = fields.Integer('Mức tăng', compute="_compute_total_salary", store=True)
    confirm_date = fields.Date(string="Ngày hiệu lực")
    reason = fields.Text(string="Ghi chú")
    checked = fields.Boolean(string='Hết hiệu lực', default=False)
    job_old = fields.Char('Chức vụ cũ')
    job_new = fields.Char('Chức vụ mới')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.basic_salary_old = self.employee_id.basic_salary
        self.allowance_old = self.employee_id.allowance
        self.KPI_salary_old = self.employee_id.KPI_salary
        self.wage_old = self.employee_id.wage
        self.job_old = self.employee_id.job_id.name
        self.salary_kd = self.employee_id.salary_kd

    @api.depends('basic_salary', 'allowance', 'KPI_salary')
    def _compute_total_salary(self):
        for item in self:
            item.wage = item.basic_salary + item.allowance + item.KPI_salary

    def print_notice(self):
        # check thương hiệu và check kiểu điểu chỉnh thu nhập (kpi/ kinh doanh)
        code_brand = self.employee_id.root_department.code
        if code_brand == 'DA':
            if self.salary_kd == True:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_donga_kd_report_attachment')
            else:
                raise ValidationError(_('DA Chưa có mẫu thông báo cho lương KPI!!'))
        elif code_brand == 'PR':
            if self.salary_kd == True:
                raise ValidationError(_('PR Chưa có mẫu thông báo cho lương kinh doanh!!'))
            else:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_paris_report_attachment')
        elif code_brand == 'KN':
            if self.salary_kd == True:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_kn_kd_report_attachment')
            else:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_kn_kpi_report_attachment')
        elif code_brand == 'HH':
            if self.salary_kd == True:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_hh_kd_report_attachment')
            else:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_hh_kpi_report_attachment')
        else:
            if self.salary_kd == True:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_sci_kd_report_attachment')
            else:
                notice_attacment = self.env.ref('sci_hrms.salary_adjustment_sci_kpi_report_attachment')
        decode = base64.b64decode(notice_attacment.datas)
        doc = MailMerge(BytesIO(decode))
        data_list = []
        record_data = {}
        record_data['nhan_vien'] = self.employee_id.name
        record_data['ma_nv'] = self.employee_id.employee_id
        record_data['don_vi'] = self.employee_id.department_id.name
        record_data['chuc_vu'] = self.employee_id.job_id.name
        record_data['basic_salary_old'] = self.basic_salary_old
        record_data['kpi_salary_old'] = self.KPI_salary_old or 0
        record_data['basic_salary_new'] = self.basic_salary + self.basic_salary_old
        record_data['kpi_salary_new'] = self.KPI_salary + self.KPI_salary_old

        # dùng cho lương kpi
        if self.salary_kd == False:
            record_data['total_salary_old'] = total_salary_old = self.basic_salary_old + self.KPI_salary_old
            record_data[
                'total_salary_new'] = total_salary_new = self.basic_salary + self.basic_salary_old + self.KPI_salary + self.KPI_salary_old
            record_data['salary_adjustment_kpi'] = total_salary_new - total_salary_old

        record_data['salary_adjustment_kd'] = self.basic_salary
        record_data['confirm_date'] = self.confirm_date

        data_list.append(record_data)
        doc.merge_templates(data_list, separator='page_break')

        fp = BytesIO()
        doc.write(fp)
        doc.close()
        fp.seek(0)
        report = base64.encodebytes((fp.read()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({'name': 'Thong_bao_dieu_chinh_thu_nhap.docx',
                                                              'datas': report,
                                                              'res_model': 'temp.creation',
                                                              'public': True})
        return {'name': 'Thông báo điều chỉnh thu nhập',
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'attachment_id': attachment.id}
                }


class InsurancePolicy(models.Model):
    _name = 'hr.insurance.policy'
    _description = 'HR insurance policy'

    name = fields.Char(string='Tên đơn vị', required=True)
    code = fields.Char(string='Mã đơn vị')
    code_brand = fields.Selection([('SCI', 'SCI'), ('KN', 'Kangnam'), ('PR', 'Paris'), ('DA', 'Đông Á'),
                                   ('HH', 'Hồng Hà'), ('HV', 'Học Viện')], default="SCI", string="Mã thương hiệu")
    note_field = fields.Html(string='Ghi chú')


class EmployeeInsuranceHistory(models.Model):
    _name = 'hr.insurance.history'
    _description = 'HR Insurance'

    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, help="Employee")
    deposit_bh = fields.Integer('Lương tham gia', default=4730000)
    date = fields.Date(string='Tháng tham gia', default=time.strftime('%Y-%m-%d'))
    payment_term_bh = fields.Float('Tỷ lệ đóng(%)', default=10.5)
    so_bhxh = fields.Char(string="Số sổ BHXH", required=True)
    money_per_month_bh = fields.Integer('Số tiền đóng', compute="_compute_money_per_month_bh", store=True)
    so_so_luu = fields.Char(string="Số sổ lưu")
    tinh_trang = fields.Char(string='Tình trạng sổ')
    tinh_trang_tra = fields.Char(string='Thông tin trả sổ')
    noi_cap = fields.Char(string='Nơi cấp')
    noi_tham_gia = fields.Many2one('hr.insurance.policy', string='Nơi tham gia', required=True)
    ly_do_ko_dong = fields.Char(string='Lý do không đóng BHXH')
    reason = fields.Text(string="Ghi chú")
    checked = fields.Boolean(string='Hết hiệu lực', default=False)
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id", readonly=True, store=True)

    @api.depends('deposit_bh', 'payment_term_bh')
    def _compute_money_per_month_bh(self):
        for record in self:
            if record.deposit_bh and record.payment_term_bh:
                record.money_per_month_bh = record.deposit_bh * (record.payment_term_bh / 100)

    @api.model
    def create(self, vals):
        insurance = self.env['hr.insurance.history'].search_count(
            [('employee_id', '=', vals.get('employee_id')), ('checked', '=', False)])
        if insurance:
            raise ValidationError(
                'Một nhân viên chỉ có thể có một sổ BHXH cùng một lúc. (Không bao gồm sổ BHXH hết hiệu lực')
        else:
            res = super(EmployeeInsuranceHistory, self).create(vals)
            return res


class Employee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'qrcode.mixin']

    # trường được thêm
    employee_id = fields.Char('Mã cũ')
    employee_code = fields.Char('Mã mới')
    joining_date = fields.Date('Joining Date', default=datetime.now().date())
    work_duration = fields.Char('Seniority', compute='_get_work_duration')
    tz = fields.Selection('_tz_get', string='Timezone', required=True, default='Asia/Ho_Chi_Minh')
    hr_point_kpi = fields.Float('Điểm tuyển dụng', digits=(16, 2), compute='_get_hr_point_kpi')
    hr_point_kpi_final = fields.Float('Điểm chốt', digits=(16, 2), compute='_get_hr_point_kpi')
    hr_user_id = fields.Many2one('res.users', "Người phụ trách", track_visibility="onchange",
                                 default=lambda self: self.env.uid)
    contract_type = fields.Many2one('hr.contract.type', string="Loại hợp đồng")
    contract_date = fields.Date('Ngày hợp đồng')
    applicants = fields.One2many('hr.applicant', 'emp_id', 'Applicant')
    hr_part = fields.Selection([('100', 'Care 100%'), ('75', 'Care 75%'), ('50', 'Care 50%'), ('25', 'Care 25%')],
                               string='Vai trò',
                               default="100", related='applicants.part')
    resignations = fields.One2many('hr.resignation', 'employee_id', 'Resignation')
    group_job = fields.Many2one('hr.group.job', string='Bộ phận', help='Chọn bộ phận nhóm vị trí',
                                related='job_id.group_job')
    area = fields.Selection([('mb', 'Miền Bắc'), ('mn', 'Miền Nam')], default="mb", string="Khu vực")
    staff_level = fields.Selection(
        [('cv', 'Chuyên viên'), ('nv', 'Nhân viên'), ('ql', 'Quản lý'), ('qlcc', 'Quản lý cấp cao'),
         ('qlct', 'Quản lý cấp trung'), ('ttv', 'Thực tập viên'), ('or', 'Khác')], default="nv", string="Cấp cán bộ")
    email = fields.Char('Email cá nhân')
    emergency_address = fields.Char('Chỗ ở hiện tại')
    root_department = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    sector_id = fields.Many2one('hr.department.sector', string='Khối', related='department_id.sector_id', store=True)

    certificate = fields.Selection([
        ('bachelor', 'Cử nhân'),
        ('master', 'Đại học'),
        ('colleges', 'Cao đẳng'),
        ('intermediate', 'Trung cấp'),
        ('other', 'Other'),
    ], 'Certificate Level', default='master', groups="hr.group_hr_user")

    graduation_year = fields.Char(string='Năm tốt nghiệp')
    classification = fields.Char(string='Xếp loại')
    entry_checklist_domain = fields.Many2many('employee.checklist', string='Check list domain',
                                              compute='_get_checklist_domain')

    job_ids = fields.Many2many('hr.job', 'sci_emp_job_rel', 'job_id', 'emp_id', string="Vị trí kiêm nhiệm",
                               ddomain=lambda self: [('company_id', 'in', self.env.companies.ids)])
    # domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    contract_ids = fields.One2many('hr.contract', 'employee_id', 'Danh sách hợp đồng')

    # thông tin lương
    basic_salary = fields.Integer('Lương cơ bản')
    allowance = fields.Integer('Phụ cấp')
    KPI_salary = fields.Integer('Lương KPI')
    wage = fields.Integer('Tổng thu nhập', compute="_compute_salary", store=True)
    salary_history = fields.One2many('hr.salary.history', 'employee_id')
    salary_kd = fields.Boolean(string='Lương kinh doanh', default=False)

    deposit = fields.Integer('Tiền ký quỹ', default=5000000)
    payment_term = fields.Integer('Thời hạn tích lũy', default=10)
    money_per_month = fields.Integer('Số tiền đóng', compute="_compute_money_per_month", store=True)
    limit = fields.Integer(string='Tiền đã đóng')
    check_kq = fields.Boolean(string='Hết hiệu lực', compute='_compute_limit', default=False)

    deposit_bh = fields.Integer('Lương tham gia BHXH', compute="_compute_deposit")
    payment_term_bh = fields.Float('Tỷ lệ đóng(%)', compute="_compute_deposit")
    money_per_month_bh = fields.Integer('Số tiền đóng', compute="_compute_deposit")
    check_bh = fields.Boolean(string='Hết hiệu lực', default=True)
    insurance_history = fields.One2many('hr.insurance.history', 'employee_id', string="Bảo hiểm", help="Insurance")
    mapped_attendance_device_ids = fields.Many2many('attendance.device', 'mapped_device_employee_rel',
                                                    string='Mapped attendance device')

    _sql_constraints = [
        ('employee_id_uniq', 'unique (employee_id)', 'Mã nhân viên đã tồn tại!'),
        ('employee_email_uniq', 'unique (work_email)', 'Email công ty của nhân viên đã tồn tại!')
    ]

    @api.onchange('company_id')
    def onchange_company(self):
        self.department_id = False
        self.sector_id = False
        self.job_id = False
        self.team_id = False

    def get_calendar_working(self):
        employee = self.env['hr.employee'].search([('department_id', '!=', False)])
        for record in employee:
            hr_attendance = self.env['hr.attendance'].search([('employee_id.id', '=', record.id)])
            today = date.today()
            number_month = calendar.monthrange(today.year, today.month)
            attendance = []
            for rec in hr_attendance:
                if rec.check_in and rec.check_in.month == today.month:
                    attendance.append(rec.check_in.day)
                elif rec.check_out and rec.check_out.month == today.month:
                    attendance.append(rec.check_out.day)
            for i in range(1, number_month[1] + 1):
                if i in attendance:
                    continue
                else:
                    self.env['hr.attendance'].sudo().create({
                        'employee_id': record.id,
                        'check_in': datetime(today.year, today.month, i, 00, 00, 00),
                        'check_out': datetime(today.year, today.month, i, 16, 59, 59),
                        'workday': '1',
                        'state': 'draft',
                    })

    @api.onchange('insurance_history')
    def _compute_deposit(self):
        deposit_bh = payment_term_bh = money_per_month_bh = 0
        check_bh = True
        for item in self.insurance_history:
            if not item.checked:
                deposit_bh = item.deposit_bh
                payment_term_bh = item.payment_term_bh
                money_per_month_bh = item.money_per_month_bh
                check_bh = False
        self.deposit_bh = deposit_bh
        self.payment_term_bh = payment_term_bh
        self.money_per_month_bh = money_per_month_bh
        self.check_bh = check_bh

    @api.depends('salary_history')
    def _compute_salary(self):
        for record in self:
            KPI_salary = allowance = basic_salary = 0
            for item in record.salary_history:
                current_datetime = datetime.now()
                current_date = datetime.strftime(current_datetime, "%Y-%m-%d ")
                x = str(item.confirm_date) if item.confirm_date else current_date
                if not item.checked and x <= current_date:
                    basic_salary += item.basic_salary
                    allowance += item.allowance
                    KPI_salary += item.KPI_salary
            record.basic_salary = basic_salary
            record.allowance = allowance
            record.KPI_salary = KPI_salary
            record.wage = record.basic_salary + record.allowance + record.KPI_salary

    def send_msg(self):
        return {'type': 'ir.actions.act_window',
                'name': _('SMS Message'),
                'res_model': 'sms.message',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.id},
                }

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        return [
            (template.id, '%s%s' % (template.employee_code and '[%s] ' % template.employee_code or '', template.name))
            for template in self]

    def _compute_limit(self):
        for res in self:
            if res.limit >= res.deposit:
                res.check_kq = True
            else:
                res.check_kq = False

    @api.depends('deposit', 'payment_term')
    def _compute_money_per_month(self):
        for record in self:
            if record.deposit and record.payment_term:
                record.money_per_month = record.deposit / record.payment_term

    @api.onchange('job_ids')
    def _onchange_job_ids(self):
        if self.job_id:
            return {
                'domain': {'job_ids': [('id', '!=', self.job_id.id)]}
            }

    @api.depends('job_id')
    def _get_checklist_domain(self):
        checklist = self.env['employee.checklist']
        for item in self:
            if not item.job_id:
                item.entry_checklist_domain = checklist.search([('group_job_ids', '=', False)])
            else:
                item.entry_checklist_domain = checklist.search(
                    ['|', ('group_job_ids', 'in', [item.job_id.group_job.id]), ('group_job_ids', '=', False)])

    def _get_entry_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([('id', 'in', each.entry_checklist_domain.ids), '|',
                                                                     ('group_job_ids', 'in', [each.group_job.id]),
                                                                     ('group_job_ids', '=', False)])
            document_ids = self.env['hr.employee.document'].sudo().search([('employee_ref', '=', each.id)])
            entry_len = len(document_ids)
            if total_len != 0:
                each.entry_progress = (entry_len * 100) / total_len

    @api.depends('applicants.job_id.point_kpi', 'resignations.type_reason.point_kpi')
    def _get_hr_point_kpi(self):
        from dateutil import relativedelta
        for item in self:
            item.hr_point_kpi = 0
            start_date = fields.Date.to_date(self.env.context.get('start_date'))
            end_date = fields.Date.to_date(self.env.context.get('end_date'))

            # Todo: Case of normal view without context, should be remove if not needed
            if not start_date or not end_date:
                if item.applicants:
                    item.hr_point_kpi = item.applicants[0].job_id.point_kpi
                    if item.applicants[0].part == '70':
                        item.hr_point_kpi_final = item.hr_point_kpi * 0.7
                    elif item.applicants[0].part == '50':
                        item.hr_point_kpi_final = item.hr_point_kpi * 0.5
                    elif item.applicants[0].part == '25':
                        item.hr_point_kpi_final = item.hr_point_kpi * 0.25
                    else:
                        item.hr_point_kpi_final = item.hr_point_kpi

                    if item.resignations:
                        if item.joining_date:
                            s_joining = item.joining_date
                            e_joining = item.joining_date + relativedelta.relativedelta(months=+1)
                            if s_joining <= item.joining_date <= e_joining:
                                item.hr_point_kpi_final *= (1 - item.resignations[0].type_reason.point_kpi / 100)
                else:
                    item.hr_point_kpi = item.job_id.point_kpi
                    item.hr_point_kpi_final = item.hr_point_kpi

                    if item.resignations:
                        if item.joining_date:
                            s_joining = item.joining_date
                            e_joining = item.joining_date + relativedelta.relativedelta(months=+1)
                            if s_joining <= item.joining_date <= e_joining:
                                self.hr_point_kpi_final *= (1 - item.resignations[0].type_reason.point_kpi / 100)
            # View with context for start_date and end_date
            else:
                if item.applicants:
                    if start_date <= item.joining_date <= end_date:
                        item.hr_point_kpi += item.applicants[0].job_id.point_kpi
                        if item.applicants[0].part == '70':
                            item.hr_point_kpi_final += item.hr_point_kpi * 0.7
                        elif item.applicants[0].part == '50':
                            item.hr_point_kpi_final += item.hr_point_kpi * 0.5
                        elif item.applicants[0].part == '25':
                            item.hr_point_kpi_final += item.hr_point_kpi * 0.25
                        else:
                            item.hr_point_kpi_final += item.hr_point_kpi

                    if item.resignations and item.resign_date and start_date <= item.joining_date <= end_date:
                        if item.joining_date:
                            s_joining = item.joining_date
                            e_joining = item.joining_date + relativedelta.relativedelta(months=+1)
                            if s_joining <= item.resignations[0].expected_revealing_date <= e_joining:
                                item.hr_point_kpi_final -= item.hr_point_kpi_final * item.resignations[
                                    0].type_reason.point_kpi / 100
                else:
                    if item.joining_date:
                        if start_date <= item.joining_date <= end_date:
                            if start_date <= item.joining_date <= end_date:
                                item.hr_point_kpi += item.job_id.point_kpi
                                item.hr_point_kpi_final += item.hr_point_kpi

                            if item.resignations and item.resign_date:
                                s_joining = item.joining_date
                                e_joining = item.joining_date + relativedelta.relativedelta(months=+1)
                                if s_joining <= item.resignations[0].expected_revealing_date <= e_joining:
                                    item.hr_point_kpi_final -= item.hr_point_kpi_final * item.resignations[
                                        0].type_reason.point_kpi / 100

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(Employee, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                               lazy=lazy)
        for line in res:
            employees = self.env['hr.employee']
            if '__domain' in line:
                employees = self.search(line['__domain'])
            if 'hr_point_kpi' in fields:
                line['hr_point_kpi'] = sum(employees.mapped('hr_point_kpi'))
            if 'hr_point_kpi_final' in fields:
                line['hr_point_kpi_final'] = sum(employees.mapped('hr_point_kpi_final'))
        return res

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('employee.code.action')
        if not sequence:
            raise ValidationError(_('Định danh mã nhân viên đang không tồn tại!'))
        vals['employee_code'] = sequence
        sci_employee = super(Employee, self).create(vals)
        return sci_employee

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    def sci_create(self):
        if not self.user_id:
            if not self.work_email:
                raise Warning(_('Please fill work email address before creating an account.'))
            else:
                user = self.env['res.users'].sudo().create({'name': self.name,
                                                            'image_1920': self.image_1920,
                                                            'login': self.work_email,
                                                            'email': self.work_email})
                self.user_id = user.id
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                context = dict(self._context or {})
                context['message'] = 'Tài khoản đã được tạo thành công!!'
                return {
                    'name': 'Success',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view_id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
        else:
            return {
                'name': 'User',  # Lable
                'res_id': self.user_id.id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('base.view_users_form').id,
                'res_model': 'res.users',  # your model
                'target': 'new',  # if you want popup
                # 'context': "{'generic_request_id': uid}",  # if you need
            }

    @api.depends('joining_date', 'resign_date')
    def _get_work_duration(self):
        for item in self:
            if item.resign_date:
                duration = relativedelta(item.resign_date, item.joining_date)
            else:
                duration = relativedelta(date.today(), item.joining_date)
            y = str(duration.years) + (' năm', ' năm')[duration.years > 1]
            m = str(duration.months) + (' tháng', ' tháng')[duration.months > 1]
            d = str(duration.days) + (' ngày', ' ngày')[duration.days > 1]
            item.work_duration = '%s %s %s' % (('', y)[duration.years > 0],
                                               ('', m)[duration.months > 0],
                                               ('', d)[duration.days > 0])

    @api.model
    def convert_emp_id_to_external_id(self, limit=2000):
        emps_external_id_data = self.env['ir.model.data'].search(
            [('model', '=', 'hr.employee'), ('name', 'ilike', 'hr_employee_')], limit=limit)
        for data in emps_external_id_data:
            emp = self.env['hr.employee'].browse(data.res_id)
            if emp.employee_id:
                data.name = emp.employee_id

    @api.model
    def revamp_job_department(self):
        all_emps = self.env['hr.employee'].search([])
        for emp in all_emps:
            if emp.job_id and emp.department_id:
                if not emp.job_id.department_id:
                    emp.job_id.department_id = emp.department_id
                elif emp.job_id.department_id != emp.department_id:
                    alt_job = self.env['hr.job'].search([('name', '=', emp.job_id.name),
                                                         ('department_id', '=', emp.department_id.id)])
                    if not alt_job:
                        alt_job = self.env['hr.job'].create({'name': emp.job_id.name,
                                                             'department_id': emp.department_id.id})
                    emp.job_id = alt_job

    #     kế thừa lưu trữ
    def toggle_active(self):
        res = super(Employee, self).toggle_active()
        today = datetime.now().strftime('%d-%m-%Y')
        for act in self:
            if act.active:
                act.write({
                    'work_email': act.work_email[:-11]
                })
                if act.user_id:
                    new_login = act.user_id.login[:-11]
                    act.user_id.write({
                        'login': new_login,
                        'active': True
                    })
                    if act.user_id.partner_id:
                        act.user_id.partner_id.write({
                            'email': new_login,
                            'active': True
                        })
            else:
                act.write({
                    'work_email': act.work_email + '.' + today
                })
                if act.user_id:
                    new_login = act.user_id.login + '.' + today
                    act.user_id.write({
                        'login': new_login,
                        'active': False
                    })
                    if act.user_id.partner_id:
                        act.user_id.partner_id.write({
                            'email': new_login,
                            'active': False
                        })
        return res


class DepartmentSector(models.Model):
    _name = "hr.department.sector"
    _description = 'HR department sector'

    name = fields.Char("Tên Khối", required=True)
    code = fields.Char("Mã Khối", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tên khối đã tồn tại!"),
    ]


class Department(models.Model):
    _inherit = ['hr.department']

    sector_id = fields.Many2one('hr.department.sector', string='Khối')
    # 2 truong đếm số nhan vien va don vi cap duoi
    child_department_count = fields.Integer(string='child nums', compute='count_department', store=True)
    employee_count = fields.Integer(string='emp nums', compute='count_employee')
    address_location = fields.Text(string='Địa điểm')
    root_code = fields.Char(string="Mã(phòng ban)")

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        return [(template.id, '%s%s' % (template.root_code and '[%s] ' % template.root_code or '', template.name))
                for template in self]

    @api.model
    def create(self, vals):
        res = super(Department, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('company_id'):
            for dep in self.child_ids:
                dep.company_id = vals.get('company_id')
            for emp in self.member_ids:
                emp.company_id = vals.get('company_id')
            lst_job = self.env['hr.job'].search([('department_id', '=', self.id)])
            for item in lst_job:
                item.company_id == vals.get('company_id')

        res = super(Department, self).write(vals)

        return res

    # ham dem don vi cap duoi
    @api.depends('child_ids')
    def count_department(self):
        for item in self:
            if item.id:
                item.child_department_count = len(item.child_ids)
            else:
                item.child_department_count = 0

    # ham dem nhan vien trong don vi
    @api.depends('member_ids')
    def count_employee(self):
        for item in self:
            if item.id:
                child_list = self.env['hr.department'].search([('parent_id', 'child_of', [item.id])])
                for dep in child_list:
                    item.employee_count += len(dep.member_ids)
            else:
                item.employee_count = 0

    # button to link manager
    def action_get_manager_view(self):
        if self.manager_id:
            return {
                'name': 'Manager',  # Lable
                'res_id': self.manager_id.id,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.employee',  # your model
                # 'target': 'new',  # if you want popup
                # 'context': ctx,  # if you need
            }
        else:
            return None


class HRResignation(models.Model):
    _inherit = 'hr.resignation'

    # brand = fields.Many2one('hr.department.brand', string="Khối (Thương hiệu)",
    #                                   related='department_id.root_parent', store=True)
    work_duration = fields.Char('Thâm niên', related='employee_id.work_duration')
