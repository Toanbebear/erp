from odoo import fields, api, models
from odoo.exceptions import ValidationError


class CRM(models.Model):
    _inherit = 'crm.lead'

    def select_service(self):
        company = self.env.user.company_id.id
        return {
            'name': 'Lựa chọn dịch vụ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_crm_select_service').id,
            'res_model': 'crm.select.service',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_booking_id': self.id,
                'default_height': self.partner_id.height,
                'default_weight': self.partner_id.weight,
                'default_institution': self.env['sh.medical.health.center'].sudo().
                search([('his_company', '=', self.env.company.id)], limit=1).id,
            },
            'target': 'new',
        }

    walkin_ids = fields.One2many('sh.medical.appointment.register.walkin', 'booking_id', string='Walkin')
    group_booking = fields.Many2many('crm.lead', 'booking_to_group_booking_rel', 'booking_id', 'group_booking_ids',
                                     string='Group booking', domain="[('type','=','opportunity')]")

    def add_service_guarantee(self):
        return {
            'name': 'THÊM DỊCH VỤ BẢO HÀNH',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_his_13.view_form_add_service_guarantee').id,
            'res_model': 'add.service.guarantee',
            'context': {
                'default_partner': self.partner_id.id,
                'default_crm_id': self.id,
                'default_brand_id': self.brand_id.id,
            },
            'target': 'new',
        }

    def write(self, vals):
        res = super(CRM, self).write(vals)
        for record in self:
            if vals.get('group_booking') and (
                    record.id not in record.group_booking.group_booking.ids):
                record.group_booking.write({'group_booking': [(4, record.id)]})
            else:
                pass
        return res

    @api.model
    def create(self, vals_list):
        if vals_list.get('group_booking'):
            res = super(CRM, self).create(vals_list)
            res.group_booking.write({'group_booking': [(4, res.id)]})
        else:
            res = super(CRM, self).create(vals_list)
        return res

    def request_deposit(self):
        # if (not self.crm_line_ids) and (not self.crm_line_product_ids):
        #     raise ValidationError('Để có thể đặt cọc, Booking cần có dịch vụ hoặc sản phẩm!')
        journal_id = self.env['account.journal'].search(
            [('company_id', '=', self.env.company.id), ('type', '=', 'cash'),
             ('currency_id', '=', self.env.ref('base.VND').id)], limit=1)
        return {
            'name': 'Yêu cầu thu/hoàn tiền',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.form_request_deposit_wizard').id,
            'res_model': 'crm.request.deposit',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_booking_id': self.id,
                'default_brand_id': self.brand_id.id,
                'default_company_id': self.company_id.id,
                'default_currency_id': self.currency_id.id,
                'default_payment_date': fields.Date.today(),
                'default_payment_method': 'tm',
                'default_journal_id': journal_id.id if journal_id else False
            },
            'target': 'new',
        }

    def request_refund(self):
        if self.amount_remain <= 0:
            raise ValidationError('Khách hàng không đủ tiền để hoàn!')
        return {
            'name': 'Yêu cầu hoàn tiền',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_his_13.form_request_refund_wizard').id,
            'res_model': 'crm.request.refund',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_booking_id': self.id,
                'default_brand_id': self.brand_id.id,
                'default_company_id': self.company_id.id,
                'default_currency_id': self.currency_id.id,
                # 'default_payment_date': fields.Date.today(),
                # 'default_payment_method': 'tm',
                # 'default_journal_id': journal_id.id if journal_id else False
            },
            'target': 'new',
        }
