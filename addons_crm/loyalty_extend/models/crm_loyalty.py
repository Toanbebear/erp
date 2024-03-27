from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, models
import re

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
from odoo.addons.queue_job.job import job


class InheritCrmLineProduct(models.Model):
    _inherit = 'crm.line.product'

    reward_id = fields.Many2one('crm.loyalty.line.reward', string='Reward')

    @job
    def sync_record(self, id):
        local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
        today_utc = local_tz.localize(datetime.now(), is_dst=None)
        today = today_utc.astimezone(utc).replace(tzinfo=None)
        today = date(today.year, today.month, today.day)
        clp = self.sudo().browse(id)
        if clp.reward_id:
            history = self.env['history.used.reward'].sudo().search(
                [('reward_line_id', '=', clp.reward_id.id), ('stage', '=', 'upcoming')], limit=1)
            relative = self.env['history.relative.reward'].sudo().search(
                [('line_product', '=', clp.id), ('stage', '=', 'upcoming')], limit=1)
            if clp.stage_line_product == 'sold':
                sl = clp.reward_id.number_use + 1
                if sl == clp.reward_id.quantity:
                    clp.reward_id.sudo().write({'stage': 'used',
                                                'date_use': today,
                                                'number_use': sl})
                    if history:
                        history.sudo().write({'stage': 'done'})
                    if relative:
                        relative.sudo().write({'stage': 'done'})
                else:
                    clp.reward_id.sudo().write({'stage': 'allow',
                                                'date_use': today,
                                                'number_use': sl})
            elif clp.stage_line_product == 'cancel':
                clp.reward_id.sudo().write({'stage': 'allow'})
                if history:
                    history.sudo().write({'stage': 'cancel'})
                if relative:
                    relative.sudo().write({'stage': 'cancel'})

    def write(self, vals):
        res = super(InheritCrmLineProduct, self).write(vals)
        if res:
            for clp in self:
                if 'stage_line_product' in vals:
                    if clp.id:
                        clp.sudo().with_delay(priority=0, channel='action_done_crm_line_product_loyalty').sync_record(
                            id=clp.id)
        return res


class InheritCrmLine(models.Model):
    _inherit = 'crm.line'

    @job
    def sync_record(self, id):
        cl = self.sudo().browse(id)
        if cl.reward_id:
            history = self.env['history.used.reward'].sudo().search(
                [('reward_line_id', '=', cl.reward_id.id), ('stage', '=', 'upcoming')], limit=1)
            relative = self.env['history.relative.reward'].sudo().search(
                [('line', '=', cl.id), ('stage', '=', 'upcoming')], limit=1)
            if cl.stage == 'done':
                if history:
                    history.sudo().write({'stage': 'done'})
                if relative:
                    relative.sudo().write({'stage': 'done'})
                sl = cl.reward_id.number_use + 1
                if sl == cl.reward_id.quantity:
                    cl.reward_id.sudo().write({'stage': 'used',
                                               'number_use': sl})
                else:
                    cl.reward_id.sudo().write({'stage': 'allow',
                                               'number_use': sl})
            elif cl.stage == 'cancel':
                cl.reward_id.sudo().write({'stage': 'allow'})
                if history:
                    history.sudo().write({'stage': 'cancel'})
                if relative:
                    relative.sudo().write({'stage': 'cancel'})

    def write(self, vals):
        res = super(InheritCrmLine, self).write(vals)
        if res:
            for cl in self:
                if 'stage' in vals:
                    if cl.id:
                        cl.sudo().with_delay(priority=0, channel='write_crm_line_loyalty').sync_record(id=cl.id)
        return res


class InheritCRMLoyaltyRank(models.Model):
    _inherit = 'crm.loyalty.rank'

    reward_ids = fields.One2many('crm.loyalty.rank.reward', 'rank', string='Cấu hình Voucher')


class InheritCRMLoyaltyLineReward(models.Model):
    _inherit = 'crm.loyalty.line.reward'

    reward_id = fields.Many2one('crm.loyalty.rank.reward', string='Quà tặng theo hạng thẻ')


