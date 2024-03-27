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


class PlanCost(models.Model):
    _name = 'plan.cost'
    _description = 'Kế hoạch chi phí cố định'
    _inherit = 'money.mixin'

    name = fields.Char()
    year = fields.Char(string='Năm kế hoạch', required=True, readonly=True, states={'draft': [('readonly', False)]})
    user_id = user_id = fields.Many2one(comodel_name='res.users', readonly=True, store=True, string='Người báo cáo', default=lambda self: self.env.user)

    def get_month(self):
        return [(str(month), 'Tháng ' + num2words(month, lang='vi_VN'))for month in range(1, 13)]

    # month = fields.Char(string='Tháng kế hoạch', required=True, readonly=True, states={'draft': [('readonly', False)]})
    month = fields.Selection(selection='get_month', string='Tháng kế hoạch', required=True, store=True, readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one(string='Chi nhánh', comodel_name='res.company', required=True, domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], readonly=True, states={'draft': [('readonly', False)]})
    plan_amount = fields.Monetary(string='Giá trị kế hoạch', required=True, default=0.0, readonly=True, states={'draft': [('readonly', False)]})
    text_plan_amount = fields.Text(string='Bằng chữ:', compute='get_text_plan_amount')
    currency_id = fields.Many2one('res.currency', string='Loại tiền tệ', default=lambda self: self.env.company.currency_id)
    sale_by_source_line = fields.One2many('sale.by.source.line', 'plan_cost_id', string='Chi phí nguồn', readonly=True, states={'draft': [('readonly', False)]})
    cost_source_ids = fields.Many2one('source.config.account', string='Nguồn/Khối', required=True, readonly=True, states={'draft': [('readonly', False)]})
    cost_items_ids = fields.Many2one('cost.item.config', string='Nhóm chi phí', required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Nháp'), ('confirm', 'Xác nhận'), ('allotment', 'Đã phân bổ'), ('cancel', 'Hủy')],
                             string='Trạng thái', default='draft', required=True)
    note = fields.Text(string='Ghi chú', states={'draft': [('readonly', False)]}, copy=False, readonly=True)
    _sql_constraints = [
        ('unique_year_month_company', 'UNIQUE(year,month,company_ids)', 'Đã tồn tại bản ghi ngày này.'),
    ]

    def name_get(self):
        res = []
        for rec in self:
            name = "Chi phí kế hoạch %s năm %s" % (rec.month, rec.year)
            res += [(rec.id, name)]
        return res

    @api.depends('plan_amount')
    def get_text_plan_amount(self):
        for rec in self:
            if rec.plan_amount:
                rec.text_plan_amount = self.num2words_vnm(int(rec.plan_amount)) + " đồng"
            else:
                rec.text_plan_amount = 'Không đồng'

    def create_plan_detail(self):
        sale_source = self.env['sales.by.source']
        for record in self:
            if record.plan_amount > 0:
                year = int(record.year)
                month = int(record.month)
                days = monthrange(year, month)[1]
                amount = record.plan_amount/days
                for day in range(1, days + 1):
                    record_sale_source = sale_source.search([('date', '=', datetime.date(year, month, day)), ('company_id', '=', record.company_id.id),
                                                             ('type', '=', '03'), ('user_id', '=', record.user_id.id)])
                    if record_sale_source:
                        cost_line = {
                            'cost_source_ids': record.cost_source_ids.id,
                            'cost_items_ids': record.cost_items_ids.id,
                            'currency_id': record.currency_id.id,
                            'plan_cost_id': record.id,
                            'note': record.note,
                            'amount_cost': amount
                        }
                        record_sale_source.write({'sale_cost_line_id': [(0, 0, cost_line)]})
                    else:
                        cost_line = {
                            'cost_source_ids': record.cost_source_ids.id,
                            'cost_items_ids': record.cost_items_ids.id,
                            'currency_id': record.currency_id.id,
                            'plan_cost_id': record.id,
                            'note': record.note,
                            'amount_cost': amount
                        }
                        val = {
                            'is_automatic': True,
                            'state': 'posted',
                            'date': datetime.date(year, month, day),
                            'user_id': self.env.user.id,
                            'company_id': record.company_id.id,
                            'currency_id': record.currency_id.id,
                            'type': '03',
                            'sale_cost_line_id': [(0, 0, cost_line)]
                        }
                        res = sale_source.create(val)
                        res.action_confirm()
                        res.accounting_action_confirm()
            record.write({
                'state': 'allotment'
            })
        return True

    def reset_to_draft(self):
        #  Xóa các phiếu con phân bổ, và đưa phiếu phân bổ về trạng thái nháp.
        line_ids = self.sale_by_source_line.ids
        for line in line_ids:
            self.write({'sale_by_source_line': [(2, line, 0)]})
        self.write({'state': 'draft'})

    def action_confirm(self):
        self.write({
            'state': 'confirm'
        })

    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })