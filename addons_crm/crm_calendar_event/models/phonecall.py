from odoo import models, fields, api
from datetime import timedelta, MAXYEAR
from odoo.exceptions import ValidationError


class PhoneCallCalendar(models.Model):
    _inherit = "crm.phone.call"

    domain_physician = fields.Many2many('sh.medical.physician', compute="_get_physician_by_booking_date")
    physician = fields.Many2one('sh.medical.physician', string='Bác sĩ/Trợ thủ',
                                domain="[('id','not in',domain_physician)]")

    def create_an_appointment(self):
        self.ensure_one()
        return {
            'name': 'Tạo lịch hẹn',
            'view_mode': 'form',
            'res_model': 'create.an.appointment',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('crm_calendar_event.form_create_calendar_event_from_booking').id,
            'context': {
                'default_customer_id': self.partner_id.id,
                'default_opportunity_id': self.crm_id.id,
            },
            'target': 'new',
        }

    @api.depends('booking_date')
    def _get_physician_by_booking_date(self):
        for record in self:
            record.domain_physician = False
            if record.booking_date:
                end_date = record.booking_date + timedelta(hours=1)
                physicians = record.env['doctor.schedule'].search(
                    [('start_datetime', '<=', record.booking_date),
                     ('end_datetime', '>=', end_date)]).mapped('physician')
                record.domain_physician = [(6, 0, physicians.ids)]

    @api.onchange('booking_date')
    def clear_physician(self):
        self.physician = False

    def write(self, vals):
        res = super(PhoneCallCalendar, self).write(vals)
        for rec in self:
            phonecall_confirm = self.env.ref('crm_base.type_phone_call_confirm_appointment')
            phonecall_exam_schedule = self.env.ref('crm_base.type_phone_call_exam_schedule')
            list_phonecall = [phonecall_confirm]
            phoncall_lieutrinh = self.env['crm.type'].search([('name', '=', 'Hẹn lịch liệu trình')], limit=1)
            if phoncall_lieutrinh:
                list_phonecall.append(phoncall_lieutrinh)
            calendar_phonecall = self.env['calendar.event'].search(
                [('opportunity_id', '=', rec.crm_id.id), ('phonecall', '=', rec.id), ('state', '=', 'confirm')])
            if (rec.type_crm_id in list_phonecall) and rec.crm_id and (rec.state == 'connected_2'):
                if not calendar_phonecall:
                    name = '[%s]%s - %s' % (rec.crm_id.name, rec.partner_id.name ,rec.type_crm_id.name)
                    self.env['calendar.event'].sudo().create({
                        'name': name,
                        'customer_id': rec.partner_id.id,
                        'user_id': self.env.user.id,
                        'start': rec.booking_date,
                        'stop': rec.booking_date + timedelta(hours=1),
                        'duration': 1,
                        'physician': rec.physician.id,
                        'alarm_ids': [(6, 0, [self.env.ref('calendar.alarm_notif_1').id])],
                        'services': [(6, 0, rec.crm_line_id.mapped('service_id').ids)] if rec.crm_line_id else False,
                        'opportunity_id': rec.crm_id.id if rec.crm_id else False,
                        'phonecall': rec.id,
                        'company_id': rec.company_id.id,
                        'location': rec.company_id.name,
                        'state': 'confirm',
                    })
                if rec.crm_id.stage_id == self.env.ref('crm_base.crm_stage_not_confirm'):
                    rec.crm_id.stage_id = self.env.ref('crm_base.crm_stage_confirm').id

            elif (rec.type_crm_id == phonecall_exam_schedule) and rec.crm_id and (rec.state == 'connected_2') and not calendar_phonecall:
                name = '[%s]%s' % (rec.type_crm_id.name, rec.crm_id.name)
                self.env['calendar.event'].sudo().create({
                    'name': name,
                    'customer_id': rec.partner_id.id,
                    'user_id': self.env.user.id,
                    'start': rec.booking_date,
                    'stop': rec.booking_date + timedelta(hours=1),
                    'duration': 1,
                    'physician': rec.physician.id,
                    'alarm_ids': [(6, 0, [self.env.ref('calendar.alarm_notif_1').id])],
                    'services': [(6, 0, rec.service_id.ids)] if rec.service_id else False,
                    'opportunity_id': rec.crm_id.id if rec.crm_id else False,
                    'phonecall': rec.id,
                    'company_id': rec.company_id.id,
                    'location': rec.company_id.name,
                    'state': 'confirm',
                })
        return res
