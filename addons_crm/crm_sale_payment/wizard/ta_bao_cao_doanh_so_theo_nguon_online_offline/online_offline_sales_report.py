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
from openpyxl.utils.cell import get_column_letter

REGION = [
    ('mb', 'Miền Bắc'),
    ('mt', 'Miền Trung'),
    ('mn', 'Miền Nam')
]


class OnlineOfflineSaleReport(models.TransientModel):
    _name = 'online.offline.sales.report'
    _description = 'Báo cáo doanh số online/offline theo tháng'

    start_date = fields.Date(string='Từ ngày',
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    data = fields.Binary('File', readonly=True)
    name = fields.Char('File Name', readonly=True)
    brand_id = fields.Many2one(string='Thương hiệu', comodel_name='res.brand', domain=lambda self: [('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
    company_id = fields.Many2one(string='Chi nhánh', comodel_name='res.company', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
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
        return sale_payment_list

    # Tao bao cao
    def create_report(self):
        # datas = self._get_data_report()

        # in dữ liệu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        if self.brand_id:
            brands = self.env['res.brand'].search([('id', '=', self.brand_id.id)])
        else:
            brands = self.env['res.brand'].search([('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
        for brand in brands:
            ws = wb.add_worksheet(str(brand.name).upper())
            # add icon

            # format
            normal_bold = wb.add_format({'font_name': 'Times New Roman', 'bold': True, 'font_size': 10, 'align': 'left',
                                         'text_wrap': True, 'border': False})
            normal_bold_bolder = wb.add_format({'font_name': 'Times New Roman', 'bold': True, 'font_size': 10, 'align': 'left',
                                         'text_wrap': True, 'border': True, 'num_format': '###,###,###'})
            normal_bolder = wb.add_format({'font_name': 'Times New Roman', 'bold': False, 'font_size': 10, 'align': 'left',
                                         'text_wrap': True, 'border': True, 'num_format': '###,###,###'})

            row = 1
            col = 0

            #header
            brand_name = brand.name
            if self.region == 'mb':
                region = 'MIỀN BẮC'
            elif self.region == 'mt':
                region = 'MIỀN TRUNG'
            elif self.region == 'mn':
                region = 'MIỀN NAM'
            else:
                region = 'TOÀN QUỐC'

            if self.company_id:
                companies = self.env['res.company'].search([('id', '=', self.company_id.id)])
            else:
                companies = self.env['res.company'].search([('brand_id', '=', brand.id),
                                                            ('id', 'in', self.env.user.company_ids.ids)])
                if self.region:
                    zone = self.region
                    companies = companies.search([('zone', '=', zone)])
            title = 'BÁO CÁO DOANH SỐ ONLINE - OFFLINE ' + str(brand_name).upper() + ' ' + str(region).upper() + ' TỪ NGÀY ' + str(self.start_date.strftime("%d/%m/%Y")) + ' ĐẾN NGÀY ' + str(self.end_date.strftime("%d/%m/%Y"))

            ws.merge_range('A2:K2', title, normal_bold)
            row += 1
            ws.merge_range(row, 0, row + 1, 0, 'Ngày', normal_bold_bolder)
            col = 1
            for company in companies:
                ws.merge_range(row, col, row, col + 1, company.name, normal_bold_bolder)
                ws.write(row + 1, col, 'DS Online', normal_bolder)
                ws.set_column(col, 25)
                col += 1
                ws.write(row + 1, col, 'DS Offline', normal_bolder)
                ws.set_column(col, 25)
                col += 1
            row += 1
            start = self.start_date
            end = self.end_date
            col_max = 0
            sales = self._get_data_report()
            while start <= end:
                row += 1
                ws.write(row, 0, start.strftime("%d/%m/%Y"), normal_bolder)
                start += timedelta(days=1)
            row += 1
            ws.write(row, 0, 'Không xác định', normal_bolder)
            col = 1
            for company in companies:
                row = 3
                company_sale = sales.filtered(lambda x: x.company_id == company)
                sales -= company_sale
                sales_online = company_sale.filtered(lambda x: x.booking_id.source_id.type_source == 'online')
                sales_offline = company_sale.filtered(lambda x: x.booking_id.source_id.type_source == 'offline')
                sales_unknown = company_sale - sales_offline - sales_online
                start = self.start_date
                while start <= end:
                    row += 1
                    sum_amount_online = sum(sales_online.filtered(lambda x:
                                                                  x.payment_date == start).mapped('amount_proceeds'))
                    ws.write(row, col, sum_amount_online, normal_bolder)
                    sum_amount_offline = sum(sales_offline.filtered(lambda x:
                                                                    x.payment_date == start).mapped('amount_proceeds'))
                    ws.write(row, col + 1, sum_amount_offline, normal_bolder)
                    start += timedelta(days=1)
                row += 1
                ws.merge_range(row, col, row, col + 1, sum(sales_unknown.mapped('amount_proceeds')), normal_bolder)
                row += 1
                ws.write(row, 0, 'TỔNG CỘNG', normal_bold_bolder)
                ws.write(row, col, sum(sales_online.mapped('amount_proceeds')), normal_bolder)
                ws.write(row, col+1, sum(sales_offline.mapped('amount_proceeds')), normal_bolder)
                row += 1
                ws.write(row, 0, 'Tổng', normal_bold_bolder)
                ws.merge_range(row, col, row, col + 1, sum(company_sale.mapped('amount_proceeds')), normal_bolder)
                col += 2
        wb.close()

        # fp = BytesIO()
        # wb.save(fp)
        # fp.seek(0)
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_doanh_so_online_offline_theo_thang.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO DOANH SỐ ONLINE & OFFLINE THEO THÁNG',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }




