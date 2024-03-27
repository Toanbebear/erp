from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InheritSelectService(models.TransientModel):
    _inherit = "crm.select.service"

    height = fields.Float('Chiều cao (cm)')
    weight = fields.Float('Cân nặng (kg)')
    brand_kn = fields.Boolean('Bệnh viện thương hiệu Kangnam', compute='get_brand_kn')

    @api.constrains('height', 'weight')
    def _constraint_height_weight(self):
        # if self.brand_kn == True:
        #     if self.height <= 0 or self.weight <= 0:
        #         raise ValidationError(
        #             'Chiều cao và cân nặng phải phải lớn hơn 0')
        for rec in self:
            if rec.brand_kn == True:
                if rec.height <= 10 or rec.height >= 500:
                    raise ValidationError('Bạn đã nhập sai chiều cao, chiều cao phải lớn hơn 10cm và nhỏ hơn 500cm')
                if rec.weight <= 10 or rec.weight >= 300:
                    raise ValidationError('Bạn đã nhập sai cân nặng, cân nặng phải lớn hơn 10kg và nhỏ hơn 300kg')

    @api.depends('booking_id')
    def get_brand_kn(self):
        if self.booking_id:
            if self.booking_id.company_id.id in (2, 4, 12):
                self.brand_kn = True
            else:
                self.brand_kn = False

    def create_quotation(self):
        res = super(InheritSelectService, self).create_quotation()
        if self.partner_id:
            partner = self.partner_id
            if self.height:
                partner.height = self.height
            if self.weight:
                partner.weight = self.weight
        return res

    @api.onchange('partner_id')
    def get_height_weight(self):
        if self.partner_id:
            self.height = self.partner_id.height

