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
from collections import OrderedDict

SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'), ('ChiPhi', 'Chi phí khác')]
dict_type = dict((key, value) for key, value in SERVICE_HIS_TYPE)


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
    return row_current, col_current


def write_roman(num):
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


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


class CRMSalePaymentServiceReport(models.TransientModel):
    _name = 'crm.sale.payment.service.report'
    _description = 'Báo các doanh số theo dịch vụ'

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

    def get_name_in_selection(self, object, field_name, value, language_code='vi_VN'):
        selection_list = self.env[object].with_context(lang=language_code).fields_get(allfields=[field_name])[field_name][
            'selection']
        return dict(selection_list).get(value, '')

    def _get_data(self, company_list):
        # Get all data init
        data = {}
        domain = [
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            ('company_id.id', 'in', company_list.ids),
            ('amount_proceeds', '!=', 0),
            ('service_id', '!=', False),
            ('not_sale', '=', False),
        ]
        pays = self.env['crm.sale.payment'].sudo().search(domain, order="id")
        for company in company_list:
            brand = company.brand_id.name
            if data.get(brand, 0) is 0:
                data[brand] = {}

            # Lấy các dịch vụ của công ty hiện tại
            services_in_company = self.env['sh.medical.health.center.service'].sudo().search(
                [('institution.name', '=', company.name)], order="id")
            # Lấy các dịch vụ của công ty thu hộ
            services_in_other_company = set(pays.filtered(lambda x: x.company_id.id == company.id).mapped('service_id'))
            for service in services_in_other_company:
                if services_in_company and service not in services_in_company:
                    services_in_company += service
            pays_in_company = pays.filtered(lambda x: x.company_id.id == company.id)
            pays -= pays_in_company
            service_types = set(services_in_company.mapped('his_service_type'))
            for type in service_types:
                services_in_type = services_in_company.filtered(lambda x: x.his_service_type == type)
                service_categorys = set(services_in_type.mapped('service_category'))
                services_in_company -= services_in_type
                pays_in_type = pays_in_company.filtered(lambda x: x.service_id.his_service_type == type)
                pays_in_company -= pays_in_type
                if data[brand].get(type, 0) == 0:
                    data[brand][type] = {}

                non_category = 'KHÔNG XÁC ĐỊNH NHÓM'
                if data[brand][type].get(non_category, 0) == 0:
                    data[brand][type][non_category] = {}
                pays_not_category = pays_in_type.filtered(lambda x: x.service_id.service_category.id is False)
                total = sum(pays_not_category.mapped('amount_proceeds'))
                if data[brand][type][non_category].get(company.name, 0) == 0:
                    data[brand][type][non_category][company.name] = total
                else:
                    data[brand][type][non_category][company.name] += total
                pays_in_type -= pays_not_category
                for categ in service_categorys:
                    categ_name = '[' + (categ.code or '') + '] ' + (categ.name or '')
                    if data[brand][type].get(categ_name, 0) == 0:
                        data[brand][type][categ_name] = {}

                    pays_in_category = pays_in_type.filtered(
                        lambda x: x.service_id.service_category.id == categ.id)
                    pays_in_type -= pays_in_category
                    total_in_category = sum(pays_in_category.mapped('amount_proceeds'))
                    if data[brand][type][categ_name].get(company.name, 0) == 0:
                        data[brand][type][categ_name][company.name] = total_in_category
                    else:
                        data[brand][type][categ_name][company.name] += total_in_category

        return data

    def _get_data_product(self, company_list):
        # Get all data init
        data = {}
        domain = [
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            ('company_id.id', 'in', company_list.ids),
            ('amount_proceeds', '!=', 0),
            ('product_id', '!=', False),
            ('not_sale', '=', False),
        ]
        pays = self.env['crm.sale.payment'].sudo().search(domain, order="id")

        for company in company_list:
            brand = company.brand_id.name
            if data.get(brand, 0) is 0:
                data[brand] = {}

            # duyệt các thanh toán sản phẩm của công ty
            for product in pays.filtered(lambda x: x.company_id.id == company.id):
                department = product.department or 'Không xác định'
                if data[brand].get(department, 0) == 0:
                    data[brand][department] = {}
                if data[brand][department].get(product.product_id.name, 0) == 0:
                    data[brand][department][product.product_id.name] = {}
                if data[brand][department][product.product_id.name].get(company.name, 0) == 0:
                    data[brand][department][product.product_id.name][company.name] = product.amount_proceeds
                else:
                    data[brand][department][product.product_id.name][company.name] += product.amount_proceeds

        return data

    # Tao bao cao
    def create_report(self):
        # in dữ liễu
        fp = io.BytesIO()
        wb = xlsxwriter.Workbook(fp)
        # format
        title_big = build_format(wb, [('font_size', 13)], 'header')
        normal_num = build_format(wb, [('num_format', '###,###,###,###'), ('align', 'right')])
        header = build_format(wb, [], 'header')
        normal = build_format(wb, [])
        header_yellow_bg = build_format(wb, [('bg_color', '#FFFF00'), ('num_format', '###,###,###,###')], 'header')
        header_dark_green_bg = build_format(wb, [('bg_color', '#92D050')], 'header')
        # add icon

        brand_domain = [('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)]
        company_domain = [('zone', '!=', False), ('id', 'in', self.env.user.company_ids.ids)]
        if self.brand_id:
            brand_domain.append(('id', '=', self.brand_id.id))
            company_domain.append(('brand_id.id', '=', self.brand_id.id))
        if self.region:
            company_domain.append(('zone', '=', self.region))
        if self.company_id:
            company_domain.append(('id', '=', self.company_id.id))

        company_list = self.env['res.company'].sudo().search(company_domain)
        brand_list = self.env['res.brand'].sudo().search(brand_domain)

        sale_data = self._get_data(company_list)
        sale_data_product = self._get_data_product(company_list)
        for brand in brand_list:
            ws = wb.add_worksheet(brand.name)

            # IN DỊCH VỤ

            # write header
            row = 1
            col = 0
            ws.set_row(1, 30)
            company_in_brand = company_list.filtered(lambda x: x.brand_id.id == brand.id)
            fix_header = [('STT', 0, 0, 0, 10), ('Loại dịch vụ', 0, 0, 0, 20), ('Tên nhóm dịch vụ', 0, 0, 0, 50)]
            fix_header.extend([(company.name, 0, 0, 0, 40) for company in company_in_brand])
            ws.merge_range('A1:' + gcl(len(fix_header)) + str(1) + '',
                           "BÁO CÁO DOANH SỐ %s THEO DỊCH VỤ TỪ NGÀY %s ĐẾN NGÀY %s"
                           % (brand.name.upper() if brand.name else '', self.start_date.strftime('%Y-%m-%d'),
                              self.end_date.strftime('%Y-%m-%d')), title_big)
            for data in fix_header:
                row, col = write_cell(ws, data[0], row, col, data[1], data[2], data[3], header_dark_green_bg)
                col += 1

            # write data
            row += 1
            categ_idx = 1
            for service_type_idx, service_type in enumerate(sale_data.get(brand.name, []), start=1):
                col = 1
                ws.write(row, 0, write_roman(service_type_idx), normal_num)
                service_type_name = self.get_name_in_selection('crm.sale.payment', 'department', service_type, self.env.user.lang)
                write_cell(ws, service_type_name or 'Không xác định loại', row, col, 0, 0, 0, header)

                col += 1
                ws.write(row, col, service_type_name or 'Không xác định loại', header_yellow_bg)

                category_list = sale_data[brand.name].get(service_type, [])
                for x in range(2, len(company_in_brand) + 2):
                    # ws.write(row, col + x, '', header_yellow_bg)
                    # write total of category

                    ws.write_formula(gcl(col + x) + str(row + 1),
                                     '=SUBTOTAL(9,%s%s:%s%s)' % (gcl(col + x), str(row + 2), gcl(col + x), str(row + len(category_list) + 1)), header_yellow_bg)

                row += 1
                # list category
                for categ in category_list:
                    ws.write(row, 0, categ_idx, normal)
                    categ_idx += 1
                    ws.write(row, col, categ, normal)
                    for company in company_in_brand:
                        col += 1
                        ws.write(row, col, sale_data[brand.name][service_type][categ].get(company.name, 0), normal_num)
                    row += 1
                    col = 2

            # set width column
            col = 0
            # row += 1
            for data in fix_header:
                ws.set_column(row, col, data[4] if len(data) == 5 else 20)
                col += 1

            # write footer
            if row > 4: # only write in the case has the data
                write_cell(ws, "TỔNG CỘNG", row, 1, 0, 1, 0, normal)
                for colx in range(2, len(fix_header)):
                    ws.write_formula(gcl(colx + 1) + str(row + 1),
                                     '=SUBTOTAL(9,%s%s:%s%s)' % (gcl(colx + 1), 3, gcl(colx + 1), str(row)), normal_num)

            # IN SẢN PHẨM
            row += 3
            col = 0
            fix_header = [('STT', 0, 0, 0, 10), ('Phòng ban bán sản phầm', 0, 0, 0, 20), ('Tên sản phẩm', 0, 0, 0, 50)]
            fix_header.extend([(company.name, 0, 0, 0, 40) for company in company_in_brand])
            for data in fix_header:
                row, col = write_cell(ws, data[0], row, col, data[1], data[2], data[3], header_dark_green_bg)
                col += 1

            # write data
            row += 1
            product_row = row
            index = 1
            index_pro = 1
            product_dept = sale_data_product.get(brand.name, [])
            for dept in product_dept:
                product_list = product_dept.get(dept, [])
                col = 0
                ws.write(row, col, write_roman(index), normal)
                col += 1
                department = self.get_name_in_selection('crm.sale.payment', 'department', dept, self.env.user.lang)
                ws.write(row, col, department or 'Không xác định', header_yellow_bg)
                col += 1
                ws.write(row, col, '', header_yellow_bg)
                for x in range(2, len(company_in_brand) + 2):
                    ws.write_formula(gcl(col + x) + str(row + 1),
                                     '=SUBTOTAL(9,%s%s:%s%s)' % (gcl(col + x), str(row + 2), gcl(col + x), str(row + len(product_list) + 1)), header_yellow_bg)

                if product_list:
                    for product in product_list:
                        row += 1
                        col = 0
                        ws.write(row, col, index_pro, normal_num)
                        col += 1
                        ws.write(row, col, '', normal_num)
                        col += 1
                        ws.write(row, col, product, normal)
                        for company in company_in_brand:
                            col += 1
                            ws.write(row, col, sale_data_product[brand.name][dept][product].get(company.name, 0), normal_num)
                        index_pro += 1
                    row += 1
                else:
                    # for col in range(0, len(company_in_brand) + 2):
                    #     ws.write(row, col, "", normal_num)
                    row += 1
                index += 1

            # write footer
            write_cell(ws, "TỔNG CỘNG", row, 1, 0, 1, 0, normal)
            for colx in range(2, len(fix_header)):
                ws.write_formula(gcl(colx + 1) + str(row + 1),
                                 '=SUBTOTAL(9,%s%s:%s%s)' % (gcl(colx + 1), product_row + 1, gcl(colx + 1), str(row)), normal_num)

        wb.close()
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_chi_tiet_doanh_so_theo_dich_vu.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO CHI TIẾT DOANH SỐ THEO DỊCH VỤ',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
