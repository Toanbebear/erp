from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, date
STAGE = [('enable', 'Có thể dùng'), ('disable', 'Không thể dùng')]


class CRMGroupCustomer(models.Model):
    _name = 'crm.group.customer'
    _description = 'List group customer to apply coupon type 5'
    _rec_name = 'code'

    code = fields.Char(string='Mã chi tiết', default="/", readonly=True,)
    coupon_id = fields.Many2one('crm.discount.program', string='Mã Coupon', required=True)
    coupon_detail_id = fields.Many2one('crm.discount.program.list', string='Coupon chi tiết', required=True)
    partner_ids = fields.Many2many('res.partner', string='Tên khách hàng', required=True)
    booking_ids = fields.Many2many('crm.lead', string='Booking', readonly=True)
    create_date = fields.Date(string='Ngày tạo', readonly=False)
    status = fields.Selection(STAGE, string='Tình trạng', readonly=True, compute='_change_status_group',store=True)

    @api.depends('coupon_detail_id')
    def _change_status_group(self):
        for rec in self:
            if len(rec.booking_ids) < len(rec.partner_ids):
                rec.status = 'enable'
            else:
                rec.status = 'disable'

    def unlink(self):
        if self.booking_ids:
            raise ValidationError('Không thể xóa nhóm khách hàng khi đã được sử dụng')

    def write(self, vals):
        if self.coupon_id:
            for rec in self.env['crm.group.customer'].search([('id', '!=', self.id)]):
                if rec.coupon_id == self.coupon_id and\
                        rec.coupon_detail_id == self.coupon_detail_id and\
                        rec.partner_ids.ids == self.partner_ids.ids and\
                        rec.create_date == self.create_date:
                    raise ValidationError('Không thể tạo 2 nhóm khách hàng giống nhau')

        result = super(CRMGroupCustomer, self).write(vals)
        return result

    @api.onchange('coupon_id')
    def disable_change_coupon_id(self):
        if self.booking_ids:
            raise ValidationError('Không thể sửa nhóm khách hàng khi đã được sử dụng')

    @api.onchange('coupon_detail_id')
    def disable_change_coupon_detail_id(self):
        if self.booking_ids:
            raise ValidationError('Không thể sửa nhóm khách hàng khi đã được sử dụng')

    @api.onchange('partner_ids')
    def disable_change_partner_ids(self):
        if self.booking_ids:
            raise ValidationError('Không thể sửa nhóm khách hàng khi đã được sử dụng')

    @api.model
    def create(self, vals):
        obj = super(CRMGroupCustomer, self).create(vals)
        if obj.code == '/':
            number = self.env['ir.sequence'].get('crm.group.customer.code') or '/'
            obj.write({'code': str(obj.coupon_id.brand_id.code) + number})
        return obj

    @api.onchange('partner_ids')
    def limit_group_create(self):
        if self.coupon_detail_id:
            if len(self.partner_ids) > self.coupon_detail_id.group_max:
                raise ValidationError('Đã tạo quá số lượng khách đi cùng tối đa của coupon')

        else:
            if self.partner_ids:
                raise ValidationError('Chọn coupon chi tiết trước!')

    @api.constrains('partner_ids')
    def constraint_partners(self):
        if self.coupon_detail_id:
            if len(self.partner_ids) < self.coupon_detail_id.group_min:
                raise ValidationError('Số lượng khách tối thiểu của coupon là :' + str(self.coupon_detail_id.group_min))














