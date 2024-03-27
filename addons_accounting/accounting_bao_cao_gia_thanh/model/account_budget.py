# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    reports = fields.Many2many('tas.product.cost.report', 'tas_product_cost_report_budget_rel', 'budget_id', 'report_id')


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    cost_driver_id = fields.Many2one('tas.cost.driver', string="Cost driver")
    sci_company_id = fields.Many2one('res.company', related='cost_driver_id.sci_company_id', string='Company')

