from odoo import fields, api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    stage_sol = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done'), ('cancel', 'Cancel')],
                                 string='Stage')
    odontology = fields.Boolean('Odontology', related='crm_line_id.odontology', store=True)
    teeth_ids = fields.Many2many('sh.medical.teeth', string='Mã răng')
    sh_room_id = fields.Many2one('sh.medical.health.center.ot', related='order_id.sh_room_id', string='Phòng xuất',
                                 store=True)

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.order_id.document_related and res.product_id.type == 'service' and res.order_id and res.order_id.booking_id:
            crm_information_ids = []
            if res.order_id.booking_id.brand_id.id == 3:
                crm_information_id = self.env['crm.information.consultant'].sudo().create(
                    {'role': 'recept', 'user_id': self.env.user.id})
                crm_information_ids.append(crm_information_id.id)
            crm_line = self.env['crm.line'].create({
                'product_id': res.product_id.id,
                'quantity': res.product_uom_qty,
                'unit_price': res.price_unit,
                'crm_id': res.order_id.booking_id.id,
                'company_id': res.order_id.company_id.id,
                'source_extend_id': res.order_id.booking_id.source_id.id,
                'price_list_id': res.order_id.pricelist_id.id,
                'sale_order_line_id': [(4, res.id)],
                'status_cus_come': 'come',
                'stage': 'new',
                'consultants_1': self.env.user.id if res.order_id.booking_id.brand_id.id != 3 else '',
                'crm_information_ids': [(6, 0, crm_information_ids)],
                'is_pk': True,
                'is_new': True
            })
        return res

    @api.depends('product_uom_qty', 'discount', 'discount_cash', 'price_unit', 'tax_id', 'uom_price', 'other_discount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.sale_to == 0:
                price = line.price_unit * (
                        1 - (line.discount or 0.0) / 100.0) - line.discount_cash - line.other_discount
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)
                total = line.price_unit * line.product_uom_qty * line.uom_price * (
                        1 - (line.discount or 0.0) / 100.0) - line.discount_cash - line.other_discount
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': total,
                    'price_subtotal': total,
                })
            else:
                total = line.sale_to * line.product_uom_qty - line.other_discount
                line.update({
                    'price_total': total,
                    'price_subtotal': total,
                })


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    odontology = fields.Boolean('Odontology', compute='set_odontology')

    @api.depends('order_line')
    def set_odontology(self):
        for rec in self:
            rec.odontology = False
            if rec.order_line and rec.order_line[0].odontology is True:
                rec.odontology = True
