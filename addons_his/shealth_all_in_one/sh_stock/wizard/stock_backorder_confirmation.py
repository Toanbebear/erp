# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Order Point Method:
#    - Order if the virtual stock of today is below the min of the defined order point
#

from odoo import api, models, tools

import logging
import threading

_logger = logging.getLogger(__name__)


class SCIStockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process_cancel_backorder(self):
        # Chưa check trường hợp dùng lô
        for picking in self.pick_ids:
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel'] and m.quantity_done == 0):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            if not picking._check_backorder():
                picking.with_context(cancel_backorder=False).action_done()
                return
        return super(SCIStockBackorderConfirmation, self).process_cancel_backorder()
