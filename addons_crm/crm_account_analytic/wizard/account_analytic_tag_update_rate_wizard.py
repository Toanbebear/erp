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

SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'), ('ChiPhi', 'Chi phí khác')]
dict_type = dict((key, value) for key, value in SERVICE_HIS_TYPE)


class AccountAnalyticTagUpdateRateWizard(models.TransientModel):
    _name = 'account.analytic.tag.update.rate.wizard'
    _description = 'Cập nhật tỉ lệ phân bổ'

    start_date = fields.Date(string='Từ ngày',
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string='Đến ngày', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    data = fields.Binary('File', readonly=True)
    name = fields.Char('File Name', readonly=True)

    def update_rate(self):
        self.ensure_one()
        tag_department_id = self.env['account.analytic.tag'].browse(self._context.get("active_ids"))
        if tag_department_id and tag_department_id.company_id:
            # Nếu chưa phân bổ thì khởi tạo line phân tích
            if not tag_department_id.analytic_distribution_ids:
                tag_department_id.analytic_distribution_ids = [(0, 0, {
                    'department': dept,
                    'account_id': False,
                    'percentage': 0
                }) for dept in dict_type]

            # Cập tỷ lệ.
            domain = [('payment_date', '>=', self.start_date),
                      ('payment_date', '<=', self.end_date),
                      ('company_id.id', '=', tag_department_id.company_id.id),
                      ('not_sale', '=', False)]
            sale_payment_ids = self.env['crm.sale.payment'].sudo().search(domain)
            total_amount = sum([pay.amount_proceeds for pay in sale_payment_ids])
            if total_amount > 0:
                # Tính tỉ lệ theo phòng ban.
                dept_rate = []
                for dept in dict_type:
                    sale_dept_ids = sale_payment_ids.filtered(lambda x: x.service_id.his_service_type == dept)
                    dept_amount = sum([pay.amount_proceeds for pay in sale_dept_ids])
                    percentage_total = sum(dept_rate)
                    percentage = (dept_amount/total_amount)*100
                    # Đảm bảo tổng tỷ lệ luôn = 100
                    if dept == 'Surgery':
                        dept_rate.append(100 - percentage_total)
                    else:
                        dept_rate.append(round(percentage, 1))

                for dept, rate in zip(tag_department_id.analytic_distribution_ids, dept_rate):
                    dept.update({
                        'percentage': rate,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                    })
        return True

