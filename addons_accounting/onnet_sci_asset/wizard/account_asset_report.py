from odoo import api, fields, models
import pandas as pd
import io
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import base64



class AccountAssetReport(models.TransientModel):
    _name = 'account.asset.report'
    _description = 'Báo cáo tài sản cố định'

    date_from = fields.Date(string='Từ ngày',
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    company_ids = fields.Many2many(string='Chi nhánh',
                                   comodel_name='res.company',
                                   domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    asset_type = fields.Selection([('sale', 'Doanh thu trả trước'), ('purchase', 'Tài sản cố định'), ('expense', 'Chi phí trả trước')])

    def _get_data(self, company_list):
        # Get all data init
        # get all asset in have created before data to and write lasted after date from
        domain = [
            ('first_depreciation_date', '<=', self.date_to),
            ('write_date', '>=', self.date_from),
            ('company_id.id', 'in', company_list.ids),
            ('asset_type', '=', self.asset_type),
            ('state', '=', 'open')
        ]
        assets = self.env['account.asset'].sudo().search(
            domain, order="create_date")

        return assets

    def action_export(self):
        # in memory byte
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        columns = ['Mã TSCĐ', 'Tên TSCĐ', 'Số lượng ghi tăng', 'Loại TSCĐ', 'Đơn vị sử dụng', 'TK phân tích', 'Ngày ghi tăng', 'Số CT ghi tăng', 'Ngày bắt đầu tính KH',
                   'Thời gian sử dụng (Tháng)', 'Kỳ tính KH(Tháng)', 'Thời gian SD còn lại(Tháng)', ' Nguyên giá    ', 'Giá trị tính KH', 'Hao mòn trong kỳ',
                   'Hao mòn lũy kế', 'Giá trị còn lại', 'Giá trị KH tháng', 'TK nguyên giá', 'TK khấu hao', 'TK chi phí']

        # get filter data by domain
        company_domain = [('id', 'in', self.env.user.company_ids.ids)]
        if self.company_ids:
            company_domain.append(('id', 'in', self.company_ids.ids))
        company_list = self.env['res.company'].sudo().search(company_domain)
        for com in company_list:
            account_asset_data = self._get_data(com)

            # writer data
            data_rows = []
            for data in account_asset_data:
                move_ids = data.depreciation_move_ids.filtered(lambda x:
                                                               self.date_from <= x.date <= self.date_to
                                                               and x.state == 'posted')
                if move_ids:
                    depreciation_in_term = sum(move_ids.mapped('amount_total'))
                    depreciation_per_period = data.depreciation_move_ids[0].amount_total or 0
                    time_remaining = len(data.depreciation_move_ids.filtered(lambda x: x.date > self.date_to)) * int(data.method_period)
                    asset_depreciated_value = move_ids[0].asset_depreciated_value or 0
                    value_residual = move_ids[0].asset_remaining_value
                else:
                    time_remaining = 0
                    depreciation_in_term = 0
                    depreciation_per_period = 0
                    asset_depreciated_value = 0
                    value_residual = 0
                row = [data.x_code or '-',  # Mã TSCĐ
                       data.name,  # Tên TSCĐ
                       data.x_qty,  # Số lượng ghi tăng
                       data.asset_model_id.name or '-',  # Loại TSCĐ
                       data.company_id.name or '-',  # Đơn vị sử dụng
                       data.account_analytic_id.name or '-',  # TK phan tic
                       data.x_date_invoice or '-',  # Ngày ghi tăng
                       data.x_info_invoice or '-',  # Số CT ghi tăng
                       data.first_depreciation_date.strftime('%d/%m/%Y') or '-',  # Ngày bắt đầu tính KH
                       int(data.method_number) * int(data.method_period),  # Thời gian SD
                       data.method_period,  # Kỳ tính KH
                       time_remaining,  # Thời gian SD còn lại
                       data.original_value,  # Nguyên giá
                       data.original_value - data.salvage_value,  # Giá trị tính KH
                       depreciation_in_term,  # Hao mòn trong kỳ
                       asset_depreciated_value,  # Hao mòn lũy kế
                       value_residual,  # Giá trị còn lại
                       depreciation_per_period,  # Giá trị KH tháng
                       data.account_asset_id.display_name or '-',  # TK nguyên giá
                       data.account_depreciation_id.display_name or '-',  # TK khấu hao
                       data.account_depreciation_expense_id.display_name or '-',  # TK chi phí
                       ]
                data_rows.append(row)
            if len(data_rows) == 0:
                data_rows = [[' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']]

            df = pd.DataFrame(data_rows, columns=columns)
            # header
            header_1 = f"BÁO CÁO TÀI SẢN CỐ ĐỊNH {com.name}"
            header_2 = f"Từ ngày {self.date_from.strftime('%d/%m/%Y')} đến ngày {self.date_to.strftime('%d/%m/%Y')}"
            #
            df.to_excel(writer, sheet_name=com.code or ' ', index=False, columns=None, startrow=4)

            # Get the XlsxWriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets[com.code or ' ']

            # Apply a format to add a border to the cells
            price_format = workbook.add_format([('num_format', '#,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @'), ('align', 'right')])
            title_format = workbook.add_format({'border': 0, 'bold': 1, 'font_size': 19})
            subtitle_format = workbook.add_format({'border': 0, 'bold': 0})
            header_format = workbook.add_format({'border': 0, 'bold': 1, 'bg_color': '#C2CFF8'})
            border_fmt = workbook.add_format({'border': 1, 'bold': 0})

            # Format title report
            worksheet.conditional_format('E1:J1', {'type': 'no_blanks', 'format': title_format})
            # Format subtitle report
            worksheet.conditional_format('G2:I2', {'type': 'no_blanks', 'format': subtitle_format})
            # Format headers
            worksheet.conditional_format('A5:U5', {'type': 'no_blanks', 'format': header_format})
            # Format dataframe
            worksheet.conditional_format('A6:U' + str(6 + len(data_rows)), {'type': 'no_blanks', 'format': border_fmt})
            # Format currency value
            worksheet.set_column(10, 15, cell_format=price_format)
            # worksheet.write('E1', header_1)
            worksheet.merge_range('E1:J1', header_1, title_format)
            worksheet.merge_range('F2:I2', header_2, subtitle_format)
            for column in df:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_length)

        writer.save()
        writer.close()
        report = base64.encodebytes((output.getvalue()))
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_tai_san_co_dinh.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO TÀI SẢN CỐ ĐỊNH',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
