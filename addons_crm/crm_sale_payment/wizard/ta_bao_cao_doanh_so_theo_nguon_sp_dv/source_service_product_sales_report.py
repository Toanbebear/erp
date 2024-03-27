from odoo import api, fields, models, modules, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import xlsxwriter
import io
import base64
import pytz
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta, date
import roman

REGION = [
    ('mb', 'Miền Bắc'),
    ('mt', 'Miền Trung'),
    ('mn', 'Miền Nam')
]


class SourceServiceProductSaleReport(models.TransientModel):
    _name = 'source.service.product.sales.report'
    _description = 'Báo cáo doanh số theo nguồn dịch vụ sản phẩm'

    start_date = fields.Date(string='Từ ngày',
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    data = fields.Binary('File', readonly=True)
    name = fields.Char('File Name', readonly=True)
    brand_id = fields.Many2one(string='Thương hiệu',
                               comodel_name='res.brand',
                               domain=lambda self: [('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
    company_id = fields.Many2one(string='Chi nhánh',
                                 comodel_name='res.company',
                                 domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    region = fields.Selection(REGION, string='Miền', help="Vùng miền")

    @api.onchange('brand_id')
    def onchange_brand(self):
        self.company_id = None

    @api.onchange('region')
    def onchange_region(self):
        self.brand_id = None
        self.company_id = None

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        for record in self:
            start_date = fields.Date.from_string(record.start_date)
            end_date = fields.Date.from_string(record.end_date)
            days = (end_date - start_date).days
            if days < 0 or days > 365:
                raise ValidationError(
                    _("Ngày kết thúc không thể ở trước ngày bắt đầu khi xuất báo cáo!!!"))

    def _get_data_report(self):
        domain = [
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            ('amount_proceeds', '!=', 0),
            ('not_sale', '=', False),
        ]
        sale_payment_list = self.env['crm.sale.payment'].sudo().search(domain)
        # return_val = []
        # for evaluation in evaluations:
        #     return_val.append(self.render_form_template(evaluation))
        return sale_payment_list

    # Tao bao cao
    def create_report(self):
        # datas = self._get_data_report()

        # in dữ liệu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        ws = wb.add_worksheet('Tháng ' + str(self.end_date.month) + '-' + str(self.end_date.year))
        # add icon

        # format
        title_bold = wb.add_format({'font_name': 'Times New Roman', 'bold': True, 'font_size': 10,
                               'align': 'center', 'text_wrap': True, 'border': False})

        normal_bold = wb.add_format({'font_name': 'Times New Roman', 'bold': True,
                                     'font_size': 10, 'align': 'left', 'text_wrap': True, 'border': False})
        normal_bold_bolder = wb.add_format({'font_name': 'Times New Roman', 'bold': True, 'font_size': 10,
                                            'align': 'left', 'text_wrap': True, 'border': True, 'num_format': '###,###,###'})
        normal_bolder = wb.add_format({'font_name': 'Times New Roman', 'bold': False, 'font_size': 10, 'align': 'left',
                                     'text_wrap': True, 'border': True, 'num_format': '###,###,###'})
        ws.set_column('C:P', 15)
        ws.set_column('A:A', 10)
        ws.set_column('B:B', 25)


        zone = []
        if self.region:
            zone.append(self.region)
        else:
            zone = ['mb', 'mt', 'mn']
        if self.brand_id:
            brands = self.brand_id
        else:
            brands = self.env['res.brand'].search([('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
        if self.company_id:
            companies = self.company_id
            brands = self.company_id.brand_id
            zone = [self.company_id.zone]
        else:
            companies = self.env['res.company'].search([('brand_id', 'in', brands.ids),
                                                        ('zone', 'in', zone),
                                                        ('id', 'in', self.env.user.company_ids.ids)])
        row = 1
        col = 0

        start = self.start_date.strftime("%d/%m/%Y")
        end = self.end_date.strftime("%d/%m/%Y")
        title = 'BÁO CÁO DOANH SỐ THEO NGUỒN SẢN PHẨM DỊCH VỤ TỪ NGÀY ' + str(start) + ' ĐẾN NGÀY ' + str(end)
        ws.merge_range('A2:K3', title, title_bold)
        row += 3
        #     header
        headers = ['',
                   '',
                   'Doanh số dịch vụ MKT online, DVKH)',
                   'DOANH SỐ OFFLINE (Trade Marketing + Bộ phận kinh doanh)',
                   'Sản phẩm',
                   'Khách hàng cũ quay lại, khách hàng vãng lai,...',
                   'CTV giới thiệu , bạn bè giới thiệu, cán bộ CNV, cán bộ nhân viên',
                   'Thuê PM',
                   'TỔNG',
                   'CHI PHÍ ROI (20% DS VƯỢT TRẦN KHUYẾN MẠI)',
                   'Ghi chú']

        for rec in headers:
            ws.write(row, col, rec, normal_bold_bolder)
            col += 1
        row += 1
        col = 0
        index = 0
        sales = self._get_data_report()
        for brand in brands:
            index += 1
            brand_total = 0
            brand_online = 0
            brand_offline = 0
            brand_product = 0
            brand_collaborator = 0
            brand_tpm = 0
            brand_remaining = 0
            for region in zone:
                row_start = row
                if self.company_id:
                    company = self.company_id
                else:
                    company = companies.search([('brand_id', '=', brand.id),
                                                ('zone', '=', region),
                                                ('id', 'in', self.env.user.company_ids.ids)])
                if company:
                    for rec in company:
                        # compute
                        company_sale = sales.filtered(lambda x: x.company_id == rec)
                        sales -= company_sale
                        total = 0
                        online = 0
                        offline = 0
                        product = 0
                        collaborator = 0
                        tpm = 0
                        for sale in company_sale:
                            total += sale.amount_proceeds
                            if sale.source_type == 'online':
                                online += sale.amount_proceeds
                            if sale.source_type == 'offline':
                                offline += sale.amount_proceeds
                            if sale.product_id:
                                product += sale.amount_proceeds
                            if sale.category_source_id.code == 'CTV':
                                collaborator += sale.amount_proceeds
                            if sale.category_source_id.code == 'TPM':
                                tpm += sale.amount_proceeds
                        remaining = total - (online + offline + product)
                        brand_total += total
                        brand_online += online
                        brand_offline += offline
                        brand_product += product
                        brand_collaborator += collaborator
                        brand_tpm += tpm
                        brand_remaining += remaining
                        # Chi nhanh
                        col = 1
                        ws.write(row, col, rec.name, normal_bolder)
                        col += 1
                        # Doanh so online
                        ws.write(row, col, online, normal_bolder)
                        col += 1
                        # Doanh so offline
                        ws.write(row, col, offline, normal_bolder)
                        col += 1
                        # Doanh so theo san pham
                        ws.write(row, col, product, normal_bolder)
                        col += 1
                        # Doanh so theo khach hang cu, quay lai
                        ws.write(row, col, remaining, normal_bolder)
                        col += 1
                        # Doanh so CTV
                        ws.write(row, col, collaborator, normal_bolder)
                        col += 1
                        # Doanh so TPM
                        ws.write(row, col, tpm, normal_bolder)
                        col += 1
                        # Tong
                        ws.write(row, col, total, normal_bolder)
                        col += 1
                        # ROI
                        ws.write(row, col, total*0.2, normal_bolder)
                        col += 1
                        # Ghi tru
                        ws.write(row, col, '', normal_bolder)
                        row += 1
                        if len(company) > 1:
                            ws.merge_range(row_start, 0, row - 1, 0, str(brand.code + '-' + region.upper()), normal_bolder)
                        else:
                            ws.write(row_start, 0, str(brand.code + '-' + region.upper()), normal_bolder)
            ws.write(row, 0, roman.toRoman(index), normal_bold_bolder)
            col = 1
            ws.write(row, col, 'Tổng ' + brand.name, normal_bold_bolder)
            col += 1
            # Doanh so online
            ws.write(row, col, brand_online, normal_bold_bolder)
            col += 1
            # Doanh so offline
            ws.write(row, col, brand_offline, normal_bold_bolder)
            col += 1
            # Doanh so theo san pham
            ws.write(row, col, brand_product, normal_bold_bolder)
            col += 1
            # Doanh so theo khach hang cu, quay lai
            ws.write(row, col, brand_remaining, normal_bold_bolder)
            col += 1
            # Doanh so CTV
            ws.write(row, col, brand_collaborator, normal_bold_bolder)
            col += 1
            # Doanh so TPM
            ws.write(row, col, brand_tpm, normal_bold_bolder)
            col += 1
            # Tong
            ws.write(row, col, brand_total, normal_bold_bolder)
            col += 1
            # ROI
            ws.write(row, col, brand_total*0.2, normal_bold_bolder)
            col += 1
            # Ghi tru
            ws.write(row, col, '', normal_bold_bolder)
            row += 1
        wb.close()

        # fp = BytesIO()
        # wb.save(fp)
        # fp.seek(0)
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_doanh_so_theo_nguon_dich_vu_san_pham.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO DOANH SỐ THEO NGUỒN DỊCH VỤ SẢN PHẨM',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }




