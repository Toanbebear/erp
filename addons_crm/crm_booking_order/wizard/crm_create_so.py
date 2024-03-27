import datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CRMCreateSaleOrder(models.TransientModel):
    _name = 'crm.create.sale.order'
    _description = 'Wizard create sale order from Booking'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.company.id)
    brand_id = fields.Many2one(related="company_id.brand_id")
    product_pricelist_id = fields.Many2one('product.pricelist', string='Bảng giá',
                                           domain="[('brand_id', '=', brand_id), ('type', '=', 'product')]")
    line_product_ids = fields.Many2many('crm.line.product', string='Sản phẩm',
                                        domain="[('booking_id', '=', booking_id), ('stage_line_product', '=', 'new')]")
    sh_room_id = fields.Many2one('sh.medical.health.center.ot', string='Phòng xuất hàng',
                                 domain="[('institution.his_company', '=', company_id)]")
    notification = fields.Text('Thông báo', compute='get_notification')

    # def _get_location_by_categ(self):
    #     """Lấy địa điểm theo phòng bệnh viện và nhóm sản phẩm"""
    #     # room = self.order_id.sh_room_id
    #     location = self.env['stock.location']
    #     if self.product_id.categ_id == self.env.ref('shealth_all_in_one.sh_medicines') and self.sh_room_id.location_medicine_stock:
    #         location = self.sh_room_id.location_medicine_stock
    #     elif self.product_id.categ_id == self.env.ref('shealth_all_in_one.sh_supplies') and self.sh_room_id.location_sale_stock:
    #         location = self.sh_room_id.location_sale_stock
    #     return location

    @api.depends('line_product_ids', 'sh_room_id')
    def get_notification(self):
        self.notification = False
        if self.sh_room_id and self.line_product_ids:
            validate_str = ''
            for line_product in self.line_product_ids:
                if line_product.product_uom_qty > 0:
                    location = self.env['stock.location']
                    if line_product.product_id.categ_id == self.env.ref(
                            'shealth_all_in_one.sh_medicines') and self.sh_room_id.location_medicine_stock:
                        location = self.sh_room_id.location_medicine_stock
                    elif line_product.product_id.categ_id == self.env.ref(
                            'shealth_all_in_one.sh_supplies') and self.sh_room_id.location_sale_stock:
                        location = self.sh_room_id.location_sale_stock
                    quantity_on_hand = self.env['stock.quant']._get_available_quantity(line_product.product_id,
                                                                                       location)
                    qty_sale = line_product.product_uom._compute_quantity(line_product.product_uom_qty,
                                                                          line_product.product_id.uom_id)
                    if quantity_on_hand < qty_sale:
                        validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                            line_product.product_id.default_code, line_product.product_id.name, str(quantity_on_hand),
                            str(line_product.product_id.uom_id.name), location.name)
            if validate_str != '':
                self.notification = """Các SP sau đang không đủ số lượng tại tủ xuất:\n """ + validate_str + """\n Hãy liên hệ với quản lý kho"""

    def create_so(self):
        if not self.line_product_ids:
            raise ValidationError('Bạn cần chọn sản phẩm trước khi tạo đơn bán hàng nháp!!!')
        else:
            # if not self.booking_id.loyalty_id:
            #     loyalty_id = self.env['crm.loyalty.card'].search(
            #         [('partner_id', '=', self.partner_id.id),
            #          ('brand_id', '=', self.booking_id.company_id.brand_id.id)])
            #     if loyalty_id:
            #         self.booking_id.loyalty_id = loyalty_id.id
            #     else:
            #         loyalty = self.env['crm.loyalty.card'].create({
            #             'partner_id': self.partner_id.id,
            #             'company_id': self.booking_id.company_id.id,
            #             'date_interaction': fields.Datetime.now(),
            #             'source_id': self.booking_id.source_id.id,
            #         })
            #         self.booking_id.loyalty_id = loyalty.id
            #         rank_now = self.env['crm.loyalty.rank'].search(
            #             [('money_fst', '<=', loyalty.amount),
            #              ('money_end', '>=', loyalty.amount),
            #              ('brand_id', '=', self.booking_id.company_id.brand_id.id)], limit=1)
            #         loyalty.rank_id = rank_now.id
            order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'pricelist_id': self.product_pricelist_id.id,
                'company_id': self.company_id.id,
                'booking_id': self.booking_id.id,
                'sh_room_id': self.sh_room_id.id if self.sh_room_id else False,
                'campaign_id': self.booking_id.campaign_id.id,
                'source_id': self.booking_id.source_id.id,
                'pricelist_type': 'product',
                'note': 'Bán sản phẩm'
            })
            for record in self.line_product_ids:
                if self.product_pricelist_id != record.product_pricelist_id:
                    raise ValidationError('Sai bảng giá')
                else:
                    order_line = self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'company_id': self.company_id.id,
                        'product_id': record.product_id.id,
                        'line_product': record.id,
                        'price_unit': record.price_unit,
                        'product_uom': record.product_id.uom_so_id.id,
                        'product_uom_qty': record.product_uom_qty,
                        'discount': record.discount_percent,
                        'discount_cash': record.discount_cash,
                        'other_discount': record.discount_other,
                        'tax_id': False,
                    })
                    record.order_line = order_line.id
                    record.stage_line_product = 'processing'
                    record.date_create_so = datetime.datetime.now()

            return {
                'name': 'BÁO GIÁ',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': order.id,
                'view_id': self.env.ref('sale.view_order_form').id,
                'res_model': 'sale.order',
                'context': {},
            }
