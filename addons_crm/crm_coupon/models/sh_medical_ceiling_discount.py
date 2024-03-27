from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class SHealthCeilingDiscount(models.Model):
    _name = 'sh.medical.ceiling.discount'
    _description = 'Ceiling discount configuration for service per company'

    service_id = fields.Many2one('sh.medical.health.center.service')
    domain_brand_ids = fields.Many2many('res.brand', compute='domain_for_brand')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', required=True)
    ceiling_discount = fields.Float(string='Mức trần khuyến mại(%)')
    begin_date = fields.Date(string='Bắt đầu', default='2000-01-01')
    end_date = fields.Date(string='Kết thúc', default='3500-01-01')

    @api.depends('service_id', 'brand_id')
    def domain_for_brand(self):
        for rec in self:
            if self.service_id:
                brand_ids = self.service_id.ceiling_discount_ids.mapped('brand_id')
                rec.domain_brand_ids = brand_ids
            else:
                rec.domain_brand_ids = None


class SHealthCenterServiceInherit(models.Model):
    _inherit = 'sh.medical.health.center.service'

    ceiling_discount_ids = fields.One2many('sh.medical.ceiling.discount', 'service_id', string='')
    not_sale = fields.Boolean(string='Không tính doanh số', default=False)
