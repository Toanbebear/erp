from odoo import api, models, fields, _


class Base(models.AbstractModel):
    _inherit = "base"

    # map_id = fields.Many2one('records.com.ent.rel', string=_('Map record'), compute='_compute_map_record')
    # ent_id = fields.Integer(string=_('Enterprise ID'), compute='')