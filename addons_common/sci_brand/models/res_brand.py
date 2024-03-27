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

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResBrand(models.Model):
    _name = "res.brand"
    _description = 'Brand'
    _order = 'sequence, name'

    def copy(self, default=None):
        raise UserError(_('Duplicating a company is not allowed. Please create a new company instead.'))

    name = fields.Char(related='partner_id.name', string='Brand Name', required=True, store=True, readonly=False)
    code = fields.Char('Code', required=True)
    phone = fields.Char(related='partner_id.phone', store=True, readonly=False)
    sequence = fields.Integer(help='Used to order brand in the brand switcher', default=10)
    logo = fields.Binary(related='partner_id.image_1920', string="Brand Logo", readonly=False)
    type = fields.Selection([('hospital', 'Hospital'), ('academy', 'Academy')], string='Type', default="hospital")
    website = fields.Char(related='partner_id.website', readonly=False)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    company_ids = fields.One2many('res.company', 'brand_id', string='Branch')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The brand name must be unique!')
    ]
