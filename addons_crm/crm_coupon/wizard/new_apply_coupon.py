from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime, date
import itertools

COUPON_TYPE = [('1', 'Coupon đơn lẻ'), ('2', 'Coupon áp dụng cho đơn hàng'), ('3', 'Coupon cho combo dịch vụ'),
               ('4', 'Coupon cho liệu trình'), ('5', 'Coupon cho nhóm khách hàng'), ('6', 'Coupon cho hạng thẻ'),
               ('7', 'Coupon cho khách hàng mới/cũ'), ('8', 'Coupon cho dịch vụ đã sử dụng')]


class InheritApplyCoupon(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon New'

    apply_coupon_list_ids = fields.One2many('crm.apply.coupon.list', 'apply_coupon_id', string='Danh sách coupon')
    show_group = fields.Boolean(default=False)

    def check_group_customer(self):
        today = datetime.today().strftime('%Y-%m-%d')
        group_ids = self.env['crm.group.customer'].search([('status', '=', 'enable'),
                                                           ('partner_ids', 'in', self.partner_id.ids)])
        for group in group_ids:
            create_date = group.create_date.strftime('%Y-%m-%d')
            if create_date == today:
                self.group_customer_id = group.id
                self.show_group = True
                return True
            else:
                return False

    # sap xep thu tu coupon, uu tien coupon combo len dau
    def list_coupon_sorted(self):
        order_list = ['3', '1', '2', '4', '5', '6', '7']
        coupon_ids = self.env['crm.discount.program'].search([('campaign_id', '=', self.campaign_id.id)])
        # result = self.env['crm.discount.program'].search([('id', '=', '0')])
        result = self.env['crm.discount.program']
        for order in order_list:
            for coupon in coupon_ids:
                if coupon.coupon_type == order:
                    result += coupon
        return result

    @api.onchange('campaign_id')
    def coupon_list_available(self):
        self.apply_coupon_list_ids = None
        if self.campaign_id:
            have_group = self.check_group_customer()
            coupon_ids = self.list_coupon_sorted()
            for coupon in coupon_ids:
                if coupon.coupon_type != '2':
                    list_index = self.check_suitable_combo(self.list_available_combo(coupon))
                    for index in list_index:
                        if coupon.coupon_type != '5' or have_group is True:
                            coupon_detail_id = self.env['crm.discount.program.list'].search([('discount_program', '=', coupon.id), ('index', '=', index)], limit=1)
                            self.env['crm.apply.coupon.list'].create({
                                'apply_coupon_id': self.id,
                                'index': index,
                                'coupon_id': coupon.id,
                                'description': coupon_detail_id.combo_note
                            })
                else:
                    check_bill = True
                    coupon_bill_ids = coupon.coupon_bill_ids.sorted(key=lambda r: r.total_min)[::-1]
                    bill_total = 0
                    if coupon.country_id and coupon.country_id.id != self.crm_id.country_id.id:
                        check_bill = False
                    if coupon.state_ids and self.crm_id.state_id.id not in coupon.state_ids.ids:
                        check_bill = False
                    if coupon.product_cate_ids:
                        service = self.env['crm.line'].search([('crm_id', '=', self.crm_id.id), (
                            'service_id.service_category.id', 'in', coupon.product_cate_ids.ids)])
                        if len(service) == 0:
                            check_bill = False
                    for line in self.line_ids:
                        bill_total += line.total
                    for discount in coupon_bill_ids:
                        if bill_total >= discount.total_min and check_bill is True:
                            self.env['crm.apply.coupon.list'].create({
                                'apply_coupon_id': self.id,
                                'index': 0,
                                'coupon_id': coupon.id,
                                'description': discount.description
                            })
                            break




class ApplyCouponList(models.TransientModel):
    _name = 'crm.apply.coupon.list'
    _description = 'Apply Coupon List'

    apply_coupon_id = fields.Many2one('crm.apply.coupon')
    index = fields.Integer(string='Index')
    coupon_id = fields.Many2one('crm.discount.program', string='Coupon', readonly=True)
    description = fields.Html(string='Combo describe')
    type_coupon = fields.Selection(COUPON_TYPE, string='Loại coupon', related='coupon_id.coupon_type')

    def apply_coupon(self):
        apply_coupon = self.env['crm.apply.coupon'].search([('id', '=', self.apply_coupon_id.id)])
        apply_coupon.coupon_id = self.coupon_id.id
        apply_coupon.index = self.index
        apply_coupon.check_type_coupon()



