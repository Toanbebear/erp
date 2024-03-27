from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class Purchase(models.Model):
    _inherit = 'purchase.order'

    partner_ref = fields.Char('Vendor Reference', copy=False, related='partner_id.code_customer',
        help="Reference of the sales order or bid sent by the vendor. "
             "It's used to do the matching when you receive the "
             "products as this reference is usually written on the "
             "delivery order sent by your vendor.")