from odoo import models


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def cron_job_remove_product_inactive(self):
        orderpoint_ids = self.env['stock.warehouse.orderpoint'].sudo().search([('product_id.active', '=', False)]).unlink

