from odoo import fields, models, api, _


class CRMLead(models.Model):
    _inherit = "crm.lead"

    def name_get(self):
        res = []
        if self._context.get('name_crm_lead_checkin'):
            for booking in self:
                if booking.type == 'opportunity':
                    name = booking.name + ' - ' + booking.company_id.name if booking.company_id else booking.name
                    res.append((booking.id, _(name)))
        else:
            for physician in self:
                res.append((physician.id, _(physician.name)))
        return res
