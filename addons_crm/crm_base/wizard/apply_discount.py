from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date

# def num2words_vnm(num):
#     num = int(num)
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

class CrmLeadPaid(models.TransientModel):
    _name = 'crm.lead.paid'
    _description = 'Crm Lead paid'
    _inherit = 'money.mixin'

    crm_id = fields.Many2one('crm.lead', string='CRM', required=True)
    add_amount_paid_crm = fields.Monetary('Số tiền khách trả', default=0, currency_field='currency_id')
    company_id = fields.Many2one('res.company', string='Company', related='crm_id.company_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    amount_paid_crm_text = fields.Char(string='Bằng chữ', readonly=True)

    @api.onchange('add_amount_paid_crm')
    def translate_value(self):
        # quy đổi tiền về tiền việt
        self.amount_paid_crm_text = self.num2words_vnm(round(self.add_amount_paid_crm)) + " đồng"

    def add_amount_paid_crm_pay(self):
        if self.crm_id:
            self.crm_id.write({'add_amount_paid_crm': self.add_amount_paid_crm})


class ApplyDiscountProgram(models.TransientModel):
    _name = 'crm.apply.discount.program'
    _description = 'Apply Discount Program'

    name = fields.Char('Name')
    type_action = fields.Selection([('apply', 'Áp dụng Chương trình khuyến mãi'), ('reverse_part', 'Hoàn lại một phần'),
                                    ('reverse_full', 'Hoàn lại tất cả')], string='Hành động thực hiện', default='apply')
    description = fields.Char(string='Giải thích', compute='depends_type_action')
    program_discount_id = fields.Many2one('crm.discount.program', string='Discount program')
    crm_id = fields.Many2one('crm.lead', string='Booking/lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    campaign_id = fields.Many2one('utm.campaign', string='Campaign')

    @api.onchange('crm_id')
    def get_campain_apply_discount_program(self):
        domain = [('campaign_status', '=', '2')]
        if self.crm_id:
            domain += [('brand_id', '=', self.crm_id.brand_id.id)]
        return {'domain': {'campaign_id': [('id', 'in', self.env['utm.campaign'].search(domain).ids)]}}

    @api.depends('type_action')
    def depends_type_action(self):
        for record in self:
            if record.type_action == 'reverse_full':
                record.description = "Sau khi thực hiện hành động này, Coupon khuyến mãi sẽ được hủy bỏ ở tất cả các line dịch vụ, bao gồm cả các line đã sử dụng.Điều này có thể gây ra chênh lệch số tiền khách đóng ở những line đã sử dụng"
            elif record.type_action == 'reverse_part':
                record.description = "Sau khi thực hiện hành động này, Coupon khuyến mãi mà người dùng chọn sẽ được hủy bỏ ở các line dịch vụ chưa sử dụng"
            else:
                record.description = "Áp dụng Coupon khuyến mãi"

    @api.onchange('crm_id', 'type_action', 'campaign_id')
    def onchange_crm(self):
        if self.crm_id:
            domain = []
            if self.type_action == 'apply':
                if self.campaign_id:
                    domain += [('stage_prg', '=', 'active'), ('campaign_id', '=', self.campaign_id.id),
                               ('brand_id', '=', self.crm_id.brand_id.id)]
                else:
                    domain += [('stage_prg', '=', 'active'), ('brand_id', '=', self.crm_id.brand_id.id)]
            else:
                domain += [('id', 'in', self.crm_id.prg_ids.ids)]
            return {'domain': {'program_discount_id': [
                ('id', 'in', self.env['crm.discount.program'].search(domain).ids)]}}