class InheritLoyaltyCard(models.Model):
    _inherit = 'crm.loyalty.card'

    # Lịch sử sử dụng của người thân
    relative_reward = fields.One2many('history.relative.reward', 'loyalty', string='Người thân')
    history_used_reward_id = fields.One2many('history.used.reward', 'loyalty_id', string='Lịch sử')
    # TODO REMOVE IT
    # partner_id_2 = fields.Many2one('res.partner', string="Khách hàng")

    def cron_job_set_rank_paris(self):
        loyalties = self.env['crm.loyalty.card'].sudo().search([('brand_id.code', '=', 'PR')])
        for loyalty in loyalties:
            rank_id = self.env['crm.loyalty.rank'].sudo().search(
                [('brand_id.code', '=', 'PR'), ('money_fst', '<=', loyalty.amount), ('money_end', '>', loyalty.amount)])
            loyalty.rank_id = rank_id.id if rank_id else None

    def cron_job_birth_day_reward(self):
        today = datetime.now() + timedelta(hours=7)
        month = today.month if today.month != 0 else 1
        year = today.year
        _, last_day_of_month = monthrange(year, month)
        last_day = date(int(year), int(month), last_day_of_month)
        reward_ids = self.env['crm.loyalty.rank.reward'].sudo().search(
            [('is_birth_day', '=', True), ('stage', '=', 'allow')])
        if reward_ids:
            for reward in reward_ids:
                loyalties = self.env['crm.loyalty.card'].sudo().search([('rank_id', '=', reward.rank.id)])
                if loyalties:
                    vals = []
                    for loyalty in loyalties:
                        if loyalty.partner_id.birth_date and loyalty.partner_id.birth_date.month == month:
                            name = reward.name + ' Tháng %s năm %s' % (month, today.year)
                            vals.append({
                                'name': name,
                                'brand_id': reward.rank.brand_id.id,
                                'rank_id': reward.rank.id,
                                'type_reward': reward.type,
                                'product_ids': reward.product_ids.ids,
                                'preferential_method': reward.method,
                                'quantity': reward.number,
                                'number_use': 0,
                                'discount_percent': reward.percent if reward.method == 'discount' else 100,
                                'stage': 'allow',
                                'loyalty_id': loyalty.id,
                                'reward_id': reward.id,
                                'end_date': last_day
                            })
                    self.env['crm.loyalty.line.reward'].sudo().create(vals)

    def cron_job_cancel_reward(self):
        today = datetime.now() + timedelta(hours=7)
        rewards = self.env['crm.loyalty.line.reward'].sudo().search([('end_date', '<', today)])
        if rewards:
            for reward in rewards:
                reward.sudo().write({'stage': 'not_allow'})

    # def cron_job_partner_2(self):
    #     querry_1 = """
    #     update crm_loyalty_card clc
    #     set partner_id_2 = partner_id
    #     where brand_id = 2 and partner_id is not Null
    #     """
    #     self.env.cr.execute(querry_1)
    #     querry_2 = """
    #     update crm_loyalty_card clc
    #     set partner_id = null
    #     where brand_id = 2
    #     """
    #     self.env.cr.execute(querry_2)


class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    def _convert(self, text):
        patterns = {
            '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
            '[đ]': 'd',
            '[èéẻẽẹêềếểễệ]': 'e',
            '[ìíỉĩị]': 'i',
            '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
            '[ùúủũụưừứửữự]': 'u',
            '[ỳýỷỹỵ]': 'y'
        }
        output = text
        for regex, replace in patterns.items():
            output = re.sub(regex, replace, output)

            # deal with upper case
            output = re.sub(regex.upper(), replace.upper(), output)
        return output

    def cron_job_sms_birthday(self):
        config = self.env['ir.config_parameter'].sudo()
        content_sms = config.get_param('content_sms_birthday_pr')
        today = fields.Date.today()
        month = today.month
        day = today.day
        query = """
        select DISTINCT cl.partner_id, rp.name, cl.phone
        from crm_lead cl
        left join res_partner rp on rp.id = cl.partner_id
        where DATE_PART('day', cl.birth_date) = %s and DATE_PART('month', cl.birth_date) = %s and cl.brand_id = 3 and cl.stage_id = 4 and cl.country_id = 241
        and DATE_PART('year', CURRENT_DATE) - CAST(cl.year_of_birth AS int) < 100  and DATE_PART('year', CURRENT_DATE) - CAST(cl.year_of_birth AS int) > 15
        """
        self.env.cr.execute(query, (int(day), int(month)))
        result = self.env.cr.fetchall()
        for val in result:
            if '[NAME]' in content_sms and val[1].replace(' ', '').isalnum():
                val_sms = {
                    'name': 'SMS chúc mừng sinh nhật KH Paris',
                    'contact_name': val[1],
                    'partner_id': val[0],
                    'phone': val[2],
                    'send_date': fields.Datetime.now().replace(hour=1, minute=0, second=0),
                    'brand_id': 3,
                    'company_id': 36,
                    'desc': content_sms.replace('[NAME]', self._convert(val[1])),
                }
                sms = self.env['crm.sms'].sudo().create(val_sms)


class InheritCrmPhoneCall(models.Model):
    _inherit = 'crm.phone.call'

    def _convert(self, text):
        patterns = {
            '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
            '[đ]': 'd',
            '[èéẻẽẹêềếểễệ]': 'e',
            '[ìíỉĩị]': 'i',
            '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
            '[ùúủũụưừứửữự]': 'u',
            '[ỳýỷỹỵ]': 'y'
        }
        output = text
        for regex, replace in patterns.items():
            output = re.sub(regex, replace, output)

            # deal with upper case
            output = re.sub(regex.upper(), replace.upper(), output)
        return output

    def write(self, vals):
        config = self.env['ir.config_parameter'].sudo()
        res = super(InheritCrmPhoneCall, self).write(vals)
        for rec in self:
            content_sms = config.get_param('content_sms_sdvknm_pr')
            if rec.brand_id.id == 3 and rec.type_crm_id.id == 5 and vals.get('state') and vals.get('state') == 'not_connect':
                if '[NAME]' in content_sms and rec.partner_id.name.replace(' ', '').isalnum():
                    val_sms = {
                        'name': 'SDV không nghe máy - Paris',
                        'contact_name': rec.partner_id.name,
                        'partner_id': rec.partner_id.id,
                        'phone': rec.phone,
                        'send_date': fields.Datetime.now(),
                        'brand_id': 3,
                        'desc': content_sms.replace('[NAME]', self._convert(rec.partner_id.name)),
                    }
                    sms = self.env['crm.sms'].sudo().create(val_sms)
        return res