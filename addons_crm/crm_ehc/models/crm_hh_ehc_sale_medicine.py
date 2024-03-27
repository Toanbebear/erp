import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleMedicineEhc(models.Model):
    _name = "crm.hh.ehc.sale.medicine"
    _description = "Danh sách bán thuốc"

    booking_id = fields.Many2one('crm.lead', string='Booking')
    patient_id = fields.Many2one('crm.hh.ehc.patient', string='Bệnh nhân')
    create_date_ehc = fields.Date('Ngày tạo phiếu')
    approval_date = fields.Date('Ngày duyệt phiếu')
    out_date = fields.Date('Ngày xuất thuốc')
    hh_line_ids = fields.One2many('crm.hh.ehc.sale.medicine.line', 'ehc_sale_medicine_id', string='Thuốc')


class SaleMedicineEhcLine(models.Model):
    _name = "crm.hh.ehc.sale.medicine.line"
    _description = "Danh sách thuốc không tìm thấy trong sản phẩm"

    ehc_sale_medicine_id = fields.Many2one('crm.hh.ehc.sale.medicine', string='EHC ID')
    medicine_code = fields.Char('Mã thuốc')
    medicine_name = fields.Char('Tên thuốc')
    unit = fields.Char('Đơn vị')
    quantity = fields.Float('Số lượng')
    currency_id = fields.Many2one('res.currency')
    unit_price = fields.Monetary('Đơn giá')