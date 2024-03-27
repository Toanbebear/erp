from odoo import fields, models, api


class ProductCostMrpBom(models.AbstractModel):
    _name = 'product.cost.mrp.bom'
    _description = 'mrp bom'


class ShMedicalProductBundle(models.Model):
    _name = 'sh.medical.product.bundle'
    _inherit = ['sh.medical.product.bundle', 'product.cost.mrp.bom']

    cost_driver_ids = fields.One2many("tas.mrp.bom.cost.driver", "mrp_bom_id", string="Cost driver")

    @api.onchange('duplicate')
    def onchange_duplicate(self):
        super(ShMedicalProductBundle, self).onchange_duplicate()
        if self.duplicate:
            vals = []
            for record in self.env['tas.mrp.bom.cost.driver'].search([('mrp_bom_id', '=', self.duplicate.id)]):
                vals.append((0, 0, {'cost_driver_id': record.cost_driver_id.id,
                                    'uom_id': record.uom_id.id,
                                    'planned_count': record.planned_count,
                                    'planned_cost_per_unit': record.planned_cost_per_unit,
                                    'actual_count': record.actual_count,
                                    'actual_cost_per_unit': record.actual_cost_per_unit,
                                    'complete_percentage': record.complete_percentage,
                                    'sci_company_id': record.sci_company_id.id,
                                    }))
            self.update({'cost_driver_ids': vals})
        if not self.duplicate and len(self.cost_driver_ids) > 0:
            for record in self.cost_driver_ids:
                record.unlink()


class ShMedicalLabBom(models.Model):
    _name = 'sh.medical.lab.bom'
    _inherit = ['sh.medical.lab.bom', 'product.cost.mrp.bom']

    cost_driver_ids = fields.One2many("tas.mrp.bom.cost.driver", "mrp_lab_bom_id", string="Cost driver")
