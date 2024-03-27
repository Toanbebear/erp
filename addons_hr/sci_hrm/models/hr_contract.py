# -*- coding: utf-8 -*-
import base64
from io import BytesIO
import pytz
from dateutil.relativedelta import relativedelta
from .mailmerge import MailMerge
from num2words import num2words

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import datetime

DATETYPE = [('months', 'tháng'), ('years', 'năm')]


class ContractType(models.Model):
    _name = 'hr.contract.type'
    _description = 'Contract Type'
    _order = 'sequence, id'

    code = fields.Char(string='Mã hợp đồng', required=True)
    name = fields.Char(string='Kiểu hợp đồng', required=True)
    type = fields.Selection([('hd', 'Hợp đồng'), ('pl', 'Phụ lục')], default="hd", string="Loại")
    sequence = fields.Integer(help="Gives the sequence when displaying a list of Contract.", default=10)
    _sql_constraints = [('unique_code', 'unique(code)', 'Mã đã tồn tại!!.')]


class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    basic_salary = fields.Monetary('Basic salary', digits=(16, 2), track_visibility="onchange")
    allowance = fields.Monetary('Allowance')
    KPI_salary = fields.Monetary('KPI salary')
    type = fields.Selection([('hd', 'Hợp đồng'), ('pl', 'Phụ lục')], default="hd", string="Loại")
    type_id = fields.Many2one('hr.contract.type', string="Loại hợp đồng", required=True, domain="[('type', '=', type)]")

    last_salary = fields.Date('Kỳ xét duyệt lần cuối', readonly="1")
    salary_deadline_type = fields.Selection(DATETYPE, 'Date Type', default="years", required=True,
                                            track_visibility="onchange")
    salary_deadline = fields.Integer('Thời hạn xét duyệt', size=3, track_visibility="onchange", default=1)
    salary_year = fields.Date(string="Ngày xét lương", compute="_compute_status")
    salary_status = fields.Text('Tình trạng', compute="_compute_status")

    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        return

    @api.onchange('type')
    def _onchange_type(self):
        self.type_id = None
        return {
            'domain': {'type_id': [('type', '=', self.type)]}
        }

    @api.onchange('basic_salary', 'allowance', 'KPI_salary')
    def total_salary(self):
        self.wage = self.basic_salary + self.allowance + self.KPI_salary

    def print_contract(self):
        contract_type = self.type_id.get_external_id()[self.type_id.id]
        company_code = self.company_id.code
        if not company_code:
            raise ValidationError(
                _('Contract template not available for %s, please contact your admin.' % self.company_id.name))
        try:

            contract_attachment = self.env.ref(
                'sci_hrms.contract_%s_%s_report_attachment' % (
                    company_code.replace('.', '').lower(), contract_type.split('_')[-1]))
        except:
            raise ValidationError(
                _('Your contract you choose does not exist, please contact your admin.'))
        if contract_attachment:
            decode = base64.b64decode(contract_attachment.datas)
            doc = MailMerge(BytesIO(decode))
            data_list = []
            record_data = {}
            record_data['decisionnum'] = str(self.employee_id.employee_id) + "/" + str(self.type_id.code) + "-" + str(
                fields.Datetime.now().year)
            record_data['currentdate'] = fields.Datetime.now().strftime('ngày %d tháng %m năm %Y')
            record_data['name2'] = self.employee_id.name
            record_data['country'] = self.employee_id.country_id.name
            record_data['birthday'] = self.employee_id.birthday.strftime('%d/%m/%Y')
            record_data['birthplace'] = self.employee_id.place_of_birth
            record_data['tdcm'] = self.employee_id.study_field
            record_data['idnum'] = self.employee_id.identification_id
            record_data['iddate'] = self.employee_id.id_issue_date
            record_data['idplace'] = self.employee_id.id_issue_place
            record_data['address'] = self.employee_id.address_home_id.street
            record_data['phone'] = self.employee_id.mobile_phone
            record_data['email'] = self.employee_id.email
            record_data['startdate'] = self.date_start.strftime('%d/%m/%Y')
            record_data['startdatechar'] = self.date_start.strftime('ngày %d tháng %m năm %Y')
            record_data['enddate'] = self.date_end.strftime('%d/%m/%Y') if self.date_end else ''
            ds = datetime.datetime.strptime(str(self.date_start), "%Y-%m-%d")
            if self.date_end:
                de = datetime.datetime.strptime(str(self.date_end), "%Y-%m-%d")
                record_data['contract_term'] = str(relativedelta(de, ds).months) + " tháng"
            record_data['position'] = self.job_id.display_name
            record_data['basicsalary'] = '{0:,.0f}'.format(self.basic_salary)
            record_data['basicsalarychar'] = num2words(int(self.basic_salary), lang='vi_VN') + " đồng"
            record_data['allowance'] = '{0:,.0f}'.format(self.allowance) if self.allowance else ''
            record_data['KPI'] = '{0:,.0f}'.format(self.KPI_salary) if self.allowance else ''
            record_data['wage'] = '{0:,.0f}'.format(self.wage) if self.wage else ''
            record_data['wagechar'] = num2words(int(self.wage), lang='vi_VN') if self.wage else ''
            record_data['deposit'] = '{0:,.0f}'.format(self.employee_id.deposit) if self.employee_id.deposit else ''
            record_data['depositchar'] = num2words(int(self.employee_id.deposit), lang='vi_VN') + " đồng"
            record_data['payment_term'] = self.employee_id.payment_term if self.employee_id.payment_term else ''
            record_data['money_per_month'] = '{0:,.0f}'.format(
                self.employee_id.money_per_month) if self.employee_id.money_per_month else ''

            data_list.append(record_data)
            doc.merge_templates(data_list, separator='page_break')
            fp = BytesIO()
            doc.write(fp)
            doc.close()
            fp.seek(0)
            report = base64.encodebytes((fp.read()))
            fp.close()
            attachment = self.env['ir.attachment'].sudo().create({'name': 'hop_dong_lao_dong.docx',
                                                                  'datas': report,
                                                                  'res_model': 'temp.creation',
                                                                  'public': True})
            url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
                  % (attachment.id)
            return {'name': 'BIÊN BẢN KIỂM KÊ',
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'self',
                    }

            # return {'name': 'Hợp đồng lao động',
            #         'type': 'ir.actions.act_window',
            #         'res_model': 'temp.wizard',
            #         'view_mode': 'form',
            #         'target': 'inline',
            #         'view_id': self.env.ref('ms_templates.report_wizard').id,
            #         'context': {'attachment_id': attachment.id}
            #         }
        else:
            raise ValidationError(_('Contract template not available, please contact your admin.'))

    def confirm_contract(self):
        for rec in self:
            if rec.type == 'hd':
                domain = [
                    ('id', '!=', rec.id),
                    ('employee_id', '=', rec.employee_id.id),
                    ('type', '=', 'hd'),
                    '|',
                    ('state', 'in', ['open', 'close']),
                    '&',
                    ('state', '=', 'draft'),
                    ('kanban_state', '=', 'done')  # replaces incoming
                ]
                if not rec.date_end:
                    start_domain = []
                    end_domain = ['|', ('date_end', '>=', rec.date_start), ('date_end', '=', False)]
                else:
                    start_domain = [('date_start', '<=', rec.date_end)]
                    end_domain = ['|', ('date_end', '>', rec.date_start), ('date_end', '=', False)]
                domain = expression.AND([domain, start_domain, end_domain])
                if self.search_count(domain):
                    raise ValidationError(
                        'Một nhân viên chỉ có thể có một hợp đồng cùng một lúc. (Không bao gồm HĐ nháp và HĐ bị hủy')
                else:
                    rec.state = 'open'
            else:
                rec.state = 'open'

    @api.depends('salary_deadline', 'salary_deadline_type', 'date_start')
    def _compute_deadline_display(self):
        for record in self:
            if record.salary_deadline > 0 and record.salary_deadline_type:
                time_type = ''
                if record.salary_deadline_type == 'days':
                    time_type = _('days')
                elif record.salary_deadline_type == 'months':
                    time_type = _('months')
                elif record.salary_deadline_type == 'years':
                    time_type = _('years')
                record.salary_year = str(record.salary_deadline) + ' ' + time_type
            else:
                record.salary_year = _('Undefined')

    @api.depends('salary_deadline', 'salary_deadline_type', 'date_start', 'last_salary')
    def _compute_status(self):
        for record in self:
            maintenance_msg = ''
            if record.date_start:
                date_start = record.date_start
                if record.salary_deadline > 0 and record.salary_deadline_type:
                    if record.last_salary and record.last_salary > record.date_start:
                        date = datetime.datetime.strptime(record.last_salary, '%Y-%m-%d').date()
                    else:
                        date = date_start
                    deadine_salary = self.count_deadline(date, record.salary_deadline_type,
                                                         record.salary_deadline)
                    days = deadine_salary['days']
                    record.salary_year = deadine_salary['date']
                    if days < 0:
                        maintenance_msg += ('Quá hạn xét tăng lương {0} ngày').format(str(abs(days)))
                    elif days == 0:
                        maintenance_msg += ('Hôm nay là ngày xét tăng lương')
                    elif days < 15:
                        maintenance_msg += ('{0} ngày nữa là ngày xét tăng lương').format(str(abs(days)))
            record.salary_status = maintenance_msg

    def count_deadline(self, date, date_type, index):
        time = datetime.datetime.now()
        tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
        tz_database = pytz.timezone('UTC')
        time = tz_database.localize(time)
        time = time.astimezone(tz_current)
        time = time.date()
        if date_type == 'days':
            date += relativedelta(days=+index)
        elif date_type == 'months':
            date += relativedelta(months=+index)
        elif date_type == 'years':
            date += relativedelta(years=+index)
        days = (date - time).days
        return {'date': date, 'days': days}
