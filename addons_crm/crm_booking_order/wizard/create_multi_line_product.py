from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CreateMultiLineProductLine(models.Model):
    _name = "create.multi.line.product.detail"
    _description = 'Multi line product detail'

    create_multi_parent = fields.Many2one('create.multi.line.product')
    pricelist = fields.Many2one('product.pricelist', string='Bảng giá')
    product = fields.Many2one('product.product', string='Sản phẩm')
    uom_so_id = fields.Many2one('uom.uom', string='Đơn vị tính', related='product.uom_so_id')
    product_uom_qty = fields.Float('Số lượng')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    unit_price = fields.Monetary('Đơn giá')

    @api.onchange('pricelist')
    def get_product(self):
        products = self.env['product.pricelist.item'].search([('pricelist_id', '=', self.pricelist.id)]).mapped(
            'product_id')
        return {'domain': {'product': [('id', 'in', products.ids)]}}

    @api.onchange('pricelist', 'product')
    def get_unit_price(self):
        self.unit_price = 0
        if self.product and self.pricelist:
            pricelist_item = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', self.pricelist.id), ('product_id', '=', self.product.id)], limit=1)
            if pricelist_item and self.product.uom_id == self.product.uom_so_id:
                unit_price = pricelist_item.fixed_price
            else:
                unit_price = self.product.uom_id._compute_price(pricelist_item.fixed_price, self.product.uom_so_id)
            self.unit_price = unit_price


class CreateMultiLineProduct(models.Model):
    _name = "create.multi.line.product"
    _description = "Hỗ trợ tạo nhiều dòng bán sản phẩn trên Booking"

    booking = fields.Many2one('crm.lead', string='Booking')
    brand = fields.Many2one('res.brand', string='Thương hiệu', default=lambda self: self.env.company.brand_id.id)
    pricelist = fields.Many2one('product.pricelist', string='Bảng giá',
                                domain="[('brand_id','=',brand), ('type','=','product')]")
    CONSULTING_ROLE = [('1', 'Tư vấn độc lập'), ('2', 'Tư vấn đồng thời'), ('3', 'Lễ tân - CVTV cùng tư vấn'),
                       ('4', 'BS da liễu - KTV cùng tư vấn'), ('5', 'Tư vấn chính'), ('6', 'Tư vấn phụ')]
    consultants_1 = fields.Many2one('res.users', string='Tư vấn viên 1')
    consulting_role_1 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 1')
    consultants_2 = fields.Many2one('res.users', string='Tư vấn viên 2')
    consulting_role_2 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 2')
    consultants_3 = fields.Many2one('res.users', string='Tư vấn viên 3', tracking=True)
    consulting_role_3 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 3', tracking=True)
    detail = fields.One2many('create.multi.line.product.detail', 'create_multi_parent', string='Chi tiết')

    crm_consultant_ids = fields.One2many('crm.information.consultant', 'create_multi_line_product_id',
                                         string='Thông tin tư vấn')

    def create_line_product(self):
        if self.brand.id == 3 and not self.crm_consultant_ids:
            raise ValidationError('Chưa nhập thông tin tư vấn')
        crm_information_ids = []
        for rec in self.crm_consultant_ids:
            crm_information_ids.append((0, 0, {
                'role': rec.role,
                'user_id': rec.user_id.id,
                'crm_line_id': False,
            }))
        if self.detail and self.pricelist:
            for line in self.detail:
                pricelist_item = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', self.pricelist.id), ('product_id', '=', line.product.id)], limit=1)
                if pricelist_item:
                    if line.product.uom_id == line.product.uom_so_id:
                        price_unit = pricelist_item.fixed_price
                    else:
                        price_unit = line.product.uom_id._compute_price(pricelist_item.fixed_price,
                                                                        line.product.uom_so_id)
                self.env['crm.line.product'].create({
                    'booking_id': self.booking.id,
                    'product_id': line.product.id,
                    'price_unit': price_unit,
                    'product_uom_qty': line.product_uom_qty,
                    'company_id': self.env.company.id,
                    'product_pricelist_id': self.pricelist.id,
                    'source_extend_id': self.booking.source_id.id,
                    'consultants_1': self.consultants_1.id,
                    'consulting_role_1': self.consulting_role_1,
                    'consultants_2': self.consultants_2.id,
                    'consulting_role_2': self.consulting_role_2,
                    'consultants_3': self.consultants_3.id,
                    'consulting_role_3': self.consulting_role_3,
                    'stage_line_product': 'new',
                    'crm_information_ids': crm_information_ids,
                })

class CrmInformationConsultant(models.Model):
    _inherit = "crm.information.consultant"

    create_multi_line_product_id = fields.Many2one('create.multi.line.product', string='Bán nhiều sản phẩm')
    crm_line_product_id = fields.Many2one('crm.line.product', string='Bán sản phẩm')
