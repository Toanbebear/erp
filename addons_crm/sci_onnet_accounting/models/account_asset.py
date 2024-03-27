from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = "account.asset"

    picking_id = fields.Many2one('stock.picking', string='Phiếu kho')

    def write(self, values):
        res = super(AccountAsset, self).write(values)
        if ('picking_id' in values) and values.get('picking_id'):
            refs = ["<a href=# data-oe-model=account.asset data-oe-id=%s>%s</a>" % (self.id, self.name)]
            message = "%s đã gán tài sản/chi phí: %s với phiếu kho này." % (self.env.user.name, ','.join(refs))
            self.picking_id.message_post(body=message)
        return res