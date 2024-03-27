from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def cron_job_cancel_stock(self):
        query_cancel = """
        UPDATE stock_picking
        set state = 'cancel'
        where state not in ('cancel', 'done') and create_uid = 2
        """
        self.env.cr.execute(query_cancel)
