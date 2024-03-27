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


class CRMSalePaymentDetailReport(models.TransientModel):
    _name = 'crm.sale.payment.detail.report.da'
    _description = 'Báo các chi tiết doanh số'

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
        # Get all data init
        domain = [
            ('account_payment_id.payment_date', '>=', self.start_date),
            ('account_payment_id.payment_date', '<=', self.end_date),
            ('company_id.id', 'in', company_list.ids),
            ('amount_proceeds', '!=', 0),
            ('account_payment_id.internal_payment_type', '!=', 'chi_ho'),
            ('not_sale', '=', False),
        ]
        pays = self.env['crm.sale.payment'].sudo().search(domain, order="id")

        return pays

    def get_name_in_selection(self, object, field_name, value, language_code='vi_VN'):
        selection_list = self.env[object].with_context(lang=language_code).fields_get(allfields=[field_name])[field_name][
            'selection']
        return dict(selection_list).get(value, '')

    # Tao bao cao
    def create_report(self):
        # in dữ liễu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        # format
        title_big = build_format(wb, [('font_size', 13), ('border', False)], 'header')
        normal_num = build_format(wb, [('num_format', '###,###,###,###'), ('align', 'right')])
        normal = build_format(wb, [])
        header_yellow_bg = build_format(wb, [('bg_color', '#FFFF00')], 'header')
        header_number_yellow_bg = build_format(wb, [('bg_color', '#FFFF00'), ('num_format', '###,###,###,###')], 'header')
        header_dark_green_bg = build_format(wb, [('bg_color', '#92D050')], 'header')

        ws = wb.add_worksheet("BÁO CÁO CHI TIẾT DOANH SỐ")
        # add icon


        # build header
            # header[name,0,0,0]
            # header[1]: row_diff - xuống dòng
            # header[2]: col_add -  merge hàng
            # header[3]: row_add -  merge cột
        fix_header = [
            ('STT', 0, 0, 0, 10),
            ('Số phiếu thu', 0, 0, 0),
            ('Ngày', 0, 0, 0),
            ('Loại phiếu', 0, 0, 0, 15),
            ('Nội dung', 0, 0, 0, 30),
            ('Nhóm dịch vụ', 0, 0, 0, 30),
            ('Tên dịch vụ/SP', 0, 0, 0, 30),
            ('Mã KH', 0, 0, 0, 15),
            ('Tên KH', 0, 0, 0, 20),
            ('Địa chỉ', 0, 0, 0),
            ('Mã Boking', 0, 0, 0),
            ('Số tiền Booking', 0, 0, 0, 12),
            ('Số tiền giảm giá/ chiết khấu', 0, 0, 0, 12),
            ('Số tiền sau giảm giá', 0, 0, 0, 12),
            # ('Số tiền thu (nguyên tệ)', 0, 0, 0, 12),
            ('Số tiền thu (VND)', 0, 0, 0, 12),
            ('Số tiền đã nộp trước', 0, 0, 0, 12),
            ('Số tiền chưa sử dụng', 0, 0, 0, 12),
            ('Nhóm nguồn', 0, 0, 0, 15),
            ('Thương hiệu', 0, 0, 0),
            ('Chi nhánh', 0, 0, 0, 30),
            ('Phòng/Ban người tạo', 0, 0, 0),
            ('Nguồn giới thiệu', 0, 0, 0),
            ('Người tạo booking', 0, 0, 0),
            ('Nguồn ban đầu', 0, 0, 0),
        ]

        # write header
        row = 4
        col = 0
        ws.merge_range('A4:G4', "BÁO CÁO DOANH SỐ TỪ NGÀY %s ĐẾN NGÀY %s" %(self.start_date.strftime('%d/%m/%Y'), self.end_date.strftime('%d/%m/%Y')), title_big)
        ws.write(0, 0, 'Tên đơn vị:')
        ws.write(1, 0, 'Địa chỉ:')
        ws.set_row(3, 30)
        ws.set_row(4, 30)
        for data in fix_header:
            ws.set_column(row, col, data[4] if len(data) == 5 else 18)
            row, col = write_cell(ws, data[0], row, col, data[1], data[2], data[3], header_dark_green_bg)
            col += 1

        # write data
        company_domain = [('id', 'in', self.env.user.company_ids.ids)]
        if self.brand_id:
            company_domain.append(('brand_id.id', '=', self.brand_id.id))
        if self.region:
            company_domain.append(('zone', '=', self.region))
        if self.company_id:
            company_domain.append(('id', '=', self.company_id.id))
        company_list = self.env['res.company'].sudo().search(company_domain)

        # Phan loai sản phẩm
        dict_satisfaction_type = {
            'consu': 'Tiêu dùng',
            'service': 'Dịch vụ',
            'product': 'Sản phẩm lưu kho',
        }

        row += 1
        col = 0
        sale_data = self._get_data(company_list)
        for idx, data in enumerate(sale_data, start=1):
            # check get payment detail service or product
            # data_payment_detail = data.account_payment_detail_id if data.service_id else data.account_payment_product_detail_id
            # data_line_detail = data.crm_line_id if data.service_id else data.crm_line_product_id

            # Dịch vụ
            if data.account_payment_detail_id:
                data_payment_detail = data.account_payment_detail_id
                data_line_detail = data.crm_line_id
                service_type = data.account_payment_detail_id.crm_line_id.service_id.his_service_type
                department_product = self.get_name_in_selection('sh.medical.health.center.service', 'his_service_type', service_type, self.env.user.lang) if service_type else ''
            # Sản phẩm
            else:
                data_payment_detail = data.account_payment_product_detail_id
                data_line_detail = data.crm_line_product_id
                department_product = data.account_payment_product_detail_id.department_product if data.account_payment_product_detail_id.department_product else ''

            values = [
                idx,
                data.account_payment_id.name if data.account_payment_id.name else '',  # số phiếu thu
                data.account_payment_id.payment_date.strftime('%d/%m/%Y') if data.account_payment_id.payment_date else '',  # ngày
                self.get_name_in_selection('account.payment', 'payment_type', data.payment_type, self.env.user.lang) if data.payment_type else '',  # loai phieu
                data.account_payment_id.communication if data.account_payment_id.communication else '',  # noi dung
                data.service_id.service_category.name or dict_satisfaction_type[
                    '%s' % data.product_id.type] if data.service_id.service_category.name or data.product_id.type else '',
                # data.service_id.service_category or data.product_id.default_code,# Nhóm dịch vụ
                data.service_id.name or data.product_id.name,
                data.partner_id.code_customer if data.partner_id.type else '',  # ma khach hang
                data.partner_id.name if data.partner_id.name else '',  # ten khach hang
                data.partner_id.state_id.name if data.partner_id.state_id.name else '',  # dia chi
                data.booking_id.name if data.booking_id.name else '',  # ma booking
                data_line_detail.unit_price if data.service_id else data_line_detail.price_unit,  # so tien booking
                data_line_detail.total_before_discount - data_line_detail.total if data_line_detail.total else '',  # so tien giảm giá chiết khấu
                data_line_detail.total if data_line_detail.total else '',  # so tien sau giam
                # '',  # so tien thu nguyen te($)
                data.amount_proceeds,  # so tien thu vnd
                data_payment_detail.total_received if data_payment_detail.total_received else '',
                data_line_detail.total - data.amount_proceeds - (data_payment_detail.total_received if data_payment_detail.total_received else 0),
                data.booking_id.category_source_id.name if data.booking_id.category_source_id.name else '',  # nhóm nguồn
                data.company_id.brand_id.name if data.account_payment_id.brand_id.name else '',  # thuong hieu
                data.company_id.name if data.company_id.name else '',  # chi nhanh
                self.env['hr.employee'].sudo().search([('user_id', '=', data.booking_id.create_by.id)], limit=1).department_id.name or None,  # phong/bo phan
                data.booking_id.source_id.name if data.booking_id.source_id.name else '',  # nguon gioi thieu
                data.booking_id.create_by.name if data.booking_id.create_by.name else '',  # nguoi tạo booking
                data.booking_id.original_source_id.name if data.booking_id.original_source_id.name else '', #nguồn ban đầu
            ]
            for value, name in zip(values, fix_header):
                # format number col
                if name[0] in ['Số tiền Booking', 'Số tiền thu (nguyên tệ)', 'Số tiền thu (VND)', 'Số tiền đã nộp trước', 'Số tiền chưa sử dụng', 'Số tiền sau giảm giá', 'Số tiền giảm giá/ chiết khấu']:
                    ws.write(row, col, value, normal_num)
                else:
                    ws.write(row, col, value, normal)
                col += 1
            col = 0
            row += 1

        # write footer
        ws.write(row, 0, "Tổng cộng", header_yellow_bg)
        for colx in range(1, 21):
            ws.write_formula(gcl(colx + 1) + str(row + 1),'=SUBTOTAL(9,' + gcl(colx + 1) + str(6) + ':' + gcl(colx + 1) + str(row) + ')',
                             header_number_yellow_bg)

        # set width column
        for data in fix_header:
            ws.set_column(row, col, data[4] if len(data) == 5 else 18)
            col += 1

        wb.close()
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_chi_tiet_doanh_so.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO CHI TIẾT DOANH SỐ',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
