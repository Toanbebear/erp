from odoo import fields, models, api, _
from num2words import num2words
from calendar import monthrange
import datetime


# def num2words_vnm(num):
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()


class PlannedRevenue(models.Model):
    _name = 'annual.plan.revenue'
    _description = 'Kế hoạch doanh thu hàng năm'
    _inherit = 'money.mixin'

    state = fields.Selection([('draft', 'Nháp'), ('confirm', 'Xác nhận'), ('allotment', 'Đã phân bổ'), ('cancel', 'Hủy')], string='Trạng thái', default='draft', required=True)
    year = fields.Char(string='Năm kế hoạch', required=True, readonly=True, states={'draft': [('readonly', False)]})
    company_ids = fields.Many2one(string='Chi nhánh', comodel_name='res.company', required=True, readonly=True,
                                  domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], states={'draft': [('readonly', False)]})
    plan_amount = fields.Monetary(string='Giá trị kế hoạch', required=True, default=0.0)
    text_plan_amount = fields.Text(string='Bằng chữ:', compute='get_text_plan_amount')
    currency_id = fields.Many2one('res.currency', string='Loại tiền tệ',
                                  default=lambda self: self.env.company.currency_id)
    # worth_amount_of_month = fields.Monetary(string='Kế hoạch trong kỳ', compute='_get_amount_of_month', store=True)
    plan_revenue_detail_id = fields.One2many(comodel_name='annual.plan.revenue.detail', inverse_name='plan_revenue_id',
                                             string='Chi tiết kế hoạch')
    # text_worth_amount_of_month = fields.Text(string='Bằng chữ:', compute='get_text_plan_amount_month')
    subtotal = fields.Monetary(sting='Giá trị kế hoạch', default=0.0, compute='_get_subtotal', store=True)
    text_subtotal = fields.Char(string='Bằng chữ', compute='get_text_subtotal')

    _sql_constraints = [
        ('unique_year_company', 'UNIQUE(year,company_ids)', 'Đã tồn tại bản ghi ngày này.'),
    ]

    @api.depends('plan_revenue_detail_id.amount')
    def _get_subtotal(self):
        for rec in self:
            rec.subtotal = sum([element.amount for element in rec.plan_revenue_detail_id])

    @api.model
    def create(self, vals_list):
        print(vals_list)
        return super(PlannedRevenue, self).create(vals_list)

    def write(self, vals):
        return super(PlannedRevenue, self).write(vals)

    def confirm(self):
        self.state = 'confirm'

    def do_cancel(self):
        self.state = 'cancel'

    def name_get(self):
        res = []
        for rec in self:
            name = "Kế hoạch doanh thu hàng năm: %s | Chi nhánh: %s" % (rec.year, rec.company_ids.name)
            res += [(rec.id, name)]
        return res

    @api.depends('plan_amount')
    def get_text_plan_amount(self):
        for rec in self:
            if rec.plan_amount:
                rec.text_plan_amount = self.num2words_vnm(int(rec.plan_amount)) + " đồng"
            else:
                rec.text_plan_amount = 'Không đồng'

    @api.depends('subtotal')
    def get_text_subtotal(self):
        for rec in self:
            if rec.subtotal:
                rec.text_subtotal = self.num2words_vnm(int(rec.subtotal)) + " đồng"
            else:
                rec.text_subtotal = 'Không đồng'

    def create_plan_month(self):
        # Tạo kế hoạch tháng theo kế hoạch năm
        for rec in self:
            detail = self.env['annual.plan.revenue.detail']

            # Các tháng đã tồn tại:
            months = [(e.year, e.month) for e in detail.search([('plan_revenue_id', '=', rec.id)])]
            if len(months) != 12:
                # Tổng tiền đã cấp
                sub_amount = sum([e.amount for e in detail])

                # Giá trị cấp cho các tháng còn lại
                value = (rec.plan_amount - sub_amount) / (12 - len(months))

                for e in range(1, 13):
                    if (rec.year, e) not in months:
                        vals = {
                            'plan_revenue_id': rec.id,
                            'year': rec.year,
                            'month': e,
                            'company': rec.company_ids.id,
                            'amount': value,
                        }
                        detail.create(vals)
                rec.write({'state': 'allotment'})
            else:
                context = dict(self._context or {})
                context['message'] = 'Đã tồn tại kế hoạch chi tiết cho các tháng.'
                return {
                    'name': _('Thông báo'),  # label
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': self.env.ref('sci_notebook_accounting.note_account_message_wizard').id,
                    'res_model': 'note.account.message.wizard',  # model want to display
                    'target': 'new',  # if you want popup
                    'context': context,
                }


class PlannedRevenueDetail(models.Model):
    _name = 'annual.plan.revenue.detail'
    _description = 'Chi tiết kế hoạch trong tháng'

    plan_revenue_id = fields.Many2one('annual.plan.revenue')
    year = fields.Char(related='plan_revenue_id.year', string='Năm kế hoạch')
    month = fields.Char(string='Tháng kế hoạch')
    company = fields.Many2one(string='Chi nhánh', comodel_name='res.company')
    amount = fields.Monetary(string='Doanh thu kế hoạch tháng')
    currency_id = fields.Many2one('res.currency', related='plan_revenue_id.currency_id')

    def name_get(self):
        res = []
        for rec in self:
            name = "Kế hoạch chi tiết tháng %s năm %s" % (rec.month, rec.year)
            res += [(rec.id, name)]
        return res

    def create_plan_date(self):
        # Ghi nhận theo ngày dựa vào kế hoạch tháng.
        source = self.env['sales.by.source']
        source_line = self.env['sale.by.source.line']
        for rec in self:
            year = int(rec.year)
            month = int(rec.month)
            days = monthrange(year, month)[1]
            for day in range(1, days + 1):
                rec_day = datetime.datetime(year, month, day)
                val_line = {
                    'note': 'Doanh thu kế hoạch tháng %s năm %s' % (rec.month, rec.year),
                    'text_category_source': 'Số kế hoạch',
                    'text_category_source_utm': 'Số kế hoạch',
                    'amount_source': rec.amount / days,
                }
                source_line_id = source_line.create(val_line)

                vals = {
                    'state': 'posted',
                    'date': rec_day,
                    'user_id': self.env.uid,
                    'company_id': rec.company.id,
                    'currency_id': rec.currency_id.id,
                    'sale_source_line_id': [(6, 0, source_line_id.ids)],
                    'type': '02'
                }
                source.create(vals)
        return True

    def update_plan_date(self):
        self.ensure_one()
        source = self.env['sales.by.source']
        year = int(self.year)
        month = int(self.month)
        days = monthrange(year, month)[1]
        for day in range(1, days + 1):
            rec_day = datetime.datetime(year, month, day)
            rec = source.search([('type', '=', '02'), ('date', '=', rec_day), ('company_id', '=', self.company.id)])
            if rec:
                source_line = rec.sale_source_line_id
                for e in source_line:
                    e.write({
                        'text_category_source': 'Số kế hoạch',
                        'text_category_source_utm': 'Số kế hoạch',
                        'amount_source': self.amount / days,
                    })
