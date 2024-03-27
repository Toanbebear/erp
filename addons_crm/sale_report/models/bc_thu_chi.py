from odoo import fields, models, api, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class BCThuChi(models.Model):
    _name = "bc.thu.chi"
    _description = 'Báo cáo thu chi'

    ngay_bao_cao = fields.Date(string='Ngày báo cáo', default=date.today())
    company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.company)
    brand_id = fields.Many2one(related='company_id.brand_id', string='Thương hiệu')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    tong_thu = fields.Monetary('Tổng thu', compute='tinh_toan_tong_thu', store=True)
    tm = fields.Monetary('Tiền mặt')
    qt = fields.Monetary('Quẹt thẻ')
    ck = fields.Monetary('Chuyển khoản')
    ngoai_te = fields.Monetary('Ngoại tệ')
    nhan_quy = fields.Monetary('Nhận quỹ')
    ton_dau = fields.Monetary('Tồn đầu')
    tong_chi_cn = fields.Monetary('Tổng chi tại chi nhánh',
                                  help="Lấy từ phiếu chi có sổ là sổ tiềm mặt VND tại chi nhánh")
    nop_quy = fields.Monetary('Chi nộp quỹ')
    tong_chi = fields.Monetary('Tổng chi', compute='tinh_toan_tong_chi', store=True)
    ton_cuoi = fields.Monetary('Tồn cuối', compute='tinh_toan_ton_cuoi', store=True)
    state = fields.Selection(
        [('draft', 'Nháp'), ('get_data', 'Lấy dữ liệu'), ('confirm', 'Xác nhận'), ('cancel', 'Hủy')],
        string="Trạng thái", default='draft')

    phieu_thu = fields.Many2many('account.payment', string='Danh sách thu tiền')
    phieu_nhan_quy = fields.Many2many('account.move', string='Danh sách nhận quỹ')
    # phieu_chi_khach_ncc = fields.Many2many('account.payment', 'phieu_chi_khach_ncc_rel', string='Chi tiền cho KH và NCC')
    phieu_chi_tai_cn = fields.Many2many('account.move', 'phieu_chi_khac_rel', string='Phiếu chi tại chi nhánh')
    phieu_nop_quy = fields.Many2many('account.move', 'phieu_nop_quy_rel', string='Nộp quỹ')

    # def unlink(self):
    #     for sp in self:
    #         if sp.state == 'confirm':
    #             raise ValidationError('Bạn không thể xóa khi đã xác nhận')
    #         return super(BCThuChi, self).unlink()

    @api.depends('tm', 'qt', 'ck', 'ngoai_te', 'nhan_quy')
    def tinh_toan_tong_thu(self):
        for record in self:
            record.tong_thu = 0
            tong_thu = 0
            if record.tm:
                tong_thu += record.tm
            if record.qt:
                tong_thu += record.qt
            if record.ck:
                tong_thu += record.ck
            if record.ngoai_te:
                tong_thu += record.ngoai_te
            if record.nhan_quy:
                tong_thu += record.nhan_quy
            record.tong_thu = tong_thu

    @api.depends('tong_chi_cn', 'nop_quy')
    def tinh_toan_tong_chi(self):
        for record in self:
            record.tong_chi = 0
            tong_chi = 0
            if record.nop_quy:
                tong_chi += record.nop_quy
            if record.tong_chi_cn:
                tong_chi += record.tong_chi_cn
            record.tong_chi = tong_chi

    # @api.depends('ton_dau', 'tong_thu', 'tong_chi')
    # def tinh_toan_ton_cuoi(self):
    #     for record in self:
    #         record.ton_cuoi = 0
    #         ton_dau = record.ton_dau if record.ton_dau else 0
    #         tong_thu = record.tong_thu if record.tong_thu else 0
    #         tong_chi = record.tong_chi if record.tong_chi else 0
    #         record.ton_cuoi = ton_dau + tong_thu - tong_chi
    @api.depends('ton_dau', 'tm', 'tong_chi', 'nhan_quy')
    def tinh_toan_ton_cuoi(self):
        for record in self:
            record.ton_cuoi = 0
            ton_dau = record.ton_dau if record.ton_dau else 0
            tm = record.tm if record.tm else 0
            nhan_quy = record.nhan_quy if record.nhan_quy else 0
            tong_chi = record.tong_chi if record.tong_chi else 0
            record.ton_cuoi = ton_dau + (tm + nhan_quy) - tong_chi

    def get_data(self):
        self.state = 'get_data'

        """
        TỒN ĐẦU: Lấy giá trị tồn cuối của ngày liền trước
        """
        date_check = self.ngay_bao_cao - timedelta(days=1)
        ngay_lien_truoc = self.env['bc.thu.chi'].sudo().search([('ngay_bao_cao', '=', date_check), ('company_id', '=', self.company_id.id)])
        if ngay_lien_truoc and ngay_lien_truoc.ton_cuoi:
            self.ton_dau = ngay_lien_truoc.ton_cuoi
        else:
            self.ton_dau = 0

        """ TỔNG THU
        I. Tiền mặt/Quẹt thẻ/Chuyển khoản/Ngoại tệ: Lấy từ phiếu thu (account.payment) có hình thức thanh toán tương ứng
        II. Nhận quỹ: Lấy từ bút toán (account.move) được tick trường nhan_quy
        """
        payment_inbound = self.env['account.payment'].sudo().search(
            [('payment_date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id),
             ('state', 'not in', ['draft', 'cancelled']), ('payment_type', '=', 'inbound')])
        self.phieu_thu = [(6, 0, payment_inbound.ids)]
        vnd = self.env.ref('base.VND')
        tm = payment_inbound.filtered(lambda ap: (ap.payment_method == 'tm') and (ap.currency_id == vnd))
        self.tm = sum(tm.mapped('amount_vnd'))
        qt = payment_inbound.filtered(lambda ap: (ap.payment_method == 'pos') and (ap.currency_id == vnd))
        self.qt = sum(qt.mapped('amount_vnd'))
        ck = payment_inbound.filtered(lambda ap: (ap.payment_method in ['ck', 'vdt']) and (ap.currency_id == vnd))
        ck_outbound = self.env['account.payment'].sudo().search(
            [('payment_date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id), ('partner_type', '=', 'customer'),
             ('state', 'not in', ['draft', 'cancelled']), ('payment_type', '=', 'outbound'), ('payment_method', '=', 'ck')])
        if ck_outbound:
            for record in ck_outbound:
                self.phieu_thu = [(4, record.id)]
        self.ck = sum(ck.mapped('amount_vnd')) - sum(ck_outbound.mapped('amount_vnd'))
        ngoai_te = payment_inbound.filtered(lambda ap: ap.currency_id != vnd)
        self.ngoai_te = sum(ngoai_te.mapped('amount_vnd'))
        nhan_quy = self.env['account.move'].sudo().search(
            [('date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id),
             ('state', 'in', ['posted']), ('tas_type', '=', 'inbound'), ('thu_quy', '=', True)])
        self.nhan_quy = sum(nhan_quy.mapped('amount_total'))
        self.phieu_nhan_quy = [(6, 0, nhan_quy.ids)]

        # TỔNG CHI
        """
        I. Tổng chi tại chi nhánh (lấy theo sổ VND tại điểm chi nhánh): Lấy ra các bút toán có loại là phiếu chi và sổ là sổ tiền mặt VND tại điểm chi nhánh
        II. Chi nộp quỹ : Bằng các bút toán được tick trường nộp quỹ
        """
        # Chi tại chi nhánh
        journal = self.env['account.journal'].sudo().search(
            [('company_id', '=', self.company_id.id), ('type', '=', 'cash'),
             ('currency_id', '=', self.env.ref('base.VND').id), ('name', 'ilike', 'VND tại điểm')])

        move_outbound = self.env['account.move'].sudo().search(
            [('date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id),
             ('tas_type', '=', 'outbound'), ('state', 'in', ['posted']), ('nop_quy', '=', False),
             ('state', 'not in', ['draft', 'cancelled']), ('journal_id', '=', journal.id)])
        self.tong_chi_cn = sum(move_outbound.mapped('amount_total'))
        self.phieu_chi_tai_cn = [(6, 0, move_outbound.ids)]

        nop_quy = self.env['account.move'].sudo().search(
            [('date', '=', self.ngay_bao_cao), ('company_id', '=', self.company_id.id),
             ('state', 'in', ['posted']), ('tas_type', '=', 'outbound'), ('nop_quy', '=', True), ('journal_id', '=', journal.id)])
        abs_amount_nop_quy = [abs(i) for i in nop_quy.mapped('amount_total_signed')]
        self.nop_quy = sum(abs_amount_nop_quy)
        self.phieu_nop_quy = [(6, 0, nop_quy.ids)]

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, '[%s] %s ' % (record.ngay_bao_cao.strftime('%d-%m-%Y'), record.company_id.name)))
        return res

    def sent_data(self):
        self.state = 'confirm'
        self.sudo().with_delay(priority=0, channel='channel_job_bc_thu_chi').sync_record_bc_thu_chi(id=self.id)

    @job
    def sync_record_bc_thu_chi(self, id):
        record = self.sudo().browse(id)
        list_chi_nhanh = []
        if record.phieu_chi_tai_cn:
            for line in record.phieu_chi_tai_cn:
                list_chi_nhanh.append({
                    "type": "1",
                    "date": str(line.date),
                    "name": str(line.name),
                    "lydo": str(line.lydo),
                    "currency_id": str(record.currency_id.name),
                    "amount_total": int(line.amount_total)
                })
        list_nop_quy = []
        if record.phieu_nop_quy:
            for line in record.phieu_nop_quy:
                list_nop_quy.append({
                    "type": "2",
                    "date": str(line.date),
                    "name": str(line.name),
                    "lydo": str(line.lydo),
                    "currency_id": str(record.currency_id.name),
                    "amount_total": int(line.amount_total)
                })
        body = {
            "erp_id": int(record.id),
            "ngay_bao_cao": str(record.ngay_bao_cao),
            "company_id": int(record.company_id.id),
            "currency_id": str(record.currency_id.name),
            "tong_thu": int(record.tong_thu),
            "tm": int(record.tm),
            "qt": int(record.qt),
            "ck": int(record.ck),
            "ngoai_te": int(record.ngoai_te),
            "nhan_quy": int(record.nhan_quy),
            "ton_dau": int(record.ton_dau),
            "tong_chi_cn": int(record.tong_chi_cn),
            "nop_quy": int(record.nop_quy),
            "tong_chi": int(record.tong_chi),
            "ton_cuoi": int(record.ton_cuoi),
            "state": record.state,
            "bc_thu_chi_detail_1": list_chi_nhanh,
            "bc_thu_chi_detail_2": list_nop_quy
        }
        config = self.env['ir.config_parameter'].sudo()
        url_root = config.get_param('url_odoo_16')
        # Lấy token
        url_get_token = url_root + '/api/auth/token'
        body_get_token = {
            "login": config.get_param('login_odoo_16'),
            "password": config.get_param('password_odoo_16')
        }
        header = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response_token = requests.request('POST', url=url_get_token, data=json.dumps(body_get_token), headers=header)
        token = response_token.json()['result']['data']['access_token']
        url = url_root + '/bc_thu_chi/create'
        headers = {
            'access-token': token,
            'Content-Type': 'application/json',
        }
        response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)
        response.json()
