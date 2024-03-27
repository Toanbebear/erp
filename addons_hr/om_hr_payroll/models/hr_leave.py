from datetime import datetime
from odoo import fields, models, api


class HRAttendanceClearData(models.Model):
    _inherit = 'hr.attendance'

    # Thêm mới field đánh dấu là dữ liệu nghỉ phép.
    is_leave_line = fields.Many2one(comodel_name='hr.leave', string="HR leave")
    # Them truong loai nghi phep
    leave_type = fields.Many2one(comodel_name='hr.leave.type', string='Leave type')

    @api.model
    def get_data_leave(self, start_time, end_time):
        # Lấy dữ liệu từ bảng nghỉ phép hr.leave sang bảng hr.attendance với điều kiện:
        #       Dữ liệu nghỉ phép đã được chuyển thì không lấy.
        #       Dữ liệu nghỉ phép phải ở trạng thái đã được duyệt.
        #       Dữ liệu nghỉ phép trong khoảng thời gian.

        # start_time = date(2021, 6, 1)
        # end_time = date(2021, 6, 30)

        hr_attendance = self.env['hr.attendance']
        hr_leave = self.env['hr.leave']
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        data_attendance = hr_attendance.search([])
        line_leave_ids = data_attendance.mapped(lambda leave: leave.is_leave_line).ids

        data_leave = hr_leave.search([('state', '=', 'validate'),
                                      ('request_date_from', '>=', start_time),
                                      ('request_date_to', '<=', end_time),
                                      ('id', 'not in', line_leave_ids)])
        rec = []
        for line in data_leave:
            if line.employee_id:
                rec.append = ({
                    'is_leave_line': line.id,
                    'employee_id': line.employee_id.id,
                    'state': 'validate',
                    'approver_id': current_employee.id,
                    'resign_confirm_date': datetime.now(),
                    'workday': None,
                    'reason': line.holiday_status_id.display_name,
                    'leave_type': line.holiday_status_id.id,
                    'check_in': line.request_date_from,
                    'check_out': line.request_date_to,
                    'name': line.holiday_status_id.code
                })


class HRLeaveInherit(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
        result = super(HRLeaveInherit, self).action_approve()
        data_attendance = self.env['hr.attendance'].sudo()
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        rec = ({
            'is_leave_line': self.id,
            'employee_id': self.employee_id.id,
            'state': 'validate',
            'approver_id': current_employee.id,
            'resign_confirm_date': datetime.now(),
            'workday': None,
            'reason': self.holiday_status_id.display_name,
            'leave_type': self.holiday_status_id.id,
            'check_in': self.request_date_from,
            'check_out': self.request_date_to,
            'name': self.holiday_status_id.code
        })

        data_attendance.create(rec)

        return result

    def action_refuse(self):
        result = super(HRLeaveInherit, self).action_refuse()
        data_attendance = self.env['hr.attendance']
        line_attendance = data_attendance.search([('is_leave_line', '=', self.id)], limit=1)
        if line_attendance:
            line_attendance.unlink()
        return result
