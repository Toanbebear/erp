from odoo import fields, api, models

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None


class ScanLoyaltyCard(models.TransientModel):
    _name = "scan.loyalty.card"
    _description = 'Scan loyalty card'

    name = fields.Char('Name')

    @api.onchange('name')
    def scan_qr(self):
        if self.name and '/' in self.name:
            name = self.name.rsplit('/', 1)[1]
            self.name = name.upper()
        if self.name:
            self.name = self.name.upper()

    def qr_confirm(self):
        for record in self:
            if record.name:
                for card in self.env.context.get('active_ids', []):
                    card_browse = self.env['loyalty.card'].browse(card)
                    card_browse.write({
                        'name': record.name
                    })
