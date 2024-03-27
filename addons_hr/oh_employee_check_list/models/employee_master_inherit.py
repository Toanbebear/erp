# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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

from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning

class EmployeeEntryDocuments(models.Model):
    _name = 'employee.checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Documents"

    name = fields.Char(string='Name', copy=False, required=1)

class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'HR Employee Documents'

    def mail_reminder(self):
        """Sending document expiry notification to employees."""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.expiry_date:
                exp_date = fields.Date.from_string(i.expiry_date) - timedelta(days=7)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.employee_ref.name + ",<br>Your Document " + i.name + "is going to expire on " + \
                                   str(i.expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.employee_ref.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()

    @api.constrains('expiry_date')
    def check_expr_date(self):
        for each in self:
            if each.expiry_date:
                exp_date = fields.Date.from_string(each.expiry_date)
                if exp_date < date.today():
                    raise Warning('Tài liệu của bạn đã hết hạn.')

    def _document_domain(self):
        emp_id = self.env.context.get('active_id')
        employee = self.env['hr.employee'].browse(emp_id)
        if not employee.job_id:
            return [('group_job_ids', '=', False)]
        else:
            employee_docs = self.env['hr.employee.document'].search([('employee_ref', '=', emp_id)])
            entry_doc = employee_docs.mapped('document_name.id')
            return [('id', 'not in', entry_doc), '|', ('group_job_ids', 'in', [employee.group_job.id]), ('group_job_ids', '=', False)]

    name = fields.Char(string='Tên tài liệu', required=True, copy=False, help='You can give your Document number.')
    document_name = fields.Many2one('employee.checklist', string='Document', help='Type of Document', required=True, domain=lambda self: self._document_domain())
    description = fields.Text(string='Mô tả', copy=False)
    expiry_date = fields.Date(string='Ngày hết hạn', copy=False)
    employee_ref = fields.Many2one('hr.employee', invisible=1, copy=False)
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel', 'doc_id', 'attach_id3', string="Tệp đính kèm",
                                         help='You can attach the copy of your document', copy=False)
    quantity = fields.Integer('Số lượng', default= 1)
    issue_date = fields.Date(string='Ngày phát hành', default=datetime.now().strftime('%Y-%m-%d'), copy=False)
    active = fields.Boolean(default=True)

    @api.onchange('document_name')
    def _onchange_department(self):
        self.name = self.document_name.name

    _sql_constraints = [
        ('document_name_uniq', 'unique (document_name, employee_ref)', 'Tài liệu đã tồn tại!')
    ]

class EmployeeMasterInherit(models.Model):
    _inherit = 'hr.employee'

    def _get_entry_progress(self):
        for each in self:
            total_len = self.env['employee.checklist'].search_count([])
            entry_len = self.env['hr.employee.document'].sudo().search_count([('employee_ref', '=', each.id)])
            if total_len != 0:
                each.entry_progress = (entry_len * 100) / total_len
            else:
                each.entry_progress = 0

    entry_progress = fields.Float(compute='_get_entry_progress', string='Hồ sơ lao động', default=0.0)
    employee_doc = fields.One2many("hr.employee.document", 'employee_ref', "Hồ sơ")
    maximum_rate = fields.Integer(default=100)
    check_list_enable = fields.Boolean(invisible=True, copy=False)
    employee_status = fields.Text('Tình trạng', compute="_compute_status")

    @api.depends('entry_progress')
    def _compute_status(self):
        for record in self:
            if record.entry_progress == 100:
                repair_msg = "Đủ HS"
            else:
                repair_msg = "Chưa có HS"
            record.employee_status = repair_msg

    def _document_count(self):
        for each in self:
            document_ids = self.env['hr.employee.document'].sudo().search([('employee_ref', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('employee_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                               Click to Create for New Documents
                            </p>'''),
            'limit': 80,
            'context': "{'default_employee_ref': '%s'}" % self.id
        }

    document_count = fields.Integer(compute='_document_count', string='# Documents')


class HrEmployeeAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_rel = fields.Many2many('hr.employee.document', 'doc_attachment_id', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)