from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class PriceListItem(models.Model):
    _inherit = 'product.pricelist.item'

    # False là có tính, True là không tính
    target_sale_marketing = fields.Boolean(string='Không tính doanh số cho S&M', default=False)