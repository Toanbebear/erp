from odoo import api, models, fields, tools


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    contact_name = fields.Char(index=True)
    pass_port = fields.Char(index=True)
    code_customer = fields.Char(index=True)
    booking_date = fields.Datetime(index=True)

    def _auto_init(self):
        res = super(CrmLeadInherit, self)._auto_init()
        if not tools.index_exists(self._cr, 'crm_lead_index_phone'):
            tools.create_index(self._cr, 'crm_lead_index_phone',
                               self._table, ['phone', 'mobile', 'phone_no_3'])

        return res
