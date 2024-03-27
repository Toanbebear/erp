from odoo import api, fields, models, modules, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import xlsxwriter
from openpyxl.utils.cell import get_column_letter as gcl
import io
import base64
import pytz
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta, date


def _start_month(month, year):
    return datetime(year, month, 1)


def _end_month(month, year):
    days_of_month = monthrange(year, month)
    return datetime.combine(date(year, month, days_of_month[1]), datetime.max.time())


def write_cell(ws, value, row_current, col_current, row_diff, col_add, row_add, format_cell):
    # chỉ ghi trong 1 ô
    if row_add == 0 and col_add == 0:
        ws.write(row_current + row_diff, col_current,
                 value, format_cell)
    # trường hợp cần merge cột / dòng
    else:
        if col_add > 1:
            col_current -= 1
        ws.merge_range(row_current + row_diff, col_current - col_add,
                       row_current + (row_diff + row_add), col_current,
                       value, format_cell)
    return row_current, col_current


def build_format(workbook, format_list, _type=None):
    format_dirt = {
        'font_name': 'Times New Roman',
        'font_size': 12 if _type == 'header' else 10,
        'text_wrap': True,
        'border': True,
        'align': 'center' if _type == 'header' else 'left',
        'valign': 'vcenter' if _type == 'header' else 'bottom',
        'bold': True if _type == 'header' else False,
    }
    for _format in format_list:
        format_dirt[_format[0]] = _format[1]
    return workbook.add_format(format_dirt)


