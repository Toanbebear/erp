from odoo import api, fields, models, modules, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import xlsxwriter
import io
import base64
from datetime import timedelta, date

REGION = [
    ('mb', 'Miền Bắc'),
    ('mt', 'Miền Trung'),
    ('mn', 'Miền Nam')
]


class OverDiscountSaleReport(models.TransientModel):
    _name = 'over.discount.sales.report'
    _description = 'Báo cáo doanh số giảm giá vượt trần khuyến mãi'

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
        domain = [('write_date', '>=', self.start_date), ('write_date', '<=', self.end_date)]
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
        if self.brand_id:
            brands = self.env['res.brand'].sudo().search([('id', '=', self.brand_id.id)])
        else:
            brands = self.env['res.brand'].sudo().search([('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
        if self.company_id:
            companies = self.env['res.company'].sudo().search([('id', '=', self.company_id.id)])
        else:
            companies = self.env['res.company'].sudo().search([('brand_id', 'in', brands.ids),
                                                               ('id', 'in', self.env.user.company_ids.ids)])
            if self.region:
                zone = self.region
                companies = companies.sudo().search([('zone', '=', zone)])
        for company in companies:
            ws = wb.add_worksheet(str(company.name).upper())
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
            title = 'BÁO CÁO DOANH SỐ VƯỢT TRẦN KHUYẾN MÃI TỪ ' + str(self.start_date.strftime("%d/%m/%Y")) + ' ĐẾN ' + str(self.end_date.strftime("%d/%m/%Y"))
            headers = ['Booking', 'Tên KH', 'Dịch vụ / sản phẩm', 'Giá gốc ( triệu)', 'Mức giảm giá',
                       'Mức trần quy định', 'Khuyến mại trên mức vượt trần', 'Khuyến mại dưới mức vượt trần',
                       'Quà tặng/voucher', 'Truyền thông/GĐCN duyệt giảm thêm', 'CP ROI', 'Ghi chú']
            ws.merge_range('C2:F2', title, normal_bold)
            row += 2
            ws.set_column('D:K', 15)
            ws.set_column('A:B', 14)
            ws.set_column('C:C', 25)
            for header in headers:
                ws.write(row, col, header, normal_bold_bolder)
                col += 1

            row += 1
            sale_payment = self.env['crm.sale.payment'].sudo().search([
                ('company_id', '=', company.id),
                ('not_sale', '=', False),
                ('payment_date', '>=', self.start_date),
                ('payment_date', '<=', self.end_date),
            ])
            for rec in sale_payment:
                if rec.service_id and abs(rec.amount_proceeds) >= rec.crm_line_id.total:
                    pass
                elif rec.product_id and rec.crm_line_product_id.total == 0:
                    pass
                elif rec.service_id and rec.amount_proceeds < rec.crm_line_id.total:
                    pay = rec.amount_proceeds
                    sale_payment_2 = self.env['crm.sale.payment'].sudo().search([
                        ('id', '!=', rec.id),
                        ('payment_date', '<=', self.end_date),
                        ('crm_line_id', '=', rec.crm_line_id.id),
                        ('payment_type', '=', rec.payment_type)
                    ])
                    for line in sale_payment_2:
                        pay += abs(line.amount_proceeds)
                    if pay >= rec.crm_line_id.total:
                        pass
                    else:
                        continue
                else:
                    continue

                if rec.product_id or rec.over_discount:
                    if rec.service_id:
                        price = rec.crm_line_id.total_before_discount
                        money_discount = price - rec.crm_line_id.total
                        special_discount = (rec.crm_line_id.discount_review_id.discount / 100) * price
                        gift_or_voucher = 0
                        today = datetime.today()
                        ceiling_discount_id = rec.service_id.ceiling_discount_ids.sudo().search([
                            ('brand_id', '=', company.brand_id.id),
                            ('begin_date', '<=', today),
                            ('end_date', '>=', today)
                        ], limit=1)
                        promotional_ceiling = ceiling_discount_id.ceiling_discount or 0
                        # promotional_ceiling = float(rec.service_id.promotional_ceiling) or 0
                        ceiling = promotional_ceiling/100 * price
                        if money_discount > ceiling:
                            above_ceiling = money_discount - ceiling
                            below_ceiling = 0
                        elif money_discount < ceiling:
                            above_ceiling = 0
                            below_ceiling = ceiling - money_discount
                        else:
                            continue
                    elif rec.product_id:
                        price = rec.crm_line_product_id.total_before_discount
                        # money_discount = price - rec.crm_line_product_id.total
                        money_discount = 0
                        special_discount = (rec.crm_line_product_id.crm_discount_review.discount / 100) * price
                        gift_or_voucher = price
                        ceiling = 0
                        above_ceiling = 0
                        below_ceiling = 0
                    else:
                        continue
                    col = 0
                    # Booking
                    ws.write(row, col, rec.booking_id.name, normal_bolder)
                    col += 1
                    # Ten KH
                    ws.write(row, col, rec.partner_id.name, normal_bolder)
                    col += 1
                    # Dich vu/san pham
                    ws.write(row, col, rec.product_id.name or rec.service_id.name or "", normal_bolder)
                    col += 1
                    # Gia goc
                    ws.write(row, col, price, normal_bolder)
                    col += 1
                    # Muc giam gia
                    ws.write(row, col, money_discount, normal_bolder)
                    col += 1
                    # Muc tran quy dinh
                    ws.write(row, col, ceiling, normal_bolder)
                    col += 1
                    # Khuyen mai tren muc tran
                    config = self.env['res.company'].sudo().search([('id', '=', company.id)], limit=1)
                    roi_rate = config.roi_rate
                    if rec.payment_type == 'inbound':
                        above_ceiling = abs(above_ceiling)
                        below_ceiling = abs(below_ceiling)
                        roi = abs((money_discount - ceiling + gift_or_voucher)*(roi_rate/100))
                    elif rec.payment_type == 'outbound':
                        above_ceiling = -abs(above_ceiling)
                        below_ceiling = -abs(below_ceiling)
                        roi = -abs((money_discount - ceiling + gift_or_voucher)*(roi_rate/100))
                    else:
                        continue

                    ws.write(row, col, above_ceiling, normal_bolder)
                    col += 1
                    # Khuyen mai duoi muc tran
                    ws.write(row, col, below_ceiling, normal_bolder)
                    col += 1
                    # Qua tang/voucher
                    ws.write(row, col, gift_or_voucher, normal_bolder)
                    col += 1
                    # Truyen thong/GDCN duyet giam them
                    ws.write(row, col, special_discount, normal_bolder)
                    col += 1
                    # ROI
                    ws.write(row, col, roi, normal_bolder)
                    col += 1
                    # Ghi chu
                    ws.write(row, col, "", normal_bolder)
                    row += 1
        wb.close()

        # fp = BytesIO()
        # wb.save(fp)
        # fp.seek(0)
        report = base64.encodebytes((fp.getvalue()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'bao_cao_doanh_so_vuot_tran_khuyen_mai.xlsx',
            'datas': report,
            'res_model': 'temp.creation',
            'public': True,
        })
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % attachment.id
        return {'name': 'BÁO CÁO DOANH SỐ VƯỢT TRẦN KHUYẾN MÃI',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }




