from odoo import fields, models, api


class TasCostDriver(models.Model):
    _name = "tas.cost.driver"
    _description = " Cost driver "
    _inherit = 'mail.thread'

    name = fields.Char('Name', required=True)
    code = fields.Char('code', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    computation = fields.Selection([('manual', 'Manual Input'),
                                    ('equal_plan', 'Equal Plan'),
                                    ('last_computed', 'Last computed'),
                                    # ('base_on_some_last_mo', 'Base on 10 last MO')
                                    ], string='Computation method', default='equal_plan')
    work_center_id = fields.Char(string='Mã tính giá thành')
    compute_actual_count_base_on_working_hour = fields.Boolean('Compute actual count base on working hour of work center', default=False)
    plan_cost_per_unit = fields.Float("Plan Cost Per Uom Unit", tracking=True)
    sci_company_id = fields.Many2one('res.company', string='Company')

    @api.depends('name', 'work_center_id')
    def name_get(self):
        result = []
        for cd in self:
            if cd.work_center_id and cd.sci_company_id:
                result.append((cd.id, cd.name + "(" + cd.work_center_id + "-" + cd.sci_company_id.name + ")"))
            else:
                result.append((cd.id, cd.name))
        return result


class TasMrpBomCostDriver(models.Model):
    _name = "tas.mrp.bom.cost.driver"
    _description = "Mrp BOM Cost driver"

    mrp_bom_id = fields.Many2one('sh.medical.product.bundle', string="Bom")
    mrp_lab_bom_id = fields.Many2one('sh.medical.lab.bom', string="Lab Bom")
    cost_driver_id = fields.Many2one('tas.cost.driver', string="Cost driver", required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='cost_driver_id.uom_id')
    planned_count = fields.Float("Planned Count")
    planned_cost_per_unit = fields.Float("Planned Cost Per Uom Unit", compute="_compute_planned_cost_per_unit", store=True)
    actual_count = fields.Float("Actual Count")
    actual_cost_per_unit = fields.Float("Actual Cost Per Uom Unit")
    complete_percentage = fields.Float("Tỷ lệ hoàn thành")
    sci_company_id = fields.Many2one('res.company', related='cost_driver_id.sci_company_id', string='Company')

    @api.depends('mrp_bom_id', 'cost_driver_id')
    def name_get(self):
        result = []
        for cd in self:
            if cd.mrp_bom_id and cd.cost_driver_id and cd.mrp_bom_id.name and cd.cost_driver_id.name:
                result.append((cd.id, cd.mrp_bom_id.name + " (" + cd.cost_driver_id.name + ")"))
            else:
                result.append((cd.id, cd.id))
        return result

    @api.depends('cost_driver_id.plan_cost_per_unit')
    def _compute_planned_cost_per_unit(self):
        for record in self:
            planned_cost_per_unit = 0
            if record.cost_driver_id:
                planned_cost_per_unit = record.cost_driver_id.plan_cost_per_unit
            record.planned_cost_per_unit = planned_cost_per_unit


class TasActualCostDriver(models.Model):
    _name = "tas.actual.cost.driver"
    _description = "Actual Cost driver"

    bom_cost_driver_id = fields.Many2one('tas.mrp.bom.cost.driver', string="Bom Cost driver", required=True)
    actual_count = fields.Float("Actual Count")
    actual_cost_per_unit = fields.Float("Actual Cost Per Uom Unit")


class TasPlanCostDriver(models.Model):
    _name = "tas.plan.cost.driver"
    _description = "Plan Cost driver"

    name = fields.Char("Name", required=True)
    lines_ids = fields.One2many('tas.plan.cost.driver.line', 'plan_cost_driver_id', string='Lines')

    def action_update_plan_price(self):
        for record in self:
            record.lines_ids._update_plan_price()


class TasPlanCostDriverLine(models.Model):
    _name = "tas.plan.cost.driver.line"
    _description = "Plan Cost driver line"

    plan_cost_driver_id = fields.Many2one('tas.plan.cost.driver', string="Bom Cost driver")
    cost_driver_id = fields.Many2one('tas.cost.driver', string="Cost driver", domain="[('code', '!=', 'nvl')]", required=True)
    plan_cost_per_unit = fields.Float("Plan Cost Per Uom Unit")
    sci_company_id = fields.Many2one('res.company', related='cost_driver_id.sci_company_id', string='Company')

    @api.model
    def _update_plan_price(self):
        for plan_cost_driver in self:
            if plan_cost_driver:
                plan_cost_driver.cost_driver_id.update({
                    'plan_cost_per_unit': plan_cost_driver.plan_cost_per_unit
                })
