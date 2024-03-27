from datetime import datetime
from odoo import fields, models, _


def get_years():
    year_list = []
    for i in range(2020, datetime.now().year + 5):
        year_list.append((str(i), str(i)))
    return year_list


class CRMSalePaymentPlan(models.Model):
    _inherit = 'crm.sale.payment.plan'

    year = fields.Selection(get_years(), string='Năm', default=str(datetime.now().year))

    def action_confirm(self):
        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.update_date))
            self.name = self.env['ir.sequence'].next_by_code('crm.sale.payment.plan', sequence_date=seq_date) or _(
                'New')
            self.write({'state': 'done'})
            sale_report_ids = self.env['sales.report'].sudo().search(
                [('company_id', '=', self.company_id.id), ('year', '=', self.year), ('month', '=', self.month)])
            for sale_report in sale_report_ids:
                ti_le = (sale_report.ds_tich_luy / sale_report.ds_chi_tieu) * 100
                sale_report.write({'ds_chi_tieu': self.amount_proceeds,
                                   'ti_le_hoan_thanh': "{:,.2f}".format(ti_le) + " %"})
