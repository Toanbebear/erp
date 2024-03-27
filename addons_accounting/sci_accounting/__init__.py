# -*- coding: utf-8 -*-

from . import models, wizard
from odoo import api, SUPERUSER_ID


def post_init(cr, registry):
    """ Set value for new date field of old stock valuation layer record."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for layer in env['stock.valuation.layer'].search([('date', '=', False)]):
        layer.write({'date': layer.create_date})
