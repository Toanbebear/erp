##############################################################################
#    Copyright (C) 2016 sHealth (<http://scigroup.com.vn/>). All Rights Reserved
#    sHealth, Hospital Management Solutions
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError

class sHealthProduct(models.Model):
    _inherit = 'product.template'

    is_medicine = fields.Boolean(string='Medicine', help='Check if the product is a medicine')
    is_bed = fields.Boolean(string='Bed', help='Check if the product is a bed')
    is_vaccine = fields.Boolean(string='Vaccine', help='Check if the product is a vaccine')
    is_medical_supply = fields.Boolean(string='Medical Supply', help='Check if the product is a medical supply')
    is_insurance_plan = fields.Boolean(string='Insurance Plan', help='Check if the product is an insurance plan')

    # def _get_default_uom_id(self):
    #     return self.env["uom.uom"].search([], limit=1, order='id').id

    # thêm trường quản lý đơn vị bán hàng
    uom_so_id = fields.Many2one(
        'uom.uom', 'Đơn vị tính bán hàng',
        help="Đơn vị mua hàng mặc định được sử dụng cho các đơn bán hàng phải cùng loại với đơn vị mặc định.")

    _sql_constraints = [
        ('unique_product_default_code', 'unique (default_code)', 'Mã nội bộ phải là duy nhất!')
    ]

    @api.constrains('uom_id', 'uom_so_id')
    def _check_uom_his(self):
        if any(template.uom_id and template.uom_so_id and template.uom_id.category_id != template.uom_so_id.category_id
               for template in self):
            raise ValidationError(
                _('Đơn vị đo lường mặc định và đơn vị đo lường bán hàng phải cùng thể loại.'))
        return True

    @api.onchange('uom_id')
    def _onchange_uom_id_his(self):
        if self.uom_id:
            self.uom_so_id = self.uom_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class sHealthProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_quantities(self):
        """Thêm context ở hàm tính số lượng khả dụng sản phẩm: nếu gặp ignore_expired thì trừ số lượng các lô quá đát"""
        res = super(sHealthProductProduct, self)._compute_quantities()
        if self.env.context.get('ignore_expired'):
            tracked_products = self.filtered(lambda p: p.tracking != 'none')
            if tracked_products:
                domain = [('product_id', '=', tracked_products.ids), ('location_id.usage', '=', 'internal'), ('lot_id.removal_date', '<', self.env.context.get('ignore_expired'))]
                quant_groups = self.env['stock.quant'].read_group(domain, ['product_id', 'quantity'], ['product_id'])
                expired_quants = dict((item['product_id'][0], item['quantity']) for item in quant_groups)
                for product in tracked_products:
                    product.qty_available -= expired_quants.get(product.id, 0)
        return res