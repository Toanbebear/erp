# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class SeedingUser(models.Model):
    _name = 'seeding.user'
    _description = 'Model quản lý user seeding'

    code_user = fields.Char(string='Mã tài khoản')
    name = fields.Char(string='Tên người dùng')
    phone = fields.Char("Số điện thoại người dùng")