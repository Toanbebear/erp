from odoo import fields, models


class CrmLineDiscountHistory(models.Model):
    _name = 'crm.line.discount.history'
    _description = 'Crm line Discount History'

    booking_id = fields.Many2one('crm.lead', 'Booking')
    crm_line = fields.Many2one('crm.line', 'Line Booking Service')
    discount_program = fields.Many2one('crm.discount.program', 'Discount Program')
    index = fields.Integer('Index')
    type = fields.Selection([('gift', 'Gift'), ('discount', 'Discount')], string='Type')
    type_discount = fields.Selection([('percent', 'Percent'), ('cash', 'Cash'), ('sale_to', 'Sale to')],
                                     string='Type Discount')
    discount = fields.Float('Discount')
