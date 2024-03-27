# -*- coding: utf-8 -*-
#############################################################################
#
#    SCI SOFTWARE
#
#    Copyright (C) 2019-TODAY SCI Software(<https://www.scisoftware.xyz>)
#    Author: SCI Software(<https://www.scisoftware.xyz>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResBrand(models.Model):

    _inherit = 'res.brand'

    cs_url = fields.Char(string="Caresoft Url")
    cs_access_token = fields.Char(string="Caresoft Token Voice")
