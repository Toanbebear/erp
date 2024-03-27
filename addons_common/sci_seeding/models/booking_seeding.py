# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class BookingSeeding(models.Model):
    _name = 'seeding.booking'
    _description = 'Model quản lý booking seeding'

    crm_id = fields.Many2one('crm.lead')
    seeding_user_id = fields.Many2one('seeding.user')