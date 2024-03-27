from odoo import api, fields, models, modules, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from pytz import timezone, utc
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


def _start_time(start_date, local_tz):
    start_datetime = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
    # start_datetime = local_tz.localize(start_datetime, is_dst=None)
    # return start_datetime.astimezone(utc).replace(tzinfo=None)
    return start_datetime


def _end_time(end_date, local_tz):
    end_datetime = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    # end_datetime = local_tz.localize(end_datetime, is_dst=None)
    # return end_datetime.astimezone(utc).replace(tzinfo=None)
    return end_datetime


def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)


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


def write_cell(ws, value, row_current, col_current, row_diff, col_add, row_add, format_cell, width_special=None):
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
    if width_special:
        ws.set_column(row_current, col_current, width_special)
    return row_current, col_current


class CRMSalePaymentDayReport(models.TransientModel):
    _name = 'crm.sale.payment.day.report'
    _description = 'Báo các doanh số theo ngày'

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

    # convert date to datetime for search domain, should be removed if using datetime directly
    start_datetime = fields.Datetime('Start datetime', compute='_compute_datetime')
    end_datetime = fields.Datetime('End datetime', compute='_compute_datetime')

    @api.onchange('brand_id')
    def onchange_brand(self):
        company_domain = [('zone', '=', self.region, ), ('id', 'in', self.env.user.company_ids.ids)]
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

    @api.depends('start_date', 'end_date')
    def _compute_datetime(self):
        self.start_datetime = False
        self.end_datetime = False
        if self.start_date and self.end_date:
            local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
            start_datetime = datetime(self.start_date.year, self.start_date.month, self.start_date.day, 0, 0, 0)
            end_datetime = datetime(self.end_date.year, self.end_date.month, self.end_date.day, 23, 59, 59)
            start_datetime = local_tz.localize(start_datetime, is_dst=None)
            end_datetime = local_tz.localize(end_datetime, is_dst=None)
            self.start_datetime = start_datetime.astimezone(utc).replace(tzinfo=None)
            self.end_datetime = end_datetime.astimezone(utc).replace(tzinfo=None)

    def _get_data(self, company_list):
        data_company_dict = {}

        # Get all data init
        domain = [
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            '|',
            ('company_id', 'in', company_list.ids),
            ('transaction_company_id', 'in', company_list.ids),
            ('not_sale', '=', False),
        ]
        domain_local = [
            ('update_date', '>=', _start_month(self.start_date.month, self.start_date.year)),
            ('update_date', '<=', _end_month(self.end_date.month, self.end_date.year)),
        ]
        pays = self.env['crm.sale.payment'].sudo().search(domain)
        pays_local = self.env['crm.sale.payment.local'].sudo().search(domain_local)

        # Get total amount in date range
        for company in company_list:
            if data_company_dict.get(company.id, 0) is 0:
                data_company_dict[company.id] = {}
            for day in daterange(self.start_date, self.end_date):
                local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
                start_time = _start_time(day, local_tz)
                end_time = _end_time(day, local_tz)
                pays_in_day = pays.filtered(
                    lambda x:
                    start_time.date() <= x.payment_date <= end_time.date()
                    and (x.company_id.id == company.id or x.transaction_company_id.id == company.id)
                )

                pays_local_in_day = pays_local.filtered(
                    lambda x:
                    start_time <= _start_time(x.update_date, local_tz) <= end_time
                    and x.company_id.id == company.id)

                total_inbound_in_day = sum(pay.amount_proceeds for pay in pays_in_day.filtered(
                    lambda x:
                    x.payment_type == 'inbound'
                    and x.internal_payment_type == 'tai_don_vi'
                    and x.company_id.id == company.id
                ))

                total_thu_ho = sum(pay.amount_proceeds for pay in pays_in_day.filtered(
                    lambda x:
                    x.payment_type == 'inbound'
                    and x.internal_payment_type == 'thu_ho'
                    and x.transaction_company_id.id == company.id
                ))

                total_duoc_thu_ho = sum(pay.amount_proceeds for pay in pays_in_day.filtered(
                    lambda x:
                    x.payment_type == 'inbound'
                    and x.internal_payment_type == 'thu_ho'
                    and x.company_id.id == company.id
                ))

                total_refund_in_day = sum(pay.amount_proceeds for pay in pays_in_day.filtered(
                    lambda x:
                    x.payment_type == 'outbound'
                    and x.internal_payment_type == 'tai_don_vi'
                    and x.company_id.id == company.id
                ))

                total_chi_ho = sum(pay.amount_proceeds for pay in pays_in_day.filtered(
                    lambda x:
                    x.payment_type == 'outbound'
                    and x.internal_payment_type == 'chi_ho'
                    and x.transaction_company_id.id == company.id
                ))

                total_duoc_chi_ho = sum(pay.amount_proceeds for pay in pays_in_day.filtered(
                    lambda x:
                    x.payment_type == 'outbound'
                    and x.internal_payment_type == 'chi_ho'
                    and x.company_id.id == company.id
                ))

                total_local_in_day = sum(pay.amount_proceeds for pay in pays_local_in_day)

                # doanh so ERP = nhan tien + hoan tien + duoc thu ho + duoc chi ho
                total_erp = total_inbound_in_day + total_refund_in_day + total_duoc_thu_ho + total_duoc_chi_ho
                data_company_dict[company.id][day.strftime('%d/%m/%Y')] = (total_erp,
                                                                           total_inbound_in_day,
                                                                           total_thu_ho,
                                                                           total_duoc_thu_ho,
                                                                           total_refund_in_day,
                                                                           total_chi_ho,
                                                                           total_duoc_chi_ho,
                                                                           total_local_in_day)
        return data_company_dict

    # Tao bao cao
    def create_report(self):
        # in dữ liễu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        # format
        header_dark_green_bg = build_format(wb, [('bg_color', '#92D050')], 'header')
        normal = build_format(wb, [])
        normal_num = build_format(wb, [('num_format', '###,###,###,###'), ('align', 'right')])
        footer = build_format(wb, [('bg_color', '#fff75e'), ('align', 'center')])
        footer_num = build_format(wb, [('num_format', '###,###,###,###'), ('bg_color', '#fff75e'), ('align', 'right')])

        # build domain
        brand_domain = []
        company_domain = [('id', 'in', self.env.user.company_ids.ids)]
        if self.brand_id:
            brand_domain.append(('id', '=', self.brand_id.id))
            company_domain.append(('brand_id.id', '=', self.brand_id.id))
        if self.region:
            company_domain.append(('zone', '=', self.region))
        if self.company_id:
            company_domain.append(('id', '=', self.company_id.id))

        company_list = self.env['res.company'].sudo().search(company_domain)

        sale_data = self._get_data(company_list)
        for company in company_list:
            ws = wb.add_worksheet(company.name)
            # add icon
            # build header
            # header[name,0,0,0]
                # header[1]: row_diff - xuống dòng
                # header[2]: col_add -  merge hàng
                # header[3]: row_add -  merge cột
            fix_header = [
                ('Ngày', 0, 0, 1),
                ('Nhận tiền tại đơn vị', 1, 0, 0),
                ('Thu hộ cơ sở khác', 1, 0, 0),
                ('Được cơ sở khác thu hộ', 1, 0, 0),
                ('Hoàn tiền tại đơn vị', 1, 0, 0),
                ('Hoàn tiền cho cơ sở khác', 1, 0, 0),
                ('Được cơ sở khác hoàn tiền cho', 1, 0, 0),
                ('DS KH mua thẻ', 1, 0, 0),
                ('Doanh số trên ERP', 1, 0, 0),
                ('Số liệu cơ sở', 1, 0, 0),
                ('Chênh lệnh', 1, 0, 0),
                ('Ghi chú', 1, 0, 0, 50),
                ('%s THÁNG TỪ NGÀY %s  ĐẾN NGÀY %s' %(company.name, self.start_date.strftime('%d/%m/%Y'), self.end_date.strftime('%d/%m/%Y')), 0, 10, 0),
            ]

            # write header
            row = 1
            col = 0
            # ws.merge_range('A2:I2', "BÁO CÁO CHI TIẾT DOANH SỐ THEO THÁNG", title_big)
            ws.set_row(1, 30)
            ws.set_row(2, 30)
            for data in fix_header:
                ws.set_column(row, col, 15)
                row, col = write_cell(ws, data[0], row, col, data[1], data[2], data[3], header_dark_green_bg, data[4] if len(data) == 5 else None)
                col += 1


            # write data
            row += 2
            col = 0
            for day in sale_data.get(company.id, []):
                values = [
                    day,  # ngay
                    sale_data[company.id][day][1],  # nhận tiền
                    sale_data[company.id][day][2],  # thu ho
                    sale_data[company.id][day][3],  # duoc thu ho
                    sale_data[company.id][day][4],  # hoan tien
                    sale_data[company.id][day][5],  # chi ho
                    sale_data[company.id][day][6],  # duoc chi ho
                    '',  # DS k/h mua the
                    sale_data[company.id][day][0],  # doanh so erp
                    sale_data[company.id][day][7],  # so lieu c/s
                    sale_data[company.id][day][0] - sale_data[company.id][day][7],  # chenh lech
                    ''  # ghi chu
                ]
                for value, name in zip(values, fix_header):
                    if name[0] in ['Ngày', 'DS KH mua thẻ', 'Ghi chú']:
                        ws.write(row, col, value, normal)
                    else:
                        ws.write(row, col, value, normal_num)
                    col += 1
                col = 0
                row += 1

            # write footer
            ws.write(row, 0, "Tổng cộng", footer)
            for colx in range(1, 12):
                ws.write_formula(gcl(colx + 1) + str(row + 1), '=SUBTOTAL(9,' + gcl(colx + 1) + str(4) + ':' + gcl(colx + 1) + str(row) + ')', footer_num)

        wb.close()
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_chi_tiet_doanh_so_theo_ngay.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'báo cáo chi tiết doanh số theo ngày',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
