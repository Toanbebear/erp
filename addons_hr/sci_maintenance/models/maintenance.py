# -*- coding: utf-8 -*-

import datetime
from datetime import timedelta
import pytz
from odoo.http import request
from odoo import api, fields, models, SUPERUSER_ID, _
import string
import random
from random import randint


class MaintenanceStage(models.Model):
    """ Model for case stages. This models the main stages of a Maintenance Request management flow. """

    _name = 'sci.maintenance.stage'
    _description = 'Maintenance Stage'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=20)
    fold = fields.Boolean('Folded in Maintenance Pipe')
    done = fields.Boolean('Request')


class MaintenanceEquipmentCategory(models.Model):
    _name = 'sci.maintenance.equipment.category'
    _description = 'Maintenance Equipment Category'

    department_id = fields.Many2one('hr.department', 'Phòng ban quản lý')
    name = fields.Char('Category Name', required=True, translate=True)
    email = fields.Char('Email')
    technician_user_id = fields.Many2one('hr.employee', 'Chịu trách nhiệm',
                                         domain="[('department_id', 'child_of', department_id)]")
    color = fields.Integer('Color Index')
    note = fields.Text('Comments', translate=True)

    equipment_ids = fields.One2many('sci.device.main', 'category_id', string='Thiết bị')
    equipment_count = fields.Integer(string="Equipment", compute='_compute_equipment_count')
    maintenance_ids = fields.One2many('sci.maintenance.request', 'category_id', copy=False)
    maintenance_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_count')
    team_ids = fields.One2many('sci.maintenance.team', 'maintenance_category_id', string='Family',
                               help='Family Information')
    team_count = fields.Integer(compute='_compute_team_count')

    @api.onchange('department_id')
    def _onchange_department(self):
        self.name = self.department_id.name

    # count of all custody contracts
    def _compute_team_count(self):
        for each in self:
            custody_ids = self.env['sci.maintenance.team'].search([('maintenance_category_id', '=', each.id)])
            each.team_count = len(custody_ids)

    def _compute_equipment_count(self):
        equipment_data = self.env['sci.device.main'].read_group([('category_id', 'in', self.ids)], ['category_id'],
                                                                ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in equipment_data])
        for category in self:
            category.equipment_count = mapped_data.get(category.id, 0)

    def _compute_maintenance_count(self):
        maintenance_data = self.env['sci.maintenance.request'].read_group([('category_id', 'in', self.ids)],
                                                                          ['category_id'], ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in maintenance_data])
        for category in self:
            category.maintenance_count = mapped_data.get(category.id, 0)


class MaintenanceEquipment(models.Model):
    _inherit = 'sci.device.main'

    category_id = fields.Many2one('sci.maintenance.equipment.category', 'BP quản lý/bảo trì', required=True)
    team_id = fields.Many2one('sci.maintenance.team', string='Đội phụ trách',
                              domain="[('maintenance_category_id', '=', category_id)]")
    maintenance_ids = fields.One2many('sci.maintenance.request', 'equipment_id')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Tổng số yêu cầu sửa chữa")
    certificate_count = fields.Integer(compute='_compute_maintenance_count', string="Tổng số bảo dưỡng định kỳ")
    custody_ids = fields.Many2many('ems.equipment.export', string="Danh sách bàn giao",
                                   domain=[('state', '=', 'approved')])

    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        for item in self:
            item.maintenance_count = len(item.maintenance_ids.filtered(lambda m: m.maintenance_type == 'corrective'))
            item.certificate_count = len(item.maintenance_ids.filtered(lambda m: m.maintenance_type == 'preventive'))

    @api.model
    def update_maintenance(self):
        data = self.search([('activate', '=', 'usage')])
        for record in data:
            if record.first_date_use:
                first_date_use = record.first_date_use
                # Bảo dưỡng định kỳ
                if datetime.datetime.now().date() == record.maintenance_expire_date:
                    payload = {
                        'name': "Bảo dưỡng định kỳ: " + '[' + record.default_code + '] ' + record.name,
                        'code': record.default_code,
                        'maintenance_type': 'preventive',
                        'description': "Yêu cầu bảo dưỡng định kỳ",
                        'category_id': record.category_id.id if record.category_id else None,
                        'priority': '2',
                        'equipment_id': record.id,
                        'request_date': datetime.datetime.now(),
                        'person_name': record.employee_id.name if record.employee_id else None,
                        'email': record.employee_id.work_email if record.employee_id else None,
                        'phone': record.employee_id.work_phone if record.employee_id else None,
                        'department': record.department_id.name if record.department_id else None,
                    }
                    self.env['sci.maintenance.request'].create(payload)
                # Bảo hành
                if record.period:
                    date = first_date_use
                    deadline_repair = self.count_deadline(date, 'months', record.period)
                    days = deadline_repair['days']
                    if days == 0:
                        record.activate = 'out_of_warranty'
        return True


