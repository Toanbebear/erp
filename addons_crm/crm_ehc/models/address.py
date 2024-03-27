import logging

from odoo import fields, api, models

_logger = logging.getLogger(__name__)


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    id_dvhc = fields.Integer('ID Đơn vị hành chính')


class ResCountryDistrict(models.Model):
    _inherit = "res.country.district"

    id_dvhc = fields.Integer('ID Đơn vị hành chính')


class ResCountryWard(models.Model):
    _inherit = "res.country.ward"

    id_dvhc = fields.Integer('ID Đơn vị hành chính')


class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    # ward_id = fields.Many2one('res.country.ward', string='Phường/ Xã')

    @api.onchange('district_id')
    def onchange_district_id(self):
        if self.district_id:
            return {'domain': {'ward_id': [
                ('id', 'in', self.env['res.country.ward'].search([('district_id', '=', self.district_id.id)]).ids)]}}