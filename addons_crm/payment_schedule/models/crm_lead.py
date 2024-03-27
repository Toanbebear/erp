from odoo import fields, models, api
from odoo.tools.profiler import profile
from datetime import datetime, timedelta


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def create_payment_schedule(self):
        return {
            'name': 'Tạo lịch trình thanh toán',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('payment_schedule.wizard_create_payment_schedule').id,
            'res_model': 'payment.schedule',
            'context': {
                'default_booking': self.id,
            },
            'target': 'new',
        }

    def update_payment_schedule(self):
        """
        Kiểm tra xem các lịch thanh toán đã trả chưa ?
        1. Lấy danh sách các DV được gán với lịch trình thanh toán
        2. Với mỗi dịch vụ đó, lấy ra các lịch thanh toán có ghi ngày và không ghi ngày
        3. Kiểm tra lũy kế số tiền của từng lịch thanh toán với số tiền thực tế đã đóng cho dịch vụ, nếu đủ thì tick paid
        4. Ưu tiên các lịch có điền ngày, đng đủ tiền cho lịch điền ngày rồi mới đến lịch không điền ngày
        """
        if self.statement_service_ids:
            self.statement_service_ids.write({'paid': False})
            services = self.statement_service_ids.mapped('service_id')
            for service in services:
                total_received = sum(self.env['crm.line'].sudo().search(
                    [('service_id', '=', service.id), ('crm_id', '=', self.id)]).mapped('total_received'))
                statements = self.env['statement.service'].sudo().search(
                    [('service_id', '=', service.id), ('booking_id', '=', self.id)])
                total = 0
                statements_date = statements.filtered(lambda sd: sd.scheduled_date)
                flag = True
                if statements_date:
                    statements_date = sorted(statements_date, key=lambda x: x['scheduled_date'])
                    for statement_date in statements_date:
                        if total + statement_date.amount <= total_received:
                            statement_date.paid = True
                            total += statement_date.amount
                        else:
                            flag = False
                            break
                if flag:
                    statements_not_date = statements.filtered(lambda sd: not sd.scheduled_date)
                    if statements_not_date:
                        statements_not_date = sorted(statements_not_date, key=lambda x: x['id'])
                        for statement_not_date in statements_not_date:
                            if total + statement_not_date.amount <= total_received:
                                statement_not_date.paid = True
                                total += statement_not_date.amount
                            else:
                                break

    show_notification = fields.Char('Ngày thanh toán', compute='check_statement')

    @api.depends('statement_service_ids.scheduled_date')
    def check_statement(self):
        current_date = datetime.now().date()
        for record in self:
            record.show_notification = False
            if record.statement_service_ids:
                date_check = current_date + timedelta(days=1)
                notification = ''
                overdue_payment = record.statement_service_ids.filtered(lambda ss: (not ss.paid) and ss.scheduled_date and (ss.scheduled_date < current_date))
                if overdue_payment:
                    notification += '\nKhách hàng %s CÒN NỢ %sđ từ những lần thanh toán trước đó.' % (str(record.partner_id.name).upper(), '{0:,.0f}'.format(sum(overdue_payment.mapped('amount'))))
                payment_due = record.statement_service_ids.filtered(lambda ss: (not ss.paid) and ss.scheduled_date and (ss.scheduled_date <= date_check) and (ss.scheduled_date >= current_date))
                if payment_due:
                    payment_due = min(payment_due, key=lambda ss: ss.scheduled_date)
                amount_due = record.statement_service_ids.filtered(lambda ss: (not ss.paid) and ss.scheduled_date and (ss.scheduled_date == payment_due.scheduled_date))
                if payment_due:
                    notification += '\nKhách hàng %s cần thanh toán %sđ vào ngày %s' % (str(record.partner_id.name).upper(), '{0:,.0f}'.format(sum(amount_due.mapped('amount'))), payment_due.scheduled_date.strftime('%d/%m/%Y'))
                record.show_notification = notification




