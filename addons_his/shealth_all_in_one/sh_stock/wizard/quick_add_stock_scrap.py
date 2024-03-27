from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time
from calendar import monthrange
from openpyxl import load_workbook
from openpyxl.styles import Font, borders, Alignment
import base64
from io import BytesIO
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

import logging

thin = borders.Side(style='thin')
double = borders.Side(style='double')
all_border_thin = borders.Border(thin, thin, thin, thin)


class SQuickAddStockScrap(models.TransientModel):
    _name = 'quick.add.stock.scrap'
    _description = 'Thêm nhanh Xuất sử dụng phòng/Tiêu hủy'

    WARD_TYPE = [
        ('Examination', 'Examination'),
        ('Laboratory', 'Laboratory'),
        ('Imaging', 'Imaging'),
        ('Surgery', 'Surgery'),
        ('Inpatient', 'Inpatient'),
        ('Spa', 'Spa'),
        ('Laser', 'Laser'),
        ('Odontology', 'Odontology')
    ]

    def get_domain_room_use(self):
        return [('institution.his_company','=', self.env.company.id)]

    type = fields.Selection([('room_use', 'Sử dụng phòng'), ('scrap', 'Tiêu hủy')], string='Loại')
    date_done = fields.Datetime('Ngày xuất', default=lambda self: fields.Datetime.now())
    scrap_location = fields.Many2one('stock.location', string='Địa điểm phế liệu', help='Địa điểm phế liệu')
    room = fields.Many2one('sh.medical.health.center.ot', string='Phòng xuất', help='Phòng xuất', domain=lambda self: self.get_domain_room_use())
    room_type = fields.Selection(WARD_TYPE, string='Loại phòng', help='Loại phòng',related="room.room_type")
    note = fields.Text("Lý do", compute='compute_note')
    scrap_product_line = fields.Many2many('stock.scrap', 'stock_scrap_quick_add_rel', 'quick_add_id', 'scrap_id', string="Dòng chi tiết")

    # xóa sản phẩm đã nhập rồi
    @api.onchange('scrap_product_line')
    def _onchange_scrap_product_line(self):
        if self.scrap_product_line:
            id_products = {}
            inx = 0
            for product in self.scrap_product_line:
                if str(product.product_id.id) in id_products:
                    qty_pro = self.scrap_product_line[id_products[str(product.product_id.id)]].scrap_qty + product.scrap_qty
                    self.scrap_product_line[id_products[str(product.product_id.id)]].scrap_qty = qty_pro
                    self.scrap_product_line = [(2, product.id, False)]
                else:
                    # chưa có
                    id_products[str(product.product_id.id)] = inx
                inx += 1

    @api.depends('type', 'date_done')
    def compute_note(self):
        for record in self:
            record.note = ''
            if record.date_done:
                record.note = '%s: %s' % (dict(record._fields['type']._description_selection(record.env)).get(record.type), record.date_done.strftime("%d/%m/%Y"))

    # thay đổi loại
    @api.onchange('type')
    def _onchange_type(self):
        if self.type:
            self.scrap_product_line = False
            if self.type == 'room_use':
                self = self.with_context(view_for='picking_scrap_room_use',type_stock_scrap='room_use')
                scrap_loc = self.env['stock.location'].search(
                    [('name', 'ilike', 'Sử dụng phòng'), ('company_id', '=', self.env.company.id)], limit=1)
                self.scrap_location = scrap_loc.id
            else:
                self = self.with_context(view_for='picking_scrap',type_stock_scrap='scrap')
                scrap_loc = self.env['stock.location'].search(
                    [('scrap_location', '=', True), ('company_id', '=', self.env.company.id)], limit=1)
                self.scrap_location = scrap_loc.id
                medicine_room = self.env['sh.medical.health.center.ot'].sudo().search(
                    [('name', 'ilike', 'dược')], limit=1)
                self.room = medicine_room.id
                return {'domain': {'product_id': [('type', 'in', ['product', 'consu'])]}}

    # thay đổi phòng thì đổ lại bom SDP nếu có
    @api.onchange('room')
    def _onchange_room(self):
        if self.room:
            self.scrap_product_line = False
            # đổ bom nếu có
            institution = self.env['sh.medical.health.center'].sudo().search(
                [('his_company', '=', self.env.companies.ids[0])], limit=1)
            if self.room_type and institution:
                vals = []
                product_room_use = self.env['sh.product.room.use'].search([('department_type', '=', self.room_type),('brand', '=', institution.brand.id)])
                for record in product_room_use:
                    location_id = self.room.location_supply_stock
                    if record.product_id.categ_id.id == self.env.ref('shealth_all_in_one.sh_medicines').id:
                        location_id = self.room.location_medicine_stock

                    vals.append((0, 0, {'sci_date_done': self.date_done,
                                        'scrap_qty': 0,
                                        'product_id': record.product_id.id,
                                        'product_uom_id': record.product_id.uom_id,
                                        'note': self.note,
                                        'location_id': location_id.id,
                                        'room_use': self.room.id,
                                        'scrap_location_id': self.scrap_location.id}))

                self.scrap_product_line = vals
            self.scrap_product_line.room_use = self.room

    @api.onchange('date_done')
    def _onchange_date_done(self):
        if self.date_done:
            if self.scrap_product_line:
                self.scrap_product_line.note = self.note
                self.scrap_product_line.sci_date_done = self.date_done

    def quick_add(self):
        if self.type == 'room_use':
            return self.env['stock.picking'].view_stock_picking_by_group('picking_scrap_room_use')
        else:
            return self.env['stock.picking'].view_stock_picking_by_group('picking_scrap')