class CRMSalePaymentReport(models.TransientModel):
    _name = 'crm.sale.payment.report'
    _description = 'Báo các doanh số'

    start_date = fields.Date(string='Từ ngày',
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    data = fields.Binary('File', readonly=True)
    name = fields.Char('File Name', readonly=True)
    brand_id = fields.Many2one(string='Thương hiệu', comodel_name='res.brand',
                               domain=lambda self: [('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
    company_id = fields.Many2one(string='Chi nhánh', comodel_name='res.company',
                                 domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    region = fields.Selection(string='Miền', selection=lambda self: self.env['res.company']._fields['zone'].selection)

    # @api.onchange('region')
    # def onchange_region(self):
    #     company_domain = []
    #     if self.region:
    #         company_domain.append(('zone', '=', self.region))
    #         self.brand_id = False
    #         self.company_id = False
    #     return {'domain': {'company_id': company_domain}}

    @api.onchange('brand_id')
    def onchange_brand(self):
        company_domain = [('zone', '=', self.region), ('id', 'in', self.env.user.company_ids.ids)]
        if self.brand_id:
            company_domain.append(('brand_id.id', '=', self.brand_id.id))
            self.company_id = False
        return {'domain': {'company_id': company_domain}}

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        for record in self:
            start_date = fields.Date.from_string(record.start_date)
            end_date = fields.Date.from_string(record.end_date)
            days = (end_date - start_date).days
            if days < 0 or days > 365:
                raise ValidationError(
                    _("Ngày kết thúc không thể ở trước ngày bắt đầu khi xuất báo cáo!!!"))

    def _get_data(self, company_list):
        data_company_dict = {}
        # Get all data init
        domain = [
            ('payment_date', '>=', _start_month(self.start_date.month, self.start_date.year)),
            ('payment_date', '<=', _end_month(self.end_date.month, self.end_date.year)),
            ('not_sale', '=', False),
        ]
        pays = self.env['crm.sale.payment'].sudo().search(domain)
        pays_plan = self.env['crm.sale.payment.plan'].sudo().search([])
        # Get total amount in monthrange
        for company in company_list:
            if data_company_dict.get(company.id, 0) is 0:
                data_company_dict[company.id] = {}
            for month in range(self.start_date.month, self.end_date.month + 1):
                # start_date = _start_month(month, self.start_date.year)
                # end_date = _end_month(month, self.end_date.year)

                # check special date
                start_date = _start_month(month, self.start_date.year)
                end_date = _end_month(month, self.end_date.year)
                if datetime.combine(self.start_date, datetime.min.time()) > _start_month(month, self.start_date.year):
                    start_date = datetime.combine(self.start_date, datetime.min.time())
                if datetime.combine(self.end_date, datetime.max.time()) < _end_month(month, self.end_date.year):
                    end_date = datetime.combine(self.end_date, datetime.max.time())

                plan_in_month = pays_plan.filtered(lambda x: str(start_date.month) == x.month and str(start_date.year) == x.year and x.company_id.id == company.id)
                plan_amount = plan_in_month.amount_proceeds if plan_in_month else 0
                pays_in_month = pays.filtered(lambda x: start_date.date() <= x.payment_date <= end_date.date() and x.company_id.id == company.id)
                total_in_month = sum(pay.amount_proceeds for pay in pays_in_month)
                data_company_dict[company.id][month] = (total_in_month, plan_amount)

        return data_company_dict

    # Tao bao cao
    def create_report(self):
        # in dữ liễu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        # format
        title_big = build_format(wb, [('font_size', 20), ('border', False)], 'header')
        header_green_bg = build_format(wb, [('bg_color', '#b3e69b')], 'header')
        normal = build_format(wb, [])
        normal_num = build_format(wb, [('num_format', '###,###,###,###'), ('align', 'right')])
        percent_num = build_format(wb, [('num_format', '###,###,###,###%'), ('align', 'right')])
        header_left = build_format(wb, [('align', 'left'), ('border', False)], 'header')

        footer_sub_center = build_format(wb, [('bg_color', '#fff75e'), ('align', 'center')])
        footer_sub_center_num = build_format(wb, [('num_format', '###,###,###,###'), ('bg_color', '#fff75e'), ('align', 'right')])
        footer_sub_center_percent = build_format(wb, [('num_format', '###,###,###,###%'), ('bg_color', '#fff75e'), ('align', 'right')])

        footer_center = build_format(wb, [('bg_color', '#92D050'), ('bold', True), ('align', 'center')])
        footer_num = build_format(wb, [('num_format', '###,###,###,###'), ('bg_color', '#92D050'), ('bold', True), ('align', 'right')])
        footer_percent = build_format(wb, [('num_format', '###,###,###,###%'), ('bg_color', '#92D050'), ('bold', True), ('align', 'right')])
        ws = wb.add_worksheet('Báo cáo chi tiết doanh số theo tháng')
        # add icon

        # build header
            # header[name,0,0,0]
            # header[1]: row_diff - xuống dòng
            # header[2]: col_add -  merge hàng
            # header[3]: row_add -  merge cột
        fix_header = [('Thương hiệu', 0, 0, 1, 20), ('Miền', 0, 0, 1, 20), ('Tên cơ sở', 0, 0, 1)]
        # add month
        for month in range(self.start_date.month, self.end_date.month + 1):
            month_header = [('Kế hoạch T%s' % month, 1, 0, 0),
                            ('Thực hiện T%s' % month, 1, 0, 0),
                            ('Tỷ trọng(%%) T%s' % month, 1, 0, 0),
                            ('Tháng %s/%s' % (month, self.start_date.year), 0, 2, 0)]
            fix_header.extend(month_header)
        # add year
        year_header = [('Kế hoạch %s' % self.start_date.year, 1, 0, 0),
                       ('Thực hiện %s' % self.start_date.year, 1, 0, 0),
                       ('Tỷ trọng(%)', 1, 0, 0),
                       ('Luỹ kế %s' % self.start_date.year, 0, 2, 0)]
        fix_header.extend(year_header)

        # write header
        row = 4
        col = 0
        ws.merge_range('A2:O2', "BÁO CÁO CHI TIẾT DOANH SỐ THEO THÁNG", title_big)
        ws.merge_range('A3:O3', "TỪ NGÀY %s ĐẾN NGÀY %s" %(self.start_date.strftime('%d/%m/%Y'), self.end_date.strftime('%d/%m/%Y')), header_left)
        ws.set_row(1, 30)
        ws.set_row(4, 30)
        ws.set_row(5, 30)
        for data in fix_header:
            row, col = write_cell(ws, data[0], row, col, data[1], data[2], data[3], header_green_bg)
            col += 1

        # write data
        brand_domain = []
        company_domain = [('zone', '!=', False), ('id', 'in', self.env.user.company_ids.ids)]
        region_list = self.env['res.company']._fields['zone'].selection

        if self.brand_id:
            brand_domain.append(('id', '=', self.brand_id.id))
            company_domain.append(('brand_id.id', '=', self.brand_id.id))
        if self.region:
            company_domain.append(('zone', '=', self.region))
            region_list = list(filter(lambda x: x[0] == self.region, self.env['res.company']._fields['zone'].selection))
        if self.company_id:
            company_domain.append(('id', '=', self.company_id.id))

        company_list = self.env['res.company'].sudo().search(company_domain)
        brand_list = self.env['res.brand'].sudo().search(brand_domain)
        company_brand = list((company_list.filtered(lambda x: x.brand_id.id == brand.id)) for brand in brand_list)

        sale_data = self._get_data(company_list)
        row += 2
        for brand, company_b in zip(brand_list, company_brand):
            if company_b:
                col = 0
                rowx = row
                # write_cell(ws, brand.name, row, col, 0, 0, len(company_b) - 1, normal) --> bỏ merger
                write_cell(ws, brand.name, row, col, 0, 0, 0, normal)

                company_region = list((company_b.filtered(lambda x: x.zone == region[0])) for region in region_list)
                for region, companies in zip(region_list, company_region):
                    if companies:
                        col = 1
                        # write_cell(ws, region[1], row, col, 0, 0, len(companies) - 1, normal) --> bỏ merge
                        write_cell(ws, region[1], row, col, 0, 0, 0, normal)
                        for company in companies:
                            col += 1
                            ws.write(row, col, company.name, normal)
                            luy_ke = [0, 0, 0]
                            if sale_data.get(company.id, []):
                                for sale in sale_data[company.id]:
                                    col += 1
                                    ws.write(row, col, sale_data[company.id][sale][1], normal_num)
                                    luy_ke[0] += sale_data[company.id][sale][1]
                                    col += 1
                                    ws.write(row, col, sale_data[company.id][sale][0], normal_num)
                                    luy_ke[1] += sale_data[company.id][sale][0]
                                    col += 1
                                    ti_trong = (sale_data[company.id][sale][0]/sale_data[company.id][sale][1]) if (sale_data[company.id][sale][1] != 0 and sale_data[company.id][sale][0] != 0) else 0
                                    ws.write(row, col, ti_trong, percent_num)
                                    luy_ke[2] = luy_ke[1]/luy_ke[0] if (luy_ke[0] != 0) else 0
                                # write luy ke
                                col += 1
                                ws.write(row, col, luy_ke[0], normal_num)
                                col += 1
                                ws.write(row, col, luy_ke[1], normal_num)
                                col += 1
                                ws.write(row, col, luy_ke[2], percent_num)
                            row += 1
                            col = 1

                # write footer line
                ws.write(row, 0, '', footer_sub_center)
                ws.write(row, 1, '', footer_sub_center)
                ws.write(row, 2, "Tổng %s" % brand.name, footer_sub_center)
                for colx in range(3, (len(list(sale_data.values())[0]) * 3 if sale_data.values() else 0) + 6):
                    formula = '=SUBTOTAL(9,' + gcl(colx + 1) + str(rowx + 1) + ':' + gcl(colx + 1) + str(row) + ')'
                    if (colx - 2) % 3 == 0:
                        ws.write_formula(gcl(colx + 1) + str(row + 1), formula, footer_sub_center_percent)
                    else:
                        ws.write_formula(gcl(colx + 1) + str(row + 1), formula, footer_sub_center_num)

                row += 1

        # set width column
        for data in fix_header:
            ws.set_column(row, col, data[4] if len(data) == 5 else 15)
            col += 1

        # write footer
        ws.write(row, 0, '', footer_center)
        ws.write(row, 1, '', footer_center)
        ws.write(row, 2, "Tổng cộng", footer_center)
        date_len = (len(list(sale_data.values())[0]) * 3 if sale_data.values() else 0)
        for colx in range(3, date_len + 6):
            formula = '=SUBTOTAL(9,' + gcl(colx + 1) + str(6 + 1) + ':' + gcl(colx + 1) + str(row) + ')'
            if (colx - 2) % 3 == 0:
                ws.write_formula(gcl(colx + 1) + str(row + 1), formula, footer_percent)
            else:
                ws.write_formula(gcl(colx + 1) + str(row + 1), formula, footer_num)
        row += 1

        wb.close()
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_chi_tiet_doanh_so_theo_thang.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO CHI TIẾT DOANH SỐ THEO THÁNG',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
