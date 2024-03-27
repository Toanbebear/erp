from odoo import fields, models, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    half_day_off = fields.Boolean(string='Nghỉ nửa ngày', default=False)
    hr_attendance = fields.Many2one('hr.attendance')
    hr_leave_allocation = fields.Many2one('hr.leave.allocation')

    @api.onchange('half_day_off')
    def calculate_half_day_break(self):
        if self.half_day_off == True:
            self.number_of_days = 0.5
            self.date_to = self.date_from
        else:
            self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)['days']

    @api.constrains('state')
    def assign_hr_leave_allocation(self):
        if self.state == 'validate':
            hr_leave_allocation = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('holiday_status_id', '=', self.holiday_status_id.id),
                 ('state', '=', 'validate'),
                 ('remaining_days', '>', '0  ')], limit=1, order='id asc')
            if hr_leave_allocation:
                self.hr_leave_allocation = hr_leave_allocation.id
                hr_leave_allocation.remaining_days -= self.number_of_days


    @api.constrains('state')
    def minus_remaining_days(self):
        if self.state == 'refuse':
            hr_leave_allocation = self.env['hr.leave.allocation'].search([('id', '=', self.hr_leave_allocation.id)])
            hr_leave_allocation.remaining_days += self.number_of_days