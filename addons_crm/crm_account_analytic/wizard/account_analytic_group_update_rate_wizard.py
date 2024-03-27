from odoo import api, fields, models, modules, tools, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from datetime import timedelta, date


class AccountAnalyticGroupUpdateRateWizard(models.TransientModel):
    _name = 'account.analytic.group.update.rate.wizard'
    _description = 'Cập nhật tỉ lệ phân bổ'

    start_date = fields.Date(string='Từ ngày',
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    data = fields.Binary('File', readonly=True)
    name = fields.Char('File Name', readonly=True)

    # start_datetime = fields.Datetime('Start datetime', compute='_compute_datetime')
    # end_datetime = fields.Datetime('End datetime', compute='_compute_datetime')

    def update_rate(self):
        self.ensure_one()
        children_ids = self.env['account.analytic.group'].browse(self._context.get("active_ids")).children_ids
        domain = [
            ('not_sale', '=', False),
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            ]
        if children_ids:
            sale_payment_ids = self.env['crm.sale.payment'].sudo().search(domain)
            # lấy tính tỉ lệ trong crm.sale.payment theo số công ty con.
            company_sale = []
            for company in children_ids:
                # nếu là SCI Group. => Tính các công ty con trong thương hiệu.
                if company.company_id.x_is_corporation is True:
                    list_company_ids = company.children_ids.mapped('company_id')
                    company_sale_payment_ids = sale_payment_ids.filtered(lambda x: x.company_id.id in list_company_ids.ids)
                else:
                    company_sale_payment_ids = sale_payment_ids.filtered(lambda x: x.company_id.id == company.company_id.id)

                company_amount = sum([pay.amount_proceeds for pay in company_sale_payment_ids])
                company_sale.append(company_amount)

            # Tính tỷ trọng các công ty trong list
            total_company_amount = sum(company_sale)
            total_company_rate_temp = 0
            if total_company_amount > 0:
                for index, num in enumerate(company_sale):
                    rate = (company_sale[index]/total_company_amount)*100
                    # đảm bảo tổng tỉ lệ các công ty luôn = 100
                    if total_company_rate_temp + rate >= 99.9:
                        company_sale[index] = 100 - total_company_rate_temp
                    else:
                        company_sale[index] = rate
                        total_company_rate_temp += rate
                # Cập nhật tỉ lệ
                for child, rate in zip(children_ids, company_sale):
                    child.update({
                        'percentage': rate,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'update_date': fields.Date.today()
                    })

        return True

