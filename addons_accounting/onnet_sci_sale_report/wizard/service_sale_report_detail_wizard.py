from odoo import api, fields, models
import pandas as pd
import io
from io import BytesIO
from odoo.tools.misc import xlsxwriter
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import base64



class ServiceSaleReport(models.TransientModel):
    _name = 'service.sale.report'
    _description = 'Báo cáo doanh thu thực hiện dịch vụ'

    date_from = fields.Date(string='Từ ngày',
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    company_id = fields.Many2one('res.company', 'Chi nhánh', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])

    # def get_data(self):
    #     query = f"""
    #         select a.date,crm,a.code_customer,partner,walkin,specialty,a.service_id,a.order_id,a.product_uom_qty,a.product_uom,a.surgery_date,a.surgery_end_date,a.price_subtotal,a.service_room,a.company_id
    #         from sale_report as a
    #         left join
    #             (select name from crm_lead) as crm on (a.booking_id = crm.id)
    #         left join
    #             (select name from res_partner) as partner on (a.partner_id = partner.id)
    #         left join
    #             (select name from sh_medical_appointment_register_walkin) as  walkin on (a.walkin_id = walkin.id)
    #         left join
    #             (select name from sh_medical_specialty) as specialty on (a.specialty_id = specialty.id)
    #         left join
    #             (select * from sh_medical_health_center_service) as service on (a.service_id = service.id)
    #         where a.company_id = {self.company_id.id}
    #         and a.date <= '{self.date_to.strftime('%d/%m/%Y')}'
    #         and a.date >= '{self.date_from.strftime('%d/%m/%Y')}'
    #     """
    #     self.env.cr.execute(query)
    #     data = self.env.cr.dictfetchall()
    #     return data

    def get_data(self):
        # Get all data init
        # get all asset in have created before data to and write lasted after date from
        domain = [
            ('date', '<=', self.date_to),
            ('date', '>=', self.date_from),
            ('company_id.id', '=', self.company_id.id),
            ('state', 'in', ['sale', 'done']),
            ('service_id.name', '!=', '')
        ]
        sale_report = self.env['sale.report'].sudo().search(
            domain, order="date desc")

        return sale_report

    def action_export(self):
        # in memory byte
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        columns = [
            'Ngày',
            'Mã Booking',
            'Mã Khách hàng',
            'Tên khách hàng',
            'Mã phiếu khám',
            'Mã phiếu chuyên khoa',
            'Dịch vụ',
            'Đơn hàng',
            'Số lượng',
            'Đơn vị xử lý',
            'Ngày giờ bắt đầu',
            'Ngày giờ kết thúc',
            'Doanh thu thực hiện dịch vụ đã làm',
            'Phòng thực hiện',
            'Đơn vị',
        ]
        sale_report_data = self.get_data()
        # writer data
        data_rows = []
        for data in sale_report_data:
            surgery_date_str = (
                data.surgery_date.strftime('%d/%m/%Y') if isinstance(data.surgery_date, datetime) else None
            )
            surgery_end_date_str = (
                data.surgery_end_date.strftime('%d/%m/%Y') if isinstance(data.surgery_end_date, datetime) else None
            )
            service_date_str = (
                data.services_date.strftime('%d/%m/%Y') if isinstance(data.services_date, datetime) else None
            )
            service_end_date_str = (
                data.services_end_date.strftime('%d/%m/%Y') if isinstance(data.services_end_date, datetime) else None
            )
            row = [
                data.date.strftime('%d/%m/%Y') if isinstance(data.date, datetime) else '-',
                data.booking_id.name or '-',
                data.code_customer or '-',
                data.partner_id.name or '-',
                data.walkin_id.name or '-',
                data.specialty_id.name or '-',
                data.service_id.name or '-',
                data.order_id.name or '-',
                data.product_uom_qty or '-',
                data.product_uom.name or '-',
                surgery_date_str or service_date_str or '-',
                surgery_end_date_str or service_end_date_str or '-',
                data.price_subtotal or '-',
                data.service_room.name or '-',
                data.company_id.name or '-',
            ]
            data_rows.append(row)
        if len(data_rows) == 0:
            data_rows = [[' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']]

        df = pd.DataFrame(data_rows, columns=columns)
        # header
        header_1 = f"BÁO CÁO DOANH THU THỰC HIỆN DỊCH VỤ"
        header_2 = f"Từ ngày {self.date_from.strftime('%d/%m/%Y')} đến ngày {self.date_to.strftime('%d/%m/%Y')}"
        header_3 = f"Chi nhánh: {self.company_id.name}"
        #
        df.to_excel(writer, sheet_name=self.company_id.code or ' ', index=False, columns=None, startrow=4)

        # Get the XlsxWriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[self.company_id.code or ' ']

        # Apply a format to add a border to the cells
        price_format = workbook.add_format([('num_format', '#,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @'), ('align', 'right')])
        title_format = workbook.add_format({'font_name': 'Arial', 'border': 0, 'bold': 1, 'font_size': 19})
        subtitle_format = workbook.add_format({'font_name': 'Arial', 'border': 0, 'bold': 0})
        header_format = workbook.add_format({'font_name': 'Arial', 'border': 0, 'bold': 1, 'bg_color': '#C2CFF8'})
        border_fmt = workbook.add_format({'font_name': 'Arial', 'border': 1, 'bold': 0})
        left_alignment_format = workbook.add_format({'font_name': 'Arial', 'align': 'left'})

        # Format title report
        worksheet.conditional_format('E1:J1', {'type': 'no_blanks', 'format': title_format})
        # Format subtitle report
        worksheet.conditional_format('G2:I2', {'type': 'no_blanks', 'format': subtitle_format})
        # Format headers
        worksheet.conditional_format('A5:S5', {'type': 'no_blanks', 'format': header_format})
        # Format dataframe
        worksheet.conditional_format('A6:S' + str(6 + len(data_rows)), {'type': 'no_blanks', 'format': border_fmt})
        # Format currency value
        worksheet.set_column('M:M', 35, cell_format=price_format)
        worksheet.set_default_row(40)

        for col_idx, column in enumerate(df.columns[:12]):
            worksheet.set_column(col_idx, col_idx, 25, cell_format=left_alignment_format)
        for col_idx in range(13, 15):
            worksheet.set_column(col_idx, col_idx, 50, cell_format=left_alignment_format)

        worksheet.merge_range('E1:J1', header_1, title_format)
        worksheet.merge_range('F2:I2', header_2, subtitle_format)
        worksheet.merge_range('F3:H3', header_3, subtitle_format)
        # for column in df:
        #     column_length = max(df[column].astype(str).map(len).max(), len(column))
        #     col_idx = df.columns.get_loc(column)
        #     worksheet.set_column(col_idx, col_idx, column_length)

        writer.save()
        writer.close()
        report = base64.encodebytes((output.getvalue()))
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_doanh_thu_thuc_hien_dich_vu.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO DOANH THU THỰC HIỆN DỊCH VỤ',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
