from calendar import monthrange
from datetime import date, datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError


class collaboratorTransactionCancelWizard(models.TransientModel):
    _name = 'collaborator.transaction.cancel.wizard'
    _description = 'Hủy dòng giao dịch CTV'

    transaction_id = fields.Many2one('collaborator.transaction', string="Dòng giao dịch")
    collaborator_id = fields.Many2one('collaborator.collaborator', string="Cộng tác viên", related='transaction_id.collaborator_id')
    sale_order = fields.Many2one('sale.order', string="SO", related='transaction_id.sale_order')
    booking_id = fields.Many2one('crm.lead', string='Booking', related='transaction_id.booking_id')
    company_id = fields.Many2one('res.company', string='Công ty', related='transaction_id.company_id')
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám', related='transaction_id.walkin_id')
    service_date = fields.Date('Ngày hoàn thành', help='Ngày hoàn thành dịch vụ', related='transaction_id.service_date')
    amount_total = fields.Monetary('Tiền KH làm dịch vụ', related='transaction_id.amount_total')
    discount_percent = fields.Float('Hoa hồng(%)', store=True, tracking=True, related='transaction_id.discount_percent')
    amount_used = fields.Monetary('Tiền hoa hồng', related='transaction_id.amount_used')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ',
                                  default=lambda self: self.env.company.currency_id)
    service_id = fields.Many2one('product.product', string='Dịch vụ', tracking=True, related='transaction_id.service_id')
    contract_id = fields.Many2one('collaborator.contract', string='Hợp đồng', related='transaction_id.contract_id')
    note = fields.Text('Ghi chú')



    def cancel(self):
        for rec in self.transaction_id:
            if rec.check_transaction == False:
                rec.check_transaction = True
                transaction = rec.env['collaborator.transaction'].sudo().create({
                    'collaborator_id': self.collaborator_id.id,
                    'company_id':  self.company_id.id,
                    'brand_id':  rec.brand_id.id,
                    'booking_id': self.booking_id.id,
                    'sale_order': self.sale_order.id,
                    'walkin_id': self.walkin_id.id,
                    'service_date': self.service_date,
                    'amount_used': self.amount_used * -1,
                    'amount_total': self.amount_total,
                    'discount_percent': self.discount_percent,
                    'currency_id': self.currency_id.id,
                    'service_id': self.service_id.id,
                    'company_id_so': rec.company_id_so.id,
                    'check_transaction': True,
                    'note': self.note,
                })
                return {
                    'name': 'Thông tin giao dịch mới',
                    'type': 'ir.actions.act_window',
                    'res_model': 'collaborator.transaction',
                    'view_mode': 'form',
                    'res_id': transaction.id,
                    'target': 'current',
                }
            else:
                raise UserError(_('Bạn đã hủy giao dịch này, bạn không thể hủy tiếp !!!'))