class SCIMaintenanceRequest(models.Model):
    _name = 'sci.maintenance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Maintenance Request'
    _order = "id desc"

    @api.returns('self')
    def _default_stage(self):
        return self.env['sci.maintenance.stage'].search([], limit=1)

    def get_code(self):
        size = 8
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    name = fields.Char('Subjects', required=True)
    code = fields.Char('Code', default=get_code)
    channel = fields.Selection([('website', 'Website'), ('email', 'Email'), ('phone', 'Phone'), ('other', 'Khác')],
                               string='Nguồn/Kênh')
    person_name = fields.Char(string='Người yêu cầu')
    email = fields.Char(string="Email")
    phone = fields.Char(string="Điện thoại")
    department = fields.Char(string="Phòng ban")
    description = fields.Html('Mô tả')
    request_date = fields.Datetime('Ngày yêu cầu', track_visibility='onchange', default=datetime.datetime.now(),
                                   help="Date requested for the maintenance to happen")
    equipment_id = fields.Many2one('sci.device.main', 'Thiết bị/Vật tư', track_visibility="onchange")
    category_id = fields.Many2one('sci.maintenance.equipment.category', 'Bộ phận tiếp nhận', required=True,
                                  track_visibility="onchange")
    maintenance_team_id = fields.Many2one('sci.maintenance.team', string='Đội tiếp nhận',
                                          domain=[('maintenance_category_id', '=', 'category_id')])
    user_id = fields.Many2one('hr.employee', string='Người phụ trách', track_visibility='onchange')
    stage_id = fields.Many2one('sci.maintenance.stage', string='Trạng thái', ondelete='restrict',
                               track_visibility='onchange',
                               group_expand='_read_group_stage_ids', default=_default_stage)
    priority = fields.Selection(
        [('0', 'Rất thấp'), ('1', 'Thấp'), ('2', 'Bình thường'), ('3', 'Cao'), ('4', 'Khẩn cấp')], string='Độ ưu tiên')
    support_rating = fields.Selection(
        [('1', 'Rất thấp'), ('2', 'Thấp'), ('3', 'Bình thường'), ('4', 'Tốt'), ('5', 'Rất tốt')], string='Đánh giá')
    color = fields.Integer('Color Index')
    close_date = fields.Datetime('Ngày đóng', help="Ngày bảo trì hoàn thành. ")
    kanban_state = fields.Selection(
        [('normal', 'In Progress'), ('doing', 'Doing'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
        string='Kanban State', required=True, default='normal', track_visibility='onchange')
    supervisor_ids = fields.Many2many('hr.employee', string='Danh sách nhân sự bảo trì',
                                      track_visibility="onchange", domain="[('active','=','usage')]")
    archive = fields.Boolean(default=False,
                             help="Set archive to true to hide the maintenance request without deleting it.")
    maintenance_type = fields.Selection([('corrective', 'Khắc phục sự cố'), ('preventive', 'Bảo dưỡng định kỳ')],
                                        string='Loại bảo trì', default="corrective", readonly=True)
    schedule_date = fields.Datetime('Lịch hẹn', help="Ngày nhóm bảo trì lên kế hoạch bảo trì ")
    duration = fields.Float(help="Duration in hours and minutes.", string='Thời lượng')
    tools_description = fields.Html('Hiện trạng', translate=True)
    operations_description = fields.Html('Kết quả', translate=True)
    status = fields.Text('Tình trạng', compute="_compute_status")
    attachment_ids = fields.One2many('sci.base.attachment', 'support_ticket_id', 'Attachment Files')
    portal_access_key = fields.Char(string="Portal Access Key")
    support_comment = fields.Text(string="Support Comment")
    close_comment = fields.Html(string="Close Comment")
    closed_by_id = fields.Many2one('res.users', string="Closed By")
    time_to_close = fields.Integer(string="Time to close (seconds)")

    @api.depends('schedule_date')
    def _compute_status(self):
        for record in self:
            if record.stage_id.code in ['new', 'doing']:
                msg = ''
                time = datetime.datetime.now()
                tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
                tz_database = pytz.timezone('UTC')
                time = tz_database.localize(time)
                time = time.astimezone(tz_current)
                time = time.date()
                if record.schedule_date:
                    expected_date = record.schedule_date.date()
                    days = (expected_date - time).days
                    if days < 0:
                        msg += ('- Quá hạn hoàn thành %s ngày') % abs(days)
                    elif days == 0:
                        msg += ('- Hôm nay là hạn chót')
                    elif days < 7:
                        msg += ('- Còn %s ngày đến hạn hoàn thành') % abs(days)
            elif record.stage_id.code == 'done':
                msg = '- Đã hoàn thành'
            elif record.stage_id.code == 'cancel':
                msg = '- Đã hủy'
            else:
                msg = '- Yêu cầu đã được đóng'
            record.status = msg

    @api.onchange('category_id')
    def _onchange_category_id(self):
        for record in self:
            if record.equipment_id and record.equipment_id.category_id != record.category_id:
                record.equipment_id = False

    @api.onchange('category_id')
    def _onchange_category_id_2(self):
        if self.category_id.department_id:
            return {
                'domain': {'user_id': [('department_id', 'child_of', self.category_id.department_id.id)]}
            }

    @api.onchange('maintenance_team_id')
    def _onchange_maintenance_team_id(self):
        self.user_id = self.maintenance_team_id.technician_user_id

    def archive_equipment_request(self):
        self.write({'archive': True})

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(SCIMaintenanceRequest, self).create(vals)
        request.portal_access_key = randint(1000000000, 2000000000)
        if request.category_id.email:
            request.followers()
        return request

    def followers(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = ""
        if self.category_id:
            body += "<p>Dear " + self.category_id.name + ",</p>"
        body += "<p>Bạn vừa nhận được 1 yêu cầu bảo trì/bảo dưỡng.</p>\
                   <p>Chi tiết yêu cầu: <a href='" + base_url + "/web#id=" + str(self.id) + \
                "&model=sci.maintenance.request&view_type=form'>Click vào đây</a></p> <hr/> \
                   <b>Ticket Number:</b> " + str(self.code) + "<br/>"
        if self.maintenance_type == 'corrective':
            body += "<b>Loại bảo trì:</b> Khắc phục sự cố<br/>"
        else:
            body += "<b>Loại bảo trì:</b> Bảo dưỡng định kỳ<br/>"
        if self.category_id:
            body += "<b>Bộ phận phụ trách:</b> " + self.category_id.name + "<br/>"
        if self.person_name:
            body += "<b>Người yêu cầu:</b> " + self.person_name + "<br/>"
        if self.phone:
            body += "<b>Số điện thoại:</b> " + self.phone + "<br/>"
        if self.department:
            body += "<b>Phòng ban/bộ phận:</b> " + self.department + "<br/>"
        if self.description:
            body += "<br/><b>Mô tả:</b><br/>" + self.description + "<br/>"
        lst_email = []
        if self.user_id.work_email:
            lst_email.append(self.user_id.work_email)
        if self.category_id.email:
            lst_email.append(self.category_id.email)
        if len(lst_email) > 0:
            main_employee = {
                'subject': ('SCI-Support: ' + self.name),
                'body_html': body,
                'email_to': ",".join(lst_email),
            }
            self.env['mail.mail'].create(main_employee).send()

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def open_close_ticket_wizard(self):
        return {
            'name': "Gửi đánh giá nhân viên hỗ trợ",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'website.support.ticket.close',
            'context': {'default_ticket_id': self.id},
            'target': 'new'
        }


class WebsiteSupportTicketClose(models.TransientModel):
    _name = "website.support.ticket.close"
    _description = 'Website support ticket close'

    ticket_id = fields.Many2one('sci.maintenance.request', string="Ticket ID")
    message = fields.Html(string="Close Message")

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            values = \
                self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, [self.ticket_id.id])[
                    self.ticket_id.id]
            self.message = values['body']

    def close_ticket(self):
        if self.ticket_id.equipment_id and self.ticket_id.maintenance_type == 'preventive':
            self.ticket_id.equipment_id.last_maintenance = datetime.datetime.now()

        # Also set the date for gamification
        self.ticket_id.close_date = datetime.datetime.now()

        diff_time = self.ticket_id.close_date - self.ticket_id.request_date
        days, seconds = diff_time.days, diff_time.seconds
        self.ticket_id.duration = days * 24 + seconds / 3600

        if self.ticket_id.stage_id:
            message = "<ul class=\"o_mail_thread_message_tracking\">\n<li>State:<span> " + self.ticket_id.stage_id.name + " </span><b>-></b> Nhân viên Closed </span></li></ul>"
        else:
            message = "<ul class=\"o_mail_thread_message_tracking\">\n<li><span> Nhân viên Closed </span></li></ul>"
        self.ticket_id.message_post(body=message, subject="Ticket Closed by Staff")

        self.ticket_id.close_comment = self.message
        self.ticket_id.closed_by_id = self.env.user.id

        ticket_state = self.env['sci.maintenance.stage'].search([('code', '=', 'closed')], limit=1)
        if ticket_state:
            self.ticket_id.stage_id = ticket_state.id

        # Auto send out survey
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        body = ""
        if self.ticket_id.person_name:
            body += "<p>Dear " + self.ticket_id.person_name + ",</p>"
        body += "<p>Chúng tôi muốn nhận được phản hồi của bạn về hỗ trợ</p><p><b><i>" + self.ticket_id.name + "</i></b></p>\
                <p><a href='" + base_url + "/support/survey/" + self.ticket_id.portal_access_key + "'>Click vào đây</a></p> <hr/>\
                <b>Ticket Number:</b> " + self.ticket_id.code + "<br/>"
        if self.ticket_id.category_id:
            body += "<b>Bộ phận hỗ trợ:</b>" + self.ticket_id.category_id.name + "<br/>"
        if self.ticket_id.description:
            body += "<b>Mô tả:</b><br/>" + self.ticket_id.description
        lst_email = []
        if self.ticket_id.email:
            lst_email.append(self.ticket_id.email)
        if len(lst_email) > 0:
            main_employee = {
                'subject': ('SCI-Support: ' + self.ticket_id.name),
                'body_html': body,
                'email_to': ",".join(lst_email),
            }
            self.env['mail.mail'].create(main_employee).send()


class BaseAttachment(models.Model):
    _inherit = "sci.base.attachment"

    support_ticket_id = fields.Many2one('sci.maintenance.request', 'Support ticket', ondelete="cascade")


class MaintenanceTeam(models.Model):
    _name = 'sci.maintenance.team'
    _description = 'Maintenance Teams'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    maintenance_category_id = fields.Many2one('sci.maintenance.equipment.category', string='Bộ phận tiếp nhận',
                                              required=True)
    technician_user_id = fields.Many2one('hr.employee', 'Chịu trách nhiệm')
    member_ids = fields.Many2many('hr.employee', string="Thành viên")
    color = fields.Integer("Color Index", default=0)
    request_ids = fields.One2many('sci.maintenance.request', 'maintenance_team_id', copy=False)

    # For the dashboard only
    todo_request_count = fields.Integer(string="Number of Requests", compute='_compute_todo_requests')
    todo_request_count_date = fields.Integer(string="Number of Requests Scheduled", compute='_compute_todo_requests')
    todo_request_count_block = fields.Integer(string="Number of Requests Blocked", compute='_compute_todo_requests')

    @api.onchange('maintenance_category_id')
    def _onchange_department(self):
        if self.maintenance_category_id.department_id:
            return {
                'domain': {'technician_user_id': [
                    ('department_id', 'child_of', self.maintenance_category_id.department_id.id)],
                           'member_ids': [('department_id', 'child_of', self.maintenance_category_id.department_id.id)]}
            }

    @api.depends('request_ids.stage_id.done')
    def _compute_todo_requests(self):
        for item in self:
            item.todo_request_count = len(item.request_ids.filtered(lambda e: e.kanban_state != 'done'))
            item.todo_request_count_date = len(item.request_ids)
            item.todo_request_count_block = len(item.request_ids.filtered(lambda e: e.kanban_state == 'done'))

    @api.depends('equipment_ids')
    def _compute_equipment(self):
        for item in self:
            item.equipment_count = len(item.equipment_ids)
