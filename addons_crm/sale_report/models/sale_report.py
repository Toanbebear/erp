from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class SalesReport(models.Model):
    _name = "sales.report"
    _description = 'Sale report'

    ngay_bao_cao = fields.Date(string='Ngày báo cáo', default=date.today())
    company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.company)
    brand_id = fields.Many2one(related='company_id.brand_id', string='Thương hiệu')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    ds_chi_tieu = fields.Monetary('Doanh số chỉ tiêu')
    ti_le_hoan_thanh = fields.Char('Tỉ lệ hoàn thành', compute='_tinh_ti_le_hoan_thanh')
    ds_ngay = fields.Monetary('Doanh số ngày hiện tại')
    ds_tich_luy = fields.Monetary('Tổng doanh số tích lũy')
    ds_spa = fields.Monetary('Spa')
    ds_laser = fields.Monetary('Laser')
    ds_nha = fields.Monetary('Nha khoa')
    ds_pttm = fields.Monetary('PTTM')
    ds_khac = fields.Monetary('Khác')
    tm = fields.Monetary('Tiền mặt')
    ck = fields.Monetary('Chuyển khoản')
    qt = fields.Monetary('Quẹt thẻ')
    state = fields.Selection(
        [('draft', 'Nháp'), ('get_data', 'Lấy dữ liệu'), ('confirm', 'Xác nhận'), ('cancel', 'Hủy')],
        string="Trạng thái", default='draft')
    sale_report_details = fields.Many2many('crm.sale.payment', string='Chi tiết')
    month = fields.Integer('Tháng', compute='calculate_date', store=True)
    year = fields.Integer('Năm', compute='calculate_date', store=True)
    ds_dich_vu = fields.Monetary('Doanh số bán dịch vụ')
    ds_san_pham = fields.Monetary('Doanh số bán sản phẩm')

    # def unlink(self):
    #     for sp in self:
    #         if sp.state == 'confirm':
    #             raise ValidationError('Bạn không thể xóa khi đã xác nhận')
    #         return super(SalesReport, self).unlink()

    @api.depends('ds_chi_tieu', 'ds_tich_luy')
    def _tinh_ti_le_hoan_thanh(self):
        for record in self:
            record.ti_le_hoan_thanh = False
            if record.ds_chi_tieu and record.ds_tich_luy:
                ti_le = (record.ds_tich_luy / record.ds_chi_tieu) * 100
                record.ti_le_hoan_thanh = "{:,.2f}".format(ti_le) + " %"

    @api.depends('ngay_bao_cao')
    def calculate_date(self):
        for record in self:
            record.month = False
            record.year = False
            if record.ngay_bao_cao:
                record.month = record.ngay_bao_cao.month
                record.year = record.ngay_bao_cao.year

    def get_data(self):

        self.state = 'get_data'
        # 1. Lấy doanh số chỉ tiêu
        plan = self.env['crm.sale.payment.plan'].sudo().search(
            [('company_id', '=', self.company_id.id), ('month', '=', self.month), ('year', '=', self.year)])
        self.ds_chi_tieu = plan.amount_proceeds

        # 2. Lấy doanh số ngày hiện tại và chi tiết doanh số
        # sale_payments = self.env['crm.sale.payment'].sudo().search(
        #     [('payment_date', '=', self.ngay_bao_cao), ('transaction_company_id', '=', self.company_id.id),
        #      ('account_payment_id', '!=', False)])
        if self.company_id.brand_id.id == 1:
            sale_payments = self.env['crm.sale.payment'].sudo().search(
                [('payment_date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id), ('khong_tinh_doanh_so', '=', False),
                 ('booking_id.source_id', 'not in', tuple(map(int, self.env['ir.config_parameter'].sudo().get_param('no_money_kn').split(', '))))])
        else:
            sale_payments = self.env['crm.sale.payment'].sudo().search(
                [('payment_date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id),
                 ('khong_tinh_doanh_so', '=', False),
                 ('booking_id.source_id', 'not in', tuple(map(int, self.env['ir.config_parameter'].sudo().get_param('no_money_pr').split(', '))))])
        self.ds_ngay = sum(sale_payments.mapped('amount_proceeds'))
        self.sale_report_details = [(6, 0, sale_payments.ids)]
        # 3. Tính tổng doanh số tích lũy trong tháng
        self.ds_tich_luy = sum(self.env['sales.report'].sudo().search(
            [('month', '=', self.month), ('year', '=', self.year), ('state', '=', 'confirm'),
             ('company_id', '=', self.company_id.id), ('id', '!=', self.id), ('ngay_bao_cao', '<', self.ngay_bao_cao)]).mapped(
            'ds_ngay')) + sum(sale_payments.mapped('amount_proceeds'))

        # 4. Tính doanh số theo từng phòng
        spa = sale_payments.filtered(lambda sp: sp.department == 'Spa')
        self.ds_spa = sum(spa.mapped('amount_proceeds'))

        laser = sale_payments.filtered(lambda sp: sp.department == 'Laser')
        self.ds_laser = sum(laser.mapped('amount_proceeds'))

        pttm = sale_payments.filtered(lambda sp: sp.department == 'Surgery')
        self.ds_pttm = sum(pttm.mapped('amount_proceeds'))

        nha = sale_payments.filtered(lambda sp: sp.department == 'Odontology')
        self.ds_nha = sum(nha.mapped('amount_proceeds'))

        khac = sale_payments.filtered(lambda sp: not sp.department or sp.department == 'ChiPhi')
        self.ds_khac = sum(khac.mapped('amount_proceeds'))

        # 5.Tính doanh số theo từng hình thức thanh toán
        tm = sale_payments.filtered(lambda sp: sp.payment_method == 'tm')
        self.tm = sum(tm.mapped('amount_proceeds'))

        qt = sale_payments.filtered(lambda sp: sp.payment_method == 'pos')
        self.qt = sum(qt.mapped('amount_proceeds'))

        ck = sale_payments.filtered(lambda sp: sp.payment_method == 'ck')
        self.ck = sum(ck.mapped('amount_proceeds'))

        # 6. Doanh số theo loại hàng bán
        dv = sale_payments.filtered(lambda sp: sp.crm_line_id)
        self.ds_dich_vu = sum(dv.mapped('amount_proceeds'))

        sp = sale_payments.filtered(lambda sp: sp.crm_line_product_id)
        self.ds_san_pham = sum(sp.mapped('amount_proceeds'))

    def sent_data(self):
        sale_report_exists = self.env['sales.report'].search(
            [('ngay_bao_cao', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id),
             ('state', '=', 'confirm')])
        if sale_report_exists:
            raise ValidationError('Đã tồn tại báo cáo của ngày hôm nay.')
        self.state = 'confirm'
        self.sudo().with_delay(priority=1, channel='channel_job_sale_report').sync_record_sr(id=self.id)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '[%s] %s ' % (record.ngay_bao_cao.strftime('%d-%m-%Y'), record.company_id.name)))
        return res

    def unlink(self):
        for record in self:
            if record.state == 'confirm':
                raise ValidationError('Không thể xóa báo cáo doanh số khi đã được gửi đi.')
        return super(SalesReport, self).unlink()

    @api.constrains('ngay_bao_cao', 'company_id')
    def validate_ngay_bao_cao(self):
        for rec in self:
            if rec.ngay_bao_cao:
                sale_report_exists = self.env['sales.report'].search(
                    [('ngay_bao_cao', '=', rec.ngay_bao_cao), ('company_id', '=', rec.company_id.id),
                     ('id', '!=', rec.id)])
                if sale_report_exists:
                    raise ValidationError('Đã tồn tại báo cáo của ngày %s của chi nhánh %s.' % (
                        rec.ngay_bao_cao.strftime("%d/%m/%Y"), rec.company_id.name))

    def get_url_token(self):
        config = self.env['ir.config_parameter'].sudo()
        url = config.get_param('url_odoo_16')
        login = config.get_param('login_odoo_16')
        password = config.get_param('password_odoo_16')
        url_get_token = url + '/api/auth/token'
        body_get_token = {
            "login": login,
            "password": password
        }
        header = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response_token = requests.request('POST', url=url_get_token, data=json.dumps(body_get_token), headers=header)
        token = response_token.json()['result']['data']['access_token']
        return url, token

    @job
    def sync_record_sr(self, id):
        sale_report = self.sudo().browse(id)
        body = {
            "erp_id": int(sale_report.id),
            "ngay_bao_cao": str(sale_report.ngay_bao_cao),
            "company_id": int(sale_report.company_id.id),
            "currency_id": str(sale_report.currency_id.name),
            "ds_chi_tieu": int(sale_report.ds_chi_tieu),
            "ds_ngay": int(sale_report.ds_ngay),
            "ds_tich_luy": int(sale_report.ds_tich_luy),
            "ds_dich_vu": int(sale_report.ds_dich_vu),
            "ds_san_pham": int(sale_report.ds_san_pham),
            "ds_spa": int(sale_report.ds_spa),
            "ds_laser": int(sale_report.ds_laser),
            "ds_nha": int(sale_report.ds_nha),
            "ds_pttm": int(sale_report.ds_pttm),
            "ds_khac": int(sale_report.ds_khac),
            "tm": int(sale_report.tm),
            "ck": int(sale_report.ck),
            "qt": int(sale_report.qt),
            "state": sale_report.state,
            "ti_le_hoan_thanh": sale_report.ti_le_hoan_thanh
        }
        url, token = self.get_url_token()

        url = url + '/sale_report/create'
        headers = {
            'access-token': token,
            'Content-Type': 'application/json',
        }
        response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
        # self.env['api.log'].sudo().create({
        #     'name': 'Tạo báo cáo doanh số',
        #     'input': body,
        #     'response': response.json()
        # })
        response.json()
