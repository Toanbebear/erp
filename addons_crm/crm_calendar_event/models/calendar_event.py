from odoo import models, fields, api
from datetime import timedelta, datetime
import pytz

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    customer_id = fields.Many2one('res.partner', string='Khách hàng')
    domain_physician = fields.Many2many('sh.medical.physician', compute="_get_physician_by_start_datetime")
    physician = fields.Many2one('sh.medical.physician', string='Bác sĩ/Trợ thủ',
                                domain="[('id','not in',domain_physician)]")
    services = fields.Many2many('sh.medical.health.center.service', string='Danh sách dịch vụ')
    company_id = fields.Many2one('res.company', string='Chi nhánh', domain="[('id', 'in', allowed_company_ids)]",
                                 default=lambda self: self.env.company)
    opportunity_id = fields.Many2one('crm.lead', 'Booking',
                                     domain="[('type', '=', 'opportunity'), ('partner_id', '=', customer_id)]")
    phonecall = fields.Many2one('crm.phone.call', string='PhoneCall')
    duration = fields.Float('Duration', states={'done': [('readonly', True)]}, default=0.5)
    state = fields.Selection([('confirm', 'Xác nhận'), ('come', 'Đã dến'), ('cancel', 'Đã hủy')], string='Trạng thái', default='confirm')
    color = fields.Integer('Color Index', default=4, tracking=True)
    is_calendar_surgery = fields.Boolean('Đây là lịch phẫu thuật')
    thanh_toan = fields.Selection([('coc', 'Cọc'), ('thanh_toan_du', 'Thanh toán đủ')], string="Thanh toán")
    consultant = fields.Text('Nhân viên tư vấn')
    is_labtest = fields.Boolean('Đã xét nghiệm')
    anesthetist_type = fields.Selection([('me', 'Mê'), ('te', 'Tê'), ('khac', 'Khác')], string='Phương pháp vô cảm')
    arrival_date = fields.Datetime('Ngày đến viện')
    surgery_date = fields.Datetime('Ngày mổ')
    guaranty_physician = fields.Many2one('sh.medical.physician', string='Bác sĩ chỉ định BH')
    ekip_gay_me = fields.Text('Ekip gây mê')
    phu_mo = fields.Many2many('sh.medical.physician', 'physician_calendar_rel', string='Điều dưỡng phụ mổ')
    room = fields.Text('Phòng mổ')
    pcr = fields.Text('PCR')

    @api.depends('start_datetime', 'stop_datetime')
    def _get_physician_by_start_datetime(self):
        for record in self:
            record.domain_physician = False
            if record.start_datetime and record.stop_datetime:
                start_datetime = record.start_datetime + timedelta(hours=7)
                end_datetime = record.start_datetime + timedelta(hours=7)
                physicians = record.env['doctor.schedule'].search(
                    [('start_datetime', '<=', start_datetime),
                     ('end_datetime', '>=', end_datetime)]).mapped('physician')
                record.domain_physician = [(6, 0, physicians.ids)]

    @api.onchange('start_datetime', 'duration')
    def refresh_physician(self):
        self.physician = False

    def view_calendar_event(self):
        return {
            'name': 'Lịch hẹn',  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('calendar.view_calendar_event_form').id,
            'res_model': 'calendar.event',  # model want to display
            'target': 'current',  # if you want popup,
            # 'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

    @api.onchange('opportunity_id')
    def get_service(self):
        self.services = False
        if self.opportunity_id:
            crm_line = self.env['crm.line'].sudo().search([('crm_id', '=', self.opportunity_id.id)])
            return {'domain': {'services': [('id', 'in', crm_line.mapped('service_id').ids)]}}

    def change_calender_evt(self, *args):
        return {
            'name': 'Đi đến Booking',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.opportunity_id.id,
            'views': [(self.env.ref('crm_base.crm_lead_form_booking').id, 'form')],
        }

    def change_calender_state_cancel(self):
        self.state = 'cancel'
        return {}

    def calendar_state_cancel(self):
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        res = super(CalendarEvent, self).create(vals)
        if res.name and res.start_datetime and res.duration:
            end_time = res.start_datetime + timedelta(hours=7) + timedelta(hours=res.duration)
            if not res.is_calendar_surgery:
                res.name += ' %s - %s' %(res.start_datetime.strftime('%H:%M'), end_time.strftime('%H:%M'))
            else:
                res.name += '- Bác sĩ: %s - Khách hàng: %s - %s - %s' % (res.physician.name, res.customer_id.name, res.start_datetime.strftime('%H:%M'), end_time.strftime('%H:%M'))

        return res
