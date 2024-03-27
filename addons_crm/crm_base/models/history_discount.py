from odoo import fields, api, models, _


class HistoryDiscount(models.Model):
    _name = 'history.discount'
    _description = 'History discount'

    name = fields.Char('Name')
    type = fields.Selection([('percent', 'Discount percent'), ('cash', 'Discount cash')], string='Type discount')
    discount_cash = fields.Float('Discount cash')
    discount_percent = fields.Float('Discount percent')
    crm_id = fields.Many2one('crm.lead', string='Booking')
    order_id = fields.Many2one('sale.order', string='Order')
    crm_line_id = fields.Many2one('crm.line', string='Crm line')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale order line')
    amount_discount = fields.Float('Amount discount', compute='set_amount_discount')
    discount_review_id = fields.Many2one('crm.discount.review', string='Discount review')

    @api.depends('type', 'crm_line_id', 'discount_cash')
    def set_amount_discount(self):
        for rec in self:
            rec.amount_discount = 0
            if rec.type == 'cash':
                rec.amount_discount = rec.discount_cash
            elif rec.type == 'percent':
                if rec.crm_line_id and rec.crm_line_id.stage != 'cancel':
                    rec.amount_discount = rec.crm_line_id.total_before_discount - rec.crm_line_id.total

    def write(self, vals):
        res = super(HistoryDiscount, self).write(vals)
        for rec in self:
            if vals.get('crm_id') is False:
                rec.unlink()
        return res


class CrmLineDiscountHistory(models.Model):
    _name = 'crm.line.discount.history'
    _description = 'Crm line Discount History'
    _rec_name = 'crm_line'

    booking_id = fields.Many2one('crm.lead', 'Booking')
    crm_line = fields.Many2one('crm.line', 'Line Booking')
    discount_program = fields.Many2one('crm.discount.program', 'Discount Program')
    index = fields.Integer('Index')
    type = fields.Selection([('gift', 'Gift'), ('discount', 'Discount')], string='Type')
    type_discount = fields.Selection([('percent', 'Percent'), ('cash', 'Cash'), ('sale_to', 'Sale to')],
                                     string='Type Discount')
    discount = fields.Float('Discount')
