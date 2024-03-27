from dateutil.relativedelta import relativedelta

import random
from datetime import datetime, date
from odoo import fields, api, models, _
from odoo.tools.safe_eval import safe_eval

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from pytz import timezone, utc
from calendar import monthrange


class CrmLoyaltyCard(models.Model):
    _name = 'crm.loyalty.card'
    _inherit = ['qrcode.mixin']
    _description = 'Loyalty Card'

    _sql_constraints = [
        ('name_name', 'unique(name)', "Mã thẻ này đã được cấp!"),
        ('name_loyalty', 'unique(partner_id,brand_id)', "Khách hàng này đã có thẻ !"),
    ]

    # general
    name = fields.Char('Code card')
    rank_id = fields.Many2one('crm.loyalty.rank', string='Hạng thẻ', tracking=True)
    reward_ids = fields.One2many('crm.loyalty.line.reward', 'loyalty_id', string="Quà tặng", tracking=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', tracking=True, related='company_id.brand_id',
                               store=True)
    partner_id = fields.Many2one('res.partner', string='Khách hàng', tracking=True)
    birth_date = fields.Date('Ngày tháng năm sinh', related='partner_id.birth_date', store=False)
    phone = fields.Char('Điện thoại', related='partner_id.phone', tracking=True)
    code_customer = fields.Char('Mã khách hàng', related='partner_id.code_customer', tracking=True)
    country_id = fields.Many2one('res.country', string='Quốc gia', tracking=True, related='partner_id.country_id')
    state_id = fields.Many2one('res.country.state', string='Thành phố', tracking=True, related='partner_id.state_id')
    address_detail = fields.Char('Địa chỉ chi tiết', related='partner_id.street', tracking=True)
    source_id = fields.Many2one('utm.source', string='Nguồn ban đầu', tracking=True)
    create_by = fields.Many2one('res.users', string='Được tạo bởi', tracking=True, default=lambda self: self.env.user)
    create_on = fields.Datetime('Được tạo ngày', tracking=True, default=fields.Datetime.now())
    company_id = fields.Many2one('res.company', string='Chi nhánh', tracking=True,
                                 default=lambda self: self.env.company)
    date_interaction = fields.Date('Ngày tương tác gần nhất', tracking=True)
    qr = fields.Binary(string="QR Code", compute='generate_qr')
    url = fields.Char('url')
    loyalty_import = fields.Boolean('Loyalty import')
    validity_card = fields.Integer('Thời gian hiệu lực', related='rank_id.validity_card', store=True)
    due_date = fields.Date('Ngày hết hạn', compute='set_due_date', store=True)
    amount_crm = fields.Float('Tiền đã sử dụng trên CRM FPT')

    # cash
    currency_id = fields.Many2one('res.users', string='User', tracking=True)
    amount = fields.Monetary('Tổng tiền sử dụng', compute='compute_total_order', tracking=True, store=True)

    # date special
    bonus = fields.Monetary('Bonus', tracking=True)
    rw_date_spc_ids = fields.One2many('crm.loyalty.reward.date.special', 'loyalty_id', string='Reward date special',
                                      tracking=True)

    image = fields.Binary('Image', default=False)
    date_special = fields.Many2many('crm.loyalty.date', 'loyalty_date_ref', 'loyalty', 'date_spc',
                                    string='Special date')
    time_active = fields.Integer('Time active')
    money_reward = fields.Monetary('Money reward')
    bonus_date_ids = fields.One2many('crm.loyalty.reward.date.special', 'loyalty_id', string='Bonus date')
    state = fields.Selection([('active', 'Đang hoạt động'), ('expire', 'Hết hạn')], string='Trạng thái',
                             compute='set_state_loyalty', store=True)

    flag = fields.Boolean('Chỉ dùng khi cập nhật mã thẻ')

    @api.depends('due_date')
    def set_state_loyalty(self):
        now = date.today()
        for rec in self:
            if rec.due_date:
                if rec.due_date > now:
                    rec.state = 'active'
                else:
                    rec.state = 'expire'
            else:
                rec.state = 'expire'

    def update_state_loyalty(self):
        self.env.cr.execute(""" UPDATE crm_loyalty_card
                                SET state = 'expire'
                                WHERE state != 'expire' and due_date < (CURRENT_DATE at time zone 'utc');""")
        self.env.cr.execute(""" UPDATE crm_loyalty_line_reward AS cllr
                                SET stage = 'not_allow'
                                FROM crm_loyalty_card AS clc
                                WHERE cllr.loyalty_id = clc.id
                                AND clc.state = 'expire' AND cllr.stage = 'allow';
                                """)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CrmLoyaltyCard, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone']:
                fields[field_name]['exportable'] = False

        return fields

    def card_issuance(self, brand):
        """
        Mã thẻ được đặt theo quy tắc:
            +) 2 ký tự ầu là ký hiệu của thương hiệu
            +) 7 ký tự tiếp theo là dãy số ngẫu nhiên và ko có quá 3 chữ số 0 trong dãy số ó
            +) 3 ký tự cuối là đuôi 999
        """
        existing_codes = self.env['crm.loyalty.card'].sudo().search([('brand_id', '=', brand.id)]).mapped('name')
        while True:
            code = str(brand.code) + ''.join(random.choices('0123456789', k=7)) + '999'
            if (code not in existing_codes) and (code.count("0") < 3):
                return code

    # @a pi.depends('partner_id.sale_order_ids.state', 'partner_id.sale_order_ids.amount_total', 'rank_id')
    # def compute_total_order(self):
    #     for record in self:
    #         record.amount = 0
    #         amount = sum([so.amount_total for so in record.partner_id.sale_order_ids if so.state in ('sale', 'sent')])
    #         record.amount = amount
    @api.depends('date_interaction', 'validity_card')
    def set_due_date(self):
        for rec in self:
            rec.due_date = False
            if rec.date_interaction:
                rec.due_date = rec.date_interaction + relativedelta(days=+ rec.validity_card)

    @api.depends('name')
    def generate_qr(self):
        for rec in self:
            rec.qr = False
            if rec.name:
                rec.qr = self.qrcode(rec.name)

    def name_get(self):
        res = []
        for record in self:
            name = 'Chưa có mã thẻ'
            if record.name:
                name = '%s' % record.name
            if record.rank_id and record.rank_id.name:
                name = '[%s] ' % record.rank_id.name + name
            res.append((record.id, name))
        return res

    def write(self, vals):
        res = super(CrmLoyaltyCard, self).write(vals)
        for rec in self:
            if vals.get('amount'):
                rec.set_rank(rec.amount, rec.rank_id, rec.partner_id)
            if vals.get('state') == 'expire':
                if rec.reward_ids:
                    for line in rec.reward_ids:
                        line.stage = 'not_allow'
        return res

    def create(self, vals):
        res = super(CrmLoyaltyCard, self).create(vals)
        # brand = self.env.company.brand_id
        code = self.card_issuance(res.brand_id)
        res.name = code
        return res

    def set_rank(self, amount, rank, partner_id):
        if amount:
            rank_now = self.env['crm.loyalty.rank'].search(
                [('money_fst', '<=', amount),
                 ('money_end', '>=', amount),
                 ('brand_id', '=', self.brand_id.id)], limit=1)
            if rank is False or rank.id != rank_now.id:
                self.rank_id = rank_now
                self.set_reward(self.rank_id, partner_id)
                self.get_special_date(self.rank_id)

    def set_reward(self, rank, partner):
        if rank:
            for reward in self.reward_ids:
                if reward.rank != rank and reward.stage == 'allow':
                    reward.sudo().write({'stage': 'not_allow'})
            voucher_ids = self.env['crm.loyalty.rank.reward'].search([('rank', '=', rank.id), ('stage', '=', 'allow')])
            if voucher_ids:
                for voucher in voucher_ids:
                    if not voucher.is_birth_day:
                        reward = self.env['crm.loyalty.line.reward'].sudo().create({
                            'name': voucher.name,
                            'brand_id': voucher.rank.brand_id.id,
                            'rank_id': voucher.rank.id,
                            'type_reward': voucher.type,
                            'product_ids': voucher.product_ids.ids,
                            'preferential_method': voucher.method,
                            'quantity': voucher.number,
                            'number_use': 0,
                            'discount_percent': voucher.percent if voucher.method == 'discount' else 100,
                            'stage': 'allow',
                            'loyalty_id': self.id,
                            'reward_id': voucher.id
                        })
                    else:
                        local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
                        today_utc = local_tz.localize(datetime.now(), is_dst=None)
                        today = today_utc.astimezone(utc).replace(tzinfo=None)
                        month = today.month
                        last_day = date(today.year, today.month, monthrange(today.year, month)[1])
                        name = voucher.name + ' Tháng %s năm %s' % (month, today.year)
                        if partner.birth_date and partner.birth_date.month == month:
                            self.env['crm.loyalty.line.reward'].sudo().create({
                                'name': name,
                                'brand_id': voucher.rank.brand_id.id,
                                'rank_id': voucher.rank.id,
                                'type_reward': voucher.type,
                                'product_ids': voucher.product_ids.ids,
                                'preferential_method': voucher.method,
                                'quantity': voucher.number,
                                'number_use': 0,
                                'discount_percent': voucher.percent if voucher.method == 'discount' else 100,
                                'stage': 'allow',
                                'loyalty_id': self.id,
                                'reward_id': voucher.id,
                                'end_date': last_day
                            })

    def get_special_date(self, rank):
        if rank.date_special:
            self.time_active = rank.time_active
            self.money_reward = rank.money_reward
            self.date_special = [(6, 0, rank.date_special.ids)]

    def find_loyalty_card_by_ref_using_qr(self, qr):
        if '/' in qr:
            qr = qr.rsplit('/', 1)[1]
            qr = qr.upper()
        loyalty_card = self.search([('name', '=', qr)], limit=1)
        if not loyalty_card:
            action = self.env.ref('loyalty.loyalty_card_find')
            result = action.read()[0]
            context = safe_eval(result['context'])
            context.update({
                'default_state': 'warning',
                'default_status': _('KHÔNG CÓ MÃ QR %s TRÊN HỆ THỐNG') % qr
            })
            result['context'] = context
            return result
        action = self.env.ref('loyalty.action_open_loyalty')
        result = action.read()[0]
        res = self.env.ref('loyalty.loyalty_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = loyalty_card.id
        return result

    def search_loyalty(self, ll):
        loyalty = self.env['crm.loyalty.card'].search([('date_special', '!=', False), ('id', 'not in', ll.ids)],
                                                      limit=100)
        if loyalty:
            self.cron_money_reward_loyalty(loyalty)
        else:
            self.cron_money_reward_loyalty(loyalty)

    # cong tien thuong
    def cron_money_reward_loyalty(self, ll=False):
        if not ll:
            loyalty = self.env['crm.loyalty.card'].search([('date_special', '!=', False)], limit=100)
        else:
            loyalty = ll
        # Todo: Date.today lấy ngày trên server
        today = fields.Date.today()
        month = today.month
        day = today.day
        for lt in loyalty:
            for rw in lt.date_special:
                if rw.type == 'b_date' and lt.partner_id.birth_date.month == month \
                        and lt.partner_id.birth_date.day == day:
                    self.set_bonus_date_special(rw, lt)

                elif rw.type == 'other' and rw.month == month and rw.date == date:
                    self.set_bonus_date_special(rw, lt)

    def update_code_loyalty(self):
        update_card = self.env['crm.loyalty.card'].search([('flag', '=', False)], limit=5000)
        for card in update_card:
            card.name = card.card_issuance(card.brand_id)
            card.flag = True

    def cancel_flag(self):
        self.env.cr.execute(""" UPDATE crm_loyalty_card
                                SET flag = False
                                WHERE name ~ '0.*0.*0' and flag = true;""")

    def set_bonus_date_special(self, rw, lt):
        self.env['crm.loyalty.reward.date.special'].create({
            'name': 'Bonus %s' % rw.name,
            'brand_id': lt.brand_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'reward_origin': lt.money_reward,
            'loyalty_id': lt.id,
            'type': 'reward',
            'active_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now() + relativedelta(days=+ lt.time_active),
            'date_special': rw.id,
        })

    def update_code_card(self):
        # self.ensure_one()
        return {
            'name': 'CẬP NHẬT MÃ THẺ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('loyalty.update_code_card_form').id,
            'res_model': 'update.code.card',
            'context': {
                'default_loyalty_id': self.id,
            },
            'target': 'new',
        }
