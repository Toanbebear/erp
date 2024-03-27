
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


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_default_production_location = fields.Boolean(string='Default production location')
    account_621 = fields.Many2one('account.account', string='Tài khoản giá thành (Trung gian)')

    @api.constrains('is_default_production_location', 'company_id')
    def _check_default_production_location_per_company(self):
        for line in self:
            if line.is_default_production_location:
                domain = [
                    ("is_default_production_location", "=", True),
                    ("company_id", "=", line.company_id.id),
                    ("id", "!=", line.id),
                ]
                duplicates = self.search(domain)
                if duplicates:
                    raise ValidationError(
                        _('Each company has only one default production location'))

    def get_default_production_location_per_company(self):
        location = self.env['stock.location'].search([
            ('is_default_production_location', '=', True),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        return location