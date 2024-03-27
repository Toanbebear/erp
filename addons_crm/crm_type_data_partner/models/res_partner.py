from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class InheritPartnerTypeData(models.Model):
    _inherit = 'res.partner'

    type_data_partner = fields.Selection([('old', 'Cũ'), ('new', 'Mới')], string='Loại data')
    return_custom = fields.Boolean('Khách hàng quay lại ?', compute='check_return_custom', store=True)

    @api.depends('type_data_partner')
    def check_return_custom(self):
        for record in self:
            record.return_custom = False
            if record.type_data_partner == 'old':
                record.return_custom = True

