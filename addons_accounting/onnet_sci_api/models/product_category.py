
from odoo import models, api, fields, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_category_account_analytic_id = fields.Many2one('account.analytic.account', company_dependent=True,
        string="Analytic Account",
        domain="[('company_id', '=', current_company_id)]")

