from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UpdateCodeCard(models.TransientModel):
    _name = 'update.code.card'
    _description = 'Update code card'

    name = fields.Char('Mã thẻ')
    loyalty_id = fields.Many2one('crm.loyalty.card', string='Thẻ thành viên')

    def update_code_card(self):
        loyalty = self.env['crm.loyalty.card'].sudo().search([('name', '=', self.name), ('brand_id', '=', self.loyalty_id.brand_id.id)])
        if loyalty:
            raise ValidationError('Mã thẻ này đã tồn tại!!!')
        else:
            self.loyalty_id.name = self.name

