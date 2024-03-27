from odoo import models, fields


class StockLocationShare(models.Model):
    _inherit = "stock.location"

    is_location_supply_share = fields.Boolean('Địa điểm nhận VT thuê phòng',
                                              help='Đối với case thuê phòng mổ, khi tạo phiếu PO, picking, vật tư thuê phòng sẽ được chỉ định điều chuyển đến tủ này')
