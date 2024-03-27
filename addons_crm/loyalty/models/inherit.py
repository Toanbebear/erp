import logging

from odoo import fields, api, models
from lxml import etree
import json
from odoo.exceptions import ValidationError
from pytz import timezone, utc
from datetime import datetime, date
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class CrmLoyalty(models.Model):
    _inherit = 'crm.lead'

    loyalty_id = fields.Many2one('crm.loyalty.card', string='Loyalty')

    def show_reward(self):
        return {
            'name': 'Ưu đãi thẻ',
            'view_mode': 'tree',
            'res_model': 'crm.loyalty.line.reward',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('loyalty.reward_tree').id,
            'domain': [('loyalty_id', '=', self.loyalty_id.id)],
            'target': 'new',
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CrmLoyalty, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
        doc = etree.XML(res['arch'])
        view_booking = self.env.ref('crm_base.crm_lead_form_booking')
        if view_type == 'form' and view_id == view_booking.id:
            for node in doc.xpath("//field[@name='user_id']"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def update_info(self):
        res = super(CrmLoyalty, self).update_info()
        if self.booking_ids:
            loyalty_card = self.env['crm.loyalty.card'].search(
                [('partner_id', '=', self.partner_id.id), ('brand_id', '=', self.company_id.brand_id.id)],
                order='id desc', limit=1)
            for rec in self.booking_ids:
                rec.loyalty_id = loyalty_card
        return res


class LoyaltyCrmLine(models.Model):
    _inherit = 'crm.line'

    reward_id = fields.Many2one('crm.loyalty.line.reward', string='Reward')


class LoyaltyCrmLineCancel(models.TransientModel):
    _inherit = 'crm.line.cancel'

    def cancel_crm_line(self):
        res = super(LoyaltyCrmLineCancel, self).cancel_crm_line()
        if self.crm_line_id and self.crm_line_id.reward_id:
            self.crm_line_id.reward_id.stage = 'allow'
        return res


class SaleOrderLoyalty(models.Model):
    _inherit = 'sale.order'

    loyalty_id = fields.Many2one('crm.loyalty.card', string='Loyalty')

    @api.model
    def create(self, vals):
        res = super(SaleOrderLoyalty, self).create(vals)
        if res.partner_id:
            loyalty = self.env['crm.loyalty.card'].search(
                [('partner_id', '=', self.partner_id.id),
                 ('brand_id', '=', self.company_id.brand_id.id)])
            res.loyalty_id = loyalty.id
        return res

    @api.onchange('partner_id')
    def set_loyalty(self):
        if self.partner_id:
            loyalty = self.env['crm.loyalty.card'].search(
                [('partner_id', '=', self.partner_id.id), ('brand_id', '=', self.company_id.brand_id.id)])
            self.loyalty_id = loyalty.id

    # @job
    # def action_record(self, id):
    #     local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
    #     today_utc = local_tz.localize(datetime.now(), is_dst=None)
    #     today = today_utc.astimezone(utc).replace(tzinfo=None)
    #     today = date(today.year, today.month, today.day)
    #     so = self.sudo().browse(id)
    #     if so.loyalty_id:
    #         so.loyalty_id.amount += so.amount_total
    #         amount = so.loyalty_id.amount
    #         rank = so.loyalty_id.rank_id
    #         partner = so.partner_id
    #         so.loyalty_id.set_rank(amount, rank, partner)
    #     else:
    #         loyalty = self.env['crm.loyalty.card'].search(
    #             [('partner_id', '=', self.partner_id.id), ('brand_id', '=', so.company_id.brand_id.id)])
    #         so.loyalty_id = loyalty.id
    #         so.loyalty_id.amount += so.amount_total
    #         amount = so.loyalty_id.amount
    #         rank = so.loyalty_id.rank_id
    #         partner = so.partner_id
    #         so.loyalty_id.set_rank(amount, rank, partner)
    #     if so.order_line:
    #         for sol in so.order_line:
    #             if sol.crm_line_id:
    #                 history = self.env['history.used.reward'].sudo().search(
    #                     [('reward_line_id', '=', sol.crm_line_id.reward_id.id), ('stage','=','upcoming')], limit=1)
    #                 relative = self.env['history.relative.reward'].sudo().search([('line', '=', sol.crm_line_id.id), ('stage','=','upcoming')], limit=1)
    #
    #                 if history:
    #                     _logger.info(history.id)
    #                     history.sudo().write({'stage': 'done'})
    #                 if relative:
    #                     _logger.info(relative.id)
    #                     relative.sudo().write({'stage': 'done'})
    #                 if sol.crm_line_id.reward_id.number_use == sol.crm_line_id.reward_id.quantity:
    #                     pass
    #                 else:
    #                     sl = sol.crm_line_id.reward_id.number_use + 1
    #                     if sl == sol.crm_line_id.reward_id.quantity:
    #                         sol.crm_line_id.reward_id.sudo().write({'stage': 'used',
    #                                                                 'date_use': today,
    #                                                                 'number_use': sl})
    #                     else:
    #                         sol.crm_line_id.reward_id.sudo().write({'stage': 'allow',
    #                                                                 'date_use': today,
    #                                                                 'number_use': sl})

    @job
    def action_record(self, id):
        local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
        today_utc = local_tz.localize(datetime.now(), is_dst=None)
        today = today_utc.astimezone(utc).replace(tzinfo=None)
        today = date(today.year, today.month, today.day)
        so = self.sudo().browse(id)
        loyalty = so.loyalty_id if so.loyalty_id else self.env['crm.loyalty.card'].sudo().search(
            [('partner_id', '=', self.partner_id.id), ('brand_id', '=', so.company_id.brand_id.id)], limit=1)
        self.env.cr.execute("""
        SELECT SUM(amount_total) AS total_amount
        FROM sale_order
        WHERE state in ('sale', 'done') AND partner_id = %s AND brand_id = %s;""" % (so.partner_id.id, so.brand_id.id))
        sum = self.env.cr.fetchall()
        sum = sum[0][0]
        loyalty.amount = sum + loyalty.amount_crm
        rank = loyalty.rank_id
        partner = so.partner_id
        loyalty.set_rank(sum, rank, partner)

        # if so.loyalty_id:
        #     so.loyalty_id.amount += so.amount_total
        #     amount = so.loyalty_id.amount
        #     rank = so.loyalty_id.rank_id
        #     partner = so.partner_id
        #     so.loyalty_id.set_rank(amount, rank, partner)
        # else:
        #     loyalty = self.env['crm.loyalty.card'].search(
        #         [('partner_id', '=', self.partner_id.id), ('brand_id', '=', so.company_id.brand_id.id)])
        #     so.loyalty_id = loyalty.id
        #     so.loyalty_id.amount += so.amount_total
        #     amount = so.loyalty_id.amount
        #     rank = so.loyalty_id.rank_id
        #     partner = so.partner_id
        #     so.loyalty_id.set_rank(amount, rank, partner)
        if so.order_line:
            for sol in so.order_line:
                if sol.crm_line_id:
                    history = self.env['history.used.reward'].sudo().search(
                        [('reward_line_id', '=', sol.crm_line_id.reward_id.id), ('stage', '=', 'upcoming')], limit=1)
                    relative = self.env['history.relative.reward'].sudo().search(
                        [('line', '=', sol.crm_line_id.id), ('stage', '=', 'upcoming')], limit=1)

                    if history:
                        _logger.info(history.id)
                        history.sudo().write({'stage': 'done'})
                    if relative:
                        _logger.info(relative.id)
                        relative.sudo().write({'stage': 'done'})
                    if sol.crm_line_id.reward_id.number_use == sol.crm_line_id.reward_id.quantity:
                        pass
                    else:
                        sl = sol.crm_line_id.reward_id.number_use + 1
                        if sl == sol.crm_line_id.reward_id.quantity:
                            sol.crm_line_id.reward_id.sudo().write({'stage': 'used',
                                                                    'date_use': today,
                                                                    'number_use': sl})
                        else:
                            sol.crm_line_id.reward_id.sudo().write({'stage': 'allow',
                                                                    'date_use': today,
                                                                    'number_use': sl})

    # def action_confirm(self):
    #     res = super(SaleOrderLoyalty, self).action_confirm()
    #     if res:
    #         for so in self:
    #             self.sudo().with_delay(priority=0, channel='action_done_sale_order_loyalty').action_record(id=so.id)
    #     return res

    def action_confirm(self):
        res = super(SaleOrderLoyalty, self).action_confirm()
        self.sudo().with_delay(priority=0, channel='action_done_sale_order_loyalty').action_record(id=self.id)
        return res


    def action_draft(self):
        res = super(SaleOrderLoyalty, self).action_draft()
        loyalty = self.loyalty_id if self.loyalty_id else self.env['crm.loyalty.card'].sudo().search(
            [('partner_id', '=', self.partner_id.id), ('brand_id', '=', self.company_id.brand_id.id)], limit=1)
        self.env.cr.execute("""
                SELECT SUM(amount_total) AS total_amount
                FROM sale_order
                WHERE state in ('sale', 'done') AND partner_id = %s AND brand_id = %s;""" % (self.partner_id.id, self.brand_id.id))
        sum = self.env.cr.fetchall()
        sum = sum[0][0]
        loyalty.amount = sum + loyalty.amount_crm
        return res

class CheckPartnerLoyalty(models.TransientModel):
    _inherit = 'check.partner.qualify'
    _description = 'Check Partner AndQualify'

    def create_phone_call(self, booking):
        res = super(CheckPartnerLoyalty, self).create_phone_call(booking)
        loyalty = self.env['crm.loyalty.card'].search(
            [('partner_id', '=', booking.partner_id.id), ('brand_id', '=', self.company_id.brand_id.id)])
        if loyalty:
            booking.loyalty_id = loyalty.id
        return res

    def qualify(self):
        res = super(CheckPartnerLoyalty, self).qualify()
        booking = self.env['crm.lead'].search([('id', '=', res['res_id'])])
        if booking and not booking.loyalty_id:
            loyalty_card = self.env['crm.loyalty.card'].search(
                [('partner_id', '=', booking.partner_id.id), ('brand_id', '=', self.company_id.brand_id.id)],
                order='id desc', limit=1)
            if loyalty_card:
                booking.loyalty_id = loyalty_card
            else:
                loyalty = self.env['crm.loyalty.card'].create({
                    'partner_id': booking.partner_id.id,
                    'company_id': booking.company_id.id,
                    'date_interaction': fields.Datetime.now(),
                    'source_id': booking.source_id.id,
                })
                booking.loyalty_id = loyalty.id
                rank_now = self.env['crm.loyalty.rank'].search(
                    [('money_fst', '<=', loyalty.amount),
                     ('money_end', '>=', loyalty.amount),
                     ('brand_id', '=', booking.company_id.brand_id.id)], limit=1)
                loyalty.rank_id = rank_now.id
        return res


class LoyaltySelectService(models.TransientModel):
    _inherit = 'crm.select.service'

    # def create_quotation(self):
    #     res = super(LoyaltySelectService, self).create_quotation()
    #
    #     if not self.booking_id.loyalty_id:
    #         loyalty_id = self.env['crm.loyalty.card'].search(
    #             [('partner_id', '=', self.partner_id.id), ('brand_id', '=', self.booking_id.company_id.brand_id.id)])
    #         if loyalty_id:
    #             self.booking_id.loyalty_id = loyalty_id.id
    #         else:
    #             loyalty = self.env['crm.loyalty.card'].create({
    #                 'partner_id': self.partner_id.id,
    #                 'company_id': self.booking_id.company_id.id,
    #                 'date_interaction': fields.Datetime.now(),
    #                 'source_id': self.booking_id.source_id.id,
    #             })
    #             self.booking_id.loyalty_id = loyalty.id
    #             rank_now = self.env['crm.loyalty.rank'].search(
    #                 [('money_fst', '<=', loyalty.amount),
    #                  ('money_end', '>=', loyalty.amount),
    #                  ('brand_id', '=', self.booking_id.company_id.brand_id.id)], limit=1)
    #             loyalty.rank_id = rank_now.id
    #     return res
