from odoo import fields, api, models, _
import datetime
from odoo.exceptions import ValidationError


class SelectService(models.TransientModel):
    _name = 'crm.select.service'
    _description = 'Select Service'

    name = fields.Char('Desc')
    booking_id = fields.Many2one('crm.lead', string='Booking')
    partner_id = fields.Many2one('res.partner', string='Partner')
    # crm_line_ids = fields.Many2many('crm.line', 'select_service_ref', 'crm_line_s', 'select_service_s',
    #                                 string='Services', domain="[('crm_id','=',booking_id), ('stage', '=', 'new')]")
    company_ids = fields.Many2many('res.company', string='Company', compute='set_company_ids', store=True)
    # debt_review = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Debt review', default='no')
    # debt_review_reason = fields.Text('Reason for debt')
    check_booking_date = fields.Boolean('Check booking date', compute='_check_booking')

    @api.depends('booking_id')
    def _check_booking(self):
        for record in self:
            record.check_booking_date = True
            if record.booking_id.booking_date <= datetime.datetime.strptime('2021/11/3 00:00:00', '%Y/%m/%d %H:%M:%S'):
                record.check_booking_date = False

    # @api.onchange('crm_line_ids')
    # def get_uom_price(self):
    #     self.uom_price = 1
    #     self.uom_price = sum(self.crm_line_ids.mapped('uom_price'))

    # @api.constrains('uom_price')
    # def check_limit_uom_price(self):
    #     for rec in self:
    #         limit = sum(rec.crm_line_ids.mapped('uom_price'))
    #         if rec.uom_price > limit:
    #             raise ValidationError(_("allowed limit on cm2/cc/unit/.. field is %s") % limit)

    @api.depends('booking_id')
    def set_company_ids(self):
        for rec in self:
            if rec.booking_id and rec.booking_id.company_id and rec.booking_id.company2_id:
                list = rec.booking_id.company2_id._origin.ids
                list.append(rec.booking_id.company_id.id)
                rec.company_ids = [(6, 0, list)]
            elif rec.booking_id and rec.booking_id.company_id:
                rec.company_ids = [(4, rec.booking_id.company_id.id)]

    def create_quotation(self):
        booking = self.booking_id
        if not self.select_line_ids:
            raise ValidationError('Bạn không thể tạo phiếu khám nếu chưa chọn dịch vụ')
        if booking.stage_id != self.env.ref('crm.stage_lead4'):
            booking.stage_id = 26

        order_line = []
        for record in self.select_line_ids:
            line = record.crm_line_id
            if (line.company_id.brand_id == self.env.ref('sci_brand.res_brand_paris')) and (not line.crm_information_ids):
                raise ValidationError('DỊCH VỤ %s THIẾU THÔNG TIN TƯ VẤN VIÊN' % line.product_id.name)
            line.status_cus_come = 'come'
            sub_vals = {
                'crm_line_id': line.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'uom_price': record.uom_price,
                'company_id': self.env.company.id,
                'product_uom_qty': 1,
                'tax_id': False,
            }
            if line.odontology:
                sub_vals.update({
                    'price_unit': record.amount / record.uom_price,
                    'price_subtotal': record.amount
                })
            else:
                sub_vals.update({
                    'price_unit': line.unit_price,
                    'discount': line.discount_percent,
                    'discount_cash': ((line.discount_cash / (line.quantity * line.uom_price)) * record.uom_price) if line.discount_cash else False,
                    'sale_to': ((line.sale_to / (line.quantity * line.uom_price)) * record.uom_price) if line.sale_to else False,
                    'other_discount': ((line.other_discount / (line.quantity * line.uom_price)) * record.uom_price) if line.other_discount else False,
                })
            order_line.append((0, 0, sub_vals))
        cids = booking.company2_id.ids
        cids.append(booking.company_id.id)
        order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'pricelist_id': booking.price_list_id.id,
            'company_id': self.env.company.id,
            'booking_id': booking.id,
            'campaign_id': booking.campaign_id.id,
            'source_id': booking.source_id.id,
            'note': self.name,
            'order_line': order_line,
            'company_allow_ids': [(6, 0, cids)]
        })
        return order

