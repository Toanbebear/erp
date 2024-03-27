import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class UtmSourceEhc(models.Model):
    _name = "crm.hh.ehc.utm.source"
    _description = 'UTM Source EHC'

    name = fields.Char(string='Tên nguồn')
    code = fields.Char(string='Mã nguồn')


class MapUtmSourceEhc(models.Model):
    _name = "crm.hh.ehc.map.utm.source"
    _description = 'UTM Source EHC'

    erp_source = fields.Many2one('crm.category.source', string='Nguồn ERP')
    ehc_source = fields.Many2many('crm.hh.ehc.utm.source', string='Nguồn EHC')
