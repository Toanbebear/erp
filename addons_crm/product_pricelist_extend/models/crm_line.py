from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class CrmLine(models.Model):
    _inherit = 'crm.line'

    price_min = fields.Monetary('Giá Min')
    discount_cs_percent = fields.Float('Giảm giá MKT %')
    discount_cs_amount = fields.Monetary('Giảm giá MKT')
    percent_total_discount = fields.Float('% giảm giá tổng', compute='set_percent_total_discount')
    is_price_min_max = fields.Boolean('Bảng giá trong khoảng', related='price_list_id.is_price_min_max')
    total_discount_review = fields.Monetary('Giảm giá sâu')
    discount_mkt = fields.Monetary('Giảm giá MKT', compute='get_total_line')
    discount_mkt_percent = fields.Float('Giảm giá MKT', compute='get_total_line')

    @api.onchange('discount_cs_percent')
    def set_discount_cs_amount(self):
        for rec in self:
            if rec.discount_cs_percent:
                if 0 <= rec.discount_cs_percent <= 100:
                    rec.discount_cs_amount = rec.total_before_discount * rec.discount_cs_percent / 100
                else:
                    raise ValidationError(_('Giảm giá % không thể lớn hơn 100 % hoặc nhỏ hơn 0 %.'))
            else:
                rec.discount_cs_amount = 0

    @api.onchange('discount_cs_amount')
    def set_discount_cs_percent(self):
        for rec in self:
            if rec.discount_cs_amount:
                if rec.discount_cs_amount <= rec.total_before_discount:
                    rec.discount_cs_percent = round(rec.discount_cs_amount / rec.total_before_discount * 100)
                else:
                    raise ValidationError(_('Giảm giá tiền mặt không thể lớn hơn tổng tiền trước giảm.'))
            else:
                rec.discount_cs_percent = 0

    @api.depends('total_discount')
    def set_percent_total_discount(self):
        for rec in self:
            rec.percent_total_discount = 0
            if rec.total_discount and rec.unit_price:
                rec.percent_total_discount = rec.total_discount / rec.total_before_discount * 100

    @api.onchange('product_id')
    def set_price_min(self):
        for rec in self:
            if rec.product_id:
                item_price = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', rec.price_list_id.id), ('product_id', '=', rec.product_id.id),
                     ('is_price_min_max', '=', True)])
                if item_price:
                    rec.price_min = item_price.price_min
            else:
                rec.unit_price = 0
                rec.price_min = 0
                rec.quantity = 1
                rec.discount_cash = 0
                rec.discount_percent = 0
                rec.discount_cs_percent = 0
                rec.discount_cs_amount = 0

    @api.depends('quantity', 'unit_price', 'discount_percent', 'discount_cash', 'uom_price', 'sale_to',
                 'other_discount', 'discount_cs_percent', 'discount_cs_amount', 'total_discount_review')
    def get_total_line(self):
        for rec in self:
            rec.total_before_discount = rec.unit_price * rec.quantity * rec.uom_price
            if not rec.sale_to:
                rec.total = rec.total_before_discount - rec.total_before_discount * rec.discount_percent / 100 - rec.discount_cash - rec.other_discount - rec.discount_cs_amount - rec.total_discount_review
                rec.total_discount = rec.total_before_discount - rec.total
                rec.discount_mkt = rec.total_before_discount * rec.discount_percent / 100 + rec.discount_cash + rec.other_discount
                rec.discount_mkt_percent = rec.discount_mkt / rec.total_before_discount * 100 if rec.total_before_discount != 0 else 0
                if rec.price_min * rec.quantity * rec.uom_price > rec.total + rec.total_discount_review:
                    raise ValidationError('Tổng tiền phải thu không được nhỏ hơn giá tối thiểu')
            else:
                rec.total = rec.sale_to - rec.other_discount - rec.total_discount_review
                rec.discount_mkt = rec.total_before_discount - rec.sale_to + rec.other_discount
                rec.discount_mkt_percent = rec.discount_mkt / rec.total_before_discount * 100 if rec.total_before_discount != 0 else 0
                if rec.price_min * rec.quantity * rec.uom_price > rec.total + rec.total_discount_review:
                    raise ValidationError('Tổng tiền phải thu không được nhỏ hơn giá tối thiểu')

    @api.model
    def create(self, vals):
        if 'price_min' in vals and 'total' in vals and 'service_id' in vals and 'quantity' in vals and 'uom_price':
            service = self.env['sh.medical.health.center.service'].sudo().browse(int(vals['service_id']))
            total = vals['total'] + vals['total_discount_review'] if 'total_discount_review' in vals else vals['total']
            if total < vals['price_min'] * vals['quantity'] * vals['uom_price']:
                if service:
                    raise ValidationError(
                        _('Tổng tiền phải thu của dịch vụ %s phải cao hơn giá tối thiểu!' % (service.name)))
                else:
                    raise ValidationError(_('Tổng tiền phải thu phải cao hơn giá tối thiểu!'))
        return super(CrmLine, self).create(vals)

    def write(self, vals):
        for rec in self:
            if 'discount_percent' in vals or 'discount_cash' in vals or 'sale_to' in vals or 'other_discount' in vals:
                if rec.discount_cs_percent or rec.discount_cs_amount:
                    if rec.discount_percent == 0 and rec.discount_cash == 0 and rec.sale_to == 0 and rec.other_discount == 0:
                        raise ValidationError(
                            _('Bạn không thể áp dụng voucher hoặc coupon vì đã nhập giảm giá tại cơ sở!'))
        return super(CrmLine, self).write(vals)

    @api.constrains('price_min', 'total')
    def check_total_min(self):
        for record in self:
            if record.price_min * record.quantity * record.uom_price > record.total + record.total_discount_review:
                raise ValidationError(
                    _("Tổng tiền phải thu của dịch vụ %s phải cao hơn giá tối thiểu!" % (record.service_id.name)))


class CrmLineProduct(models.Model):
    _inherit = 'crm.line.product'

    total_discount_review = fields.Monetary('Giảm giá sâu')

    @api.depends('price_unit', 'product_uom_qty', 'discount_percent', 'discount_cash', 'discount_other',
                 'total_discount_review')
    def _calculate_total_line(self):
        for rec in self:
            rec.total = 0
            rec.total = rec.total_before_discount * (
                    1 - (
                        rec.discount_percent or 0.0) / 100.0) - rec.discount_cash - rec.discount_other - rec.total_discount_review
