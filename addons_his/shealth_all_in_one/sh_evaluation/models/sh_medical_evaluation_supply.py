from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, Warning


# vat tu tieu hao cho moi lan tham kham ...
class SHealthEvaluationSupply(models.Model):
    _name = "sh.medical.evaluation.supply"
    _description = "Supplies related to the evaluation"

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        ('CCDC', 'CCDC')
    ]

    name = fields.Many2one('sh.medical.evaluation', string='Evaluation')
    qty = fields.Float(string='Initial Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                       help="Initial Quantity", default=0)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    supply = fields.Many2one('sh.medical.medicines', string='Supply', required=True,
                             help="Supply to be used in this evaluation",
                             domain=lambda self: [('categ_id', 'child_of', self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    notes = fields.Char(string='Notes')

    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ trực",
                              compute='compute_available_qty_supply_in_location')
    is_warning_location = fields.Boolean('Cảnh báo tại tủ', compute='compute_available_qty_supply_in_location')
    qty_used = fields.Float(string='Actual quantity used', required=True, help="Actual quantity used",
                            default=lambda *a: 1, digits=dp.get_precision('Product Unit of Measure'))
    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="supply.medicament_type", string='Medicament Type',
                                       store=True)

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự

    services = fields.Many2many('sh.medical.health.center.service', 'sh_evaluation_supply_service_rel',
                                track_visibility='onchange',
                                string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_evaluation_supply_service_related_rel',
                                       related="name.services",
                                       string='Dịch vụ liên quan')

    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')

    is_diff_bom = fields.Boolean('Khác định mức?', compute='compute_qty_used_bom')

    @api.depends('qty', 'qty_used')
    def compute_qty_used_bom(self):
        for record in self:
            if record.qty_used > record.qty:
                record.is_diff_bom = True
            else:
                record.is_diff_bom = False

    @api.depends('supply', 'uom_id')
    def compute_available_qty_supply(self):  # so luong kha dung toan vien
        for record in self:
            if record.supply:
                record.qty_avail = record.uom_id._compute_quantity(record.supply.qty_available,
                                                                   record.supply.uom_id) if record.uom_id != record.supply.uom_id else record.supply.qty_available
            else:
                record.qty_avail = 0

    @api.depends('supply', 'location_id', 'qty_used', 'uom_id')
    def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
        for record in self:
            if record.supply:
                quantity_on_hand = self.env['stock.quant'].with_user(1)._get_available_quantity(
                    record.supply.product_id,
                    record.location_id)  # check quantity trong location

                record.qty_in_loc = record.uom_id._compute_quantity(quantity_on_hand,
                                                                    record.supply.uom_id) if record.uom_id != record.supply.uom_id else quantity_on_hand
            else:
                record.qty_in_loc = 0

            record.is_warning_location = True if record.qty_used > record.qty_in_loc else False

    @api.onchange('qty_used', 'supply')
    def onchange_qty_used(self):
        if self.qty_used < 0 and self.supply:
            raise UserError("Số lượng nhập phải lớn hơn 0!")

    @api.onchange('supply')
    def _change_product_id(self):
        self.uom_id = self.supply.uom_id
        self.services = self.name.services
        domain = {'domain': {'uom_id': [('category_id', '=', self.supply.uom_id.category_id.id)]}}
        if self.medicament_type == 'Medicine':
            self.location_id = self.name.room.location_medicine_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'),
                                               ('company_id', '=', self.name.institution.his_company.id)]
        elif self.medicament_type == 'Supplies':
            self.location_id = self.name.room.location_supply_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'),
                                               ('company_id', '=', self.name.institution.his_company.id)]
        return domain

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.supply.uom_id.category_id:
            self.uom_id = self.supply.uom_id
            raise Warning(_('The Supply Unit of Measure and the Material Unit of Measure must be in the same category.'))
