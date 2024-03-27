from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EmployeeQuit(models.TransientModel):
    _name = 'employee.quit'
    _description = 'Tool lưu trữ nhân viên nghỉ việc'

    import_data = fields.Char('Email nhân viên', help='Danh sách Email nhân viên nghỉ việc')
    employee_ids = fields.Many2many('hr.employee', string='Danh sách nhân viên')

    @api.onchange('import_data')
    def get_employee_ids(self):
        if self.import_data:
            list_email = list(self.import_data.split(" "))
            employee_ids = self.env['hr.employee'].sudo().search([('work_email','in',list_email)])
            if employee_ids:
                self.employee_ids = employee_ids.ids
            else:
                raise ValidationError("Không tìm thấy nhân viên")
        else:
            self.employee_ids = None

    def disable(self):
        employee_disable = """
        update hr_employee
        set active = false
        where id in %s
        """
        self.env.cr.execute(employee_disable, [tuple(self.employee_ids.ids)])
        user_disable="""
        update res_users
        set active = false
        where id in %s
        """
        self.env.cr.execute(user_disable, [tuple(self.employee_ids.user_id.ids)])
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = "Nhân viên đã được lưu trữ thành công. Nếu có vấn đề kỹ thuật, vui lòng liên hệ phòng Công nghệ thông tin. Xin cảm ơn."
        return {
            'name': 'THÔNG BÁO THÀNH CÔNG',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view_id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

