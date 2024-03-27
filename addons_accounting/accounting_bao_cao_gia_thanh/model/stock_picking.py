
from collections import Counter
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError,AccessError
from lxml import etree
import json
from odoo.tools.float_utils import float_round, float_compare
from odoo.osv import expression
from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.page import (
    PrintPageSetup,
    PageMargins,
    PrintOptions,
)
from openpyxl.styles import Font, borders, Alignment, PatternFill
from openpyxl.worksheet.pagebreak import Break
import base64
from io import BytesIO
import pytz
from num2words import num2words

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    material_line_object = fields.Char('Martial Object')
    material_line_object_id = fields.Char('Martial Object ID')

    def _get_done_price_unit(self):
        for move in self:
            done_price_unit = 0
            if move.state == 'done':
                done_price_unit = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
                if move.product_id.cost_method == 'standard':
                    done_price_unit = move.product_id.standard_price
                # done_price_unit = move.stock_valuation_layer_ids[0].unit_cost if move.stock_valuation_layer_ids else 0.0
                # if move.product_id.cost_method == 'standard':
                #     done_price_unit = move.product_id.standard_price
            return done_price_unit
        return 0.0

    def get_done_unit_price_by_material_line(self, material_line_object, material_line_object_id):
        move = self.search([('state', '=', 'done'),
                     ('material_line_object', '=', material_line_object),
                     ('material_line_object_id', '=', material_line_object_id)], limit=1, order='id desc')
        return move._get_done_price_unit()