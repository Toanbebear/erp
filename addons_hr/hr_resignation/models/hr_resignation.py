# -*- coding: utf-8 -*-
import base64
import datetime
from datetime import datetime
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request
from .mailmerge import MailMerge

date_format = "%Y-%m-%d"


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = "Resignation"

    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Nhân viên", default=_get_employee_id, required=True,
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Phòng ban", related='employee_id.department_id',
                                    help='Department of the employee')
    joined_date = fields.Date(string="Ngày vào làm", readonly=True,
                              help='Joining date of the employee')
    expected_revealing_date = fields.Date(string="Ngày nghỉ việc", required=True,
                                          help='Date on which he is revealing from the company')
    revealing_date = fields.Date(string="Ngày nộp đơn", default=fields.Datetime.now())
    resign_confirm_date = fields.Date(string="Ngày phê duyệt", required=True, default=fields.Datetime.now())
    reason = fields.Text(string="Reason", help='Specify reason for leaving the company')
    state = fields.Selection([('draft', 'Bản nháp'), ('approved', 'Chấp thuận'), ('cancel', 'Hủy')],
                             string='Trạng thái', default='draft')
    check_resignation = fields.Boolean(string='Công nợ nghị việc', default=False)

    type_reason = fields.Many2one('hr.resignation.reason', "Lý do", required=True)
    job = fields.Many2one('hr.job', 'Chức vụ', related='employee_id.job_id', store=True)
    flag = fields.Boolean('Flag', default=False)

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def _compute_read_only(self):
        """ Use this function to check weather the user has the permission to change the employee"""
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_user'):
            self.read_only = True
        else:
            self.read_only = False

    @api.onchange('employee_id')
    def set_join_date(self):
        self.joined_date = self.employee_id.joining_date if self.employee_id.joining_date else ''

    @api.model
    def create(self, vals):
        # assigning the sequence for the record
        employee = self.env['hr.employee'].search([('id', '=', vals['employee_id'])], limit=1)
        if employee.user_id:
            user = request.env['res.users'].sudo().search([('id', '=', employee.user_id.id)], limit=1)
            user.update({'active': False})
            employee.update({'user_id': None})
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
        res = super(HrResignation, self).create(vals)
        return res

    @api.constrains('employee_id')
    def check_employee(self):
        # Checking whether the user is creating leave request of his/her own
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
                    raise ValidationError(_('You cannot create request for other employees'))

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        # Check whether any resignation request already exists
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['confirm', 'approved'])])
                if resignation_request:
                    raise ValidationError(
                        'Có một yêu cầu từ chức ở trạng thái được xác nhận hoặc phê duyệt cho nhân viên này!')

    def confirm_resignation(self):
        for rec in self:
            rec.state = 'approved'
            rec.resign_confirm_date = str(datetime.now())
            DeviceMain = self.env['sci.device.main']
            custody_group = DeviceMain.read_group([('employee_id', '=', rec.employee_id.id)], ['category_id'],
                                                  ['category_id'])
            for item in custody_group:
                custody_ids = DeviceMain.search(
                    [('employee_id', '=', rec.employee_id.id), ('category_id', '=', item['category_id'][0])])
                flag = False
                device_ids = []
                for data in custody_ids:
                    flag = True
                    device_ids.append((4, data.id))
                    emp_id = data.category_id.technician_user_id.id if data.category_id.technician_user_id else None
                if flag:
                    payload = {
                        'type': 'import',
                        'category_id': item['category_id'][0],
                        'employee_id': emp_id,
                        'department_id': rec.employee_id.department_id.id,
                        'parent_id': rec.employee_id.department_id.manager_id.id if rec.employee_id.department_id.manager_id else None,
                        'employee_use': rec.employee_id.id,
                        'description': 'Phiếu bàn giao thiết bị nhân viên nghỉ việc!!!',
                        'state': 'confirm',
                        'device_ids': device_ids
                    }
                    self.env['ems.equipment.export'].create(payload)

    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def update_employee_status(self):
        resignation = self.env['hr.resignation'].search([('state', '=', 'approved'), ('flag', '!=', True)])
        contracts = self.env['hr.contract'].search(
            [('state', 'in', ('open', 'pending'))])  # ('employee_id', '=', self.employee_id.id)
        for rec in resignation:
            if rec.resign_confirm_date <= fields.Date.today() and rec.employee_id.active:
                contract = contracts.search([('employee_id', '=', rec.employee_id.id)])
                if contract:
                    contract.state = 'cancel'
                rec.employee_id.active = False
                rec.employee_id.resign_date = rec.resign_confirm_date
                rec.employee_id.reason_resign = rec.type_reason.name
                rec.flag = True

    def print_decision(self):
        try:
            code_brand = self.employee_id.company_id.code
            if self.employee_id.insurance_history:
                insurances_location = self.employee_id.insurance_history
                for rec in insurances_location:
                    print(rec)
                    print(rec.noi_tham_gia.code_brand)
                    print(rec.checked)
                    if rec.checked == False:
                        code_brand = rec.noi_tham_gia.code_brand
            print(code_brand)
            decision_attachment = self.env.ref(
                'hr_resignation.decision_resignation_%s_report_attachment' % code_brand.lower())
            decode = base64.b64decode(decision_attachment.datas)
            doc = MailMerge(BytesIO(decode))
            data_list = []
            record_data = {}
            record_data['nhan_vien'] = self.employee_id.name
            record_data['ngay_nghi'] = self.expected_revealing_date.strftime(
                'ngày %d tháng %m năm %Y') if self.expected_revealing_date else ''
            record_data['ngay_sinh'] = self.employee_id.birthday
            record_data['cmnd'] = self.employee_id.identification_id
            record_data['ngay_cap'] = self.employee_id.id_issue_date
            record_data['noi_cap'] = self.employee_id.id_issue_place
            record_data['dia_chi'] = self.employee_id.address_home_id
            record_data['chuc_vu'] = self.employee_id.job_id.name

            data_list.append(record_data)
            doc.merge_templates(data_list, separator='page_break')

            fp = BytesIO()
            doc.write(fp)
            doc.close()
            fp.seek(0)
            report = base64.encodebytes((fp.read()))
            fp.close()
            attachment = self.env['ir.attachment'].sudo().create({'name': 'quyet_dinh_nghi_viec.docx',
                                                                  'datas': report,
                                                                  'res_model': 'temp.creation',
                                                                  'public': True})
            url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
                  % (attachment.id)
            return {'name': 'Quyết định nghỉ việc',
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'self',
                    }
        except:
            raise ValidationError(
                _('Việc in quyết định đang có vấn đề ,xin lỗi về sự bất tiện này, hãy liên hệ với quản trị viên để được giúp đỡ!'))


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    resign_date = fields.Date('Ngày từ chức', readonly=True)
    reason_resign = fields.Char(string='Lý do từ chức', readonly=True)


class RecruitmentDegree(models.Model):
    _name = "hr.resignation.reason"
    _description = "resignation reason"
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Lý do đã tồn tại!')
    ]

    name = fields.Char("Lý do", required=True, translate=True)
    point_kpi = fields.Float('Hệ số điểm(%)', digits=(16, 1), default=50)
    sequence = fields.Integer("Thứ tự", default=1, help="Gives the sequence order when displaying a list of degrees.")
