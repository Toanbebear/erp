# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAnnouncementTable(models.Model):
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Code No:')
    announcement_reason = fields.Text(string='Tiêu đề', states={'draft': [('readonly', False)]}, required=True, readonly=True)
    state = fields.Selection([('draft', 'Bản nháp'), ('to_approve', 'Chờ phê duyệt'),
                              ('approved', 'Phê duyệt'), ('rejected', 'Từ chối')],
                             string='Trạng thái',  default='draft',
                             track_visibility='always')
    requested_date = fields.Date(string='Ngày yêu cầu', default=datetime.now().strftime('%Y-%m-%d'))
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
                                     string="Tệp đính kèm", help='You can attach the copy of your Letter')
    company_id = fields.Many2one('res.company', string='Công ty',
                                 default=lambda self: self.env.user.company_id)
    is_announcement = fields.Boolean(string='Thông báo chung?')
    announcement_type = fields.Selection([('employee', 'Nhân viên'), ('department', 'Phòng ban'), ('job_position', 'Vị trí công việc')], string="Loại thông báo")
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_announcements', 'announcement', 'employee', domain="[('company_id', '=', company_id)]",
                                    string='Nhân viên')
    department_ids = fields.Many2many('hr.department', 'hr_department_announcements', 'announcement', 'department', domain="[('company_id', '=', company_id)]",
                                      string='Phòng ban')
    position_ids = fields.Many2many('hr.job', 'hr_job_position_announcements', 'announcement', 'job_position',
                                    string='Vị trí công việc')
    announcement = fields.Html(string='Nội dung', states={'draft': [('readonly', False)]}, readonly=True)
    date_start = fields.Date(string='Ngày bắt đầu', default=fields.Date.today(), required=True)
    date_end = fields.Date(string='Ngày kết thúc', default=fields.Date.today(), required=True)

    def reject(self):
        self.state = 'rejected'

    def approve(self):
        self.state = 'approved'

    def sent(self):
        self.state = 'to_approve'

    @api.constrains('date_start', 'date_end')
    def validation(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be less than End Date")

    @api.model
    def create(self, vals):
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement.general')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement')
        return super(HrAnnouncementTable, self).create(vals)
