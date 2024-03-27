# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class HRLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    expiration_date = fields.Date(string='Expiration date')
    remaining_days = fields.Float(string='Remaining days')
    attendance = fields.Many2one('hr.attendance')

    def holiday_expires(self):
        today = fields.Date.today()
        hr_leave_allocation = self.env['hr.leave.allocation'].search([('state', '=', 'validate')])
        for record in hr_leave_allocation:
            if record.expiration_date:
                if today > record.expiration_date:
                    self.env['hr.leave'].create({
                        'employee_id': record.employee_id.id,
                        'holiday_status_id': record.holiday_status_id.id,
                        'holiday_type': record.holiday_type,
                        'name': 'Hết hạn phép',
                        'date_from': today,
                        'date_to': today,
                        'number_of_days': record.remaining_days,
                        'state': 'validate',
                    })

    @api.constrains('state', 'number_per_interval')
    def get_remaining_days(self):
        if self.allocation_type == 'regular':
            if self.state == 'validate':
                self.remaining_days = self.number_of_days
        else:
            if self.state == 'validate':
                self.remaining_days += self.number_per_interval



