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
from openpyxl.utils.cell import get_column_letter as gcl

REGION = [
    ('mb', 'Miền Bắc'),
    ('mt', 'Miền Trung'),
    ('mn', 'Miền Nam')
]


class SourceSaleReport(models.TransientModel):
    _name = 'source.sales.report'
    _description = 'Báo cáo doanh số theo nguồn tháng'

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

    def _get_data_report(self, company_list):
        data = {}
        domain = [
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            ('company_id.id', 'in', company_list.ids),
            ('amount_proceeds', '!=', 0),
            ('not_sale', '=', False),
            ('booking_id.type', '=', 'opportunity'),
        ]
        sale_payment_list = self.env['crm.sale.payment'].sudo().search(domain)
        source_group = self.env['crm.category.source'].sudo().search([])
        sources_all = self.env['utm.source'].sudo().search([])

        for group in source_group:
            if data.get(group.name, 0) is 0:
                data[group.name] = {}
            sources_in_group = sources_all.filtered(lambda x: x.accounting_source_category.id == group.id)
            for source in sources_in_group:
                pay_in_source = sale_payment_list.filtered(lambda x: x.crm_line_id.source_extend_id.id == source.id
                                                                     or x.crm_line_product_id.source_extend_id.id == source.id)
                sale_payment_list -= pay_in_source
                if data[group.name].get(source.name, 0) is 0:
                    data[group.name][source.name] = {}
                for company in company_list:
                    pay_in_company = pay_in_source.filtered(lambda x: x.company_id.id == company.id)
                    if data[group.name][source.name].get(company.name, 0) is 0:
                        data[group.name][source.name][company.name] = sum(pay_in_company.mapped('amount_proceeds'))
                    else:
                        data[group.name][source.name][company.name] += sum(pay_in_company.mapped('amount_proceeds'))
        if sale_payment_list:
            not_source = 'Không xác định'
            data[not_source] = {}
            data[not_source][not_source] = {}
            for company in company_list:
                pay_in_company = sale_payment_list.filtered(lambda x: x.company_id.id == company.id)
                if data[not_source][not_source].get(company.name, 0) is 0:
                    data[not_source][not_source][company.name] = sum(pay_in_company.mapped('amount_proceeds'))
                else:
                    data[not_source][not_source][company.name] += sum(pay_in_company.mapped('amount_proceeds'))
        return data

    # Tao bao cao
    def create_report(self):
        # datas = self._get_data_report()

        # in dữ liệu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        if self.brand_id:
            brands = self.env['res.brand'].sudo().search([('id', '=', self.brand_id.id)])
        else:
            brands = self.env['res.brand'].sudo().search([('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
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
            normal_yellow_bolder = wb.add_format({'font_name': 'Times New Roman', 'bg_color': 'yellow', 'bold': False, 'font_size': 10, 'align': 'left',
                                           'text_wrap': True, 'border': True, 'num_format': '###,###,###'})
            normal_red_bolder = wb.add_format({'font_name': 'Times New Roman', 'bg_color': '#de9595', 'bold': False, 'font_size': 10, 'align': 'left',
                                           'text_wrap': True, 'border': True, 'num_format': '###,###,###'})
            ws.set_column('A:P', 20)

            row = 1
            col = 0

            # title
            brand_name = brand.name
            if self.company_id:
                company_name = ' CHI NHÁNH ' + str(self.company_id.name) + ' '
            else:
                company_name = ''

            start = self.start_date.strftime("%d/%m/%Y")
            end = self.end_date.strftime("%d/%m/%Y")
            title = 'BÁO CÁO DOANH SỐ THEO NGUỒN ' + str(brand_name).upper() + str(company_name) + ' TỪ NGÀY ' + str(start) + ' ĐẾN NGÀY ' + str(end)

            ws.merge_range('A2:C3', title, normal_bold)
            row += 2

            if self.company_id:
                companies = self.env['res.company'].sudo().search([('id', '=', self.company_id.id)])
            else:
                companies = self.env['res.company'].sudo().search([('brand_id', '=', brand.id),
                                                                   ('id', 'in', self.env.user.company_ids.ids)])
                if self.region:
                    zone = self.region
                    companies = companies.sudo().search([('zone', '=', zone)])
            # header

            headers = ['Nhóm nguồn', 'Nguồn mở rộng']

            for rec in headers:
                ws.write(row, col, rec, normal_bold_bolder)
                col += 1
            for company in companies:
                ws.write(row, col, company.name, normal_bold_bolder)
                col += 1
            ws.write(row, col, 'Tổng cộng', normal_bold_bolder)
            row += 1

            sales = self._get_data_report(companies)
            for group in sales:
                ws.write(row, 0, group, normal_yellow_bolder)
                ws.write(row, 1, '', normal_yellow_bolder)
                row_set = row
                row += 1
                for source in sales[group]:
                    col = 2
                    sum_amount = 0
                    ws.write(row, 1, source, normal_bolder)
                    ws.write(row, 0, '', normal_bolder)
                    for company in companies:
                        amount = sales[group][source].get(company.name, 0)
                        sum_amount += amount
                        ws.write(row, col, amount, normal_bolder)
                        col += 1
                    ws.write(row, col, sum_amount, normal_bolder)
                    row += 1
                for col in range(2, len(companies)+3):
                    if len(sales[group]):
                        ws.write_formula(gcl(col + 1) + str(row_set + 1),
                                         '=SUBTOTAL(9,' + gcl(col + 1) + str(row_set + 2) + ':' + gcl(col + 1) + str(row_set + 1 + len(sales[group])) + ')', normal_yellow_bolder)
                    else:
                        ws.write(row_set, col, 0, normal_yellow_bolder)
                    ws.write_formula(gcl(col + 1) + str(row + 1),
                                     '=SUBTOTAL(9,' + gcl(col + 1) + str(5) + ':' + gcl(col + 1) + str(
                                         row) + ')', normal_red_bolder)
            ws.write(row, 0, 'TỔNG CỘNG', normal_red_bolder)
            ws.write(row, 1, '', normal_red_bolder)



        wb.close()

        # fp = BytesIO()
        # wb.save(fp)
        # fp.seek(0)
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_doanh_so_theo_nguon_thang.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO DOANH SỐ THEO NGUỒN THÁNG',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }




