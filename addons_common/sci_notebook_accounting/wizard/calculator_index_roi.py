from odoo import fields, models, api, _


class CalculatorROI(models.TransientModel):
    _name = 'index.roi'
    _description = 'Tính chỉ số ROI'

    start_date = fields.Date(string='Từ ngày')
    end_date = fields.Date(string='Tới ngày')
    # company = fields.Many2many('res.company', string='Chi nhánh', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    brand = fields.Many2one('res.brand', string='Thương hiệu', domain=lambda self: [('id', 'in', self.env.user.company_ids.brand_id.ids)])

    def calculator_roi(self):
        sale_by_source = self.env['sales.by.source'].search([('date', '>=', self.start_date),
                                                             ('date', '<=', self.end_date),
                                                             ('company_id.brand_id', 'in', self.brand.ids)])
        sale_amount = 0.0
        cost_amount = 0.0
        ROI = 0.0
        if sale_by_source:

            for element in sale_by_source:
                sale_category = element.sale_source_line_id
                cost_category = element.sale_cost_line_id
                sale_amount += sum([line.amount_source for line in sale_category if line.category_source.code == 'MAR'])
                cost_amount += sum([line.amount_cost for line in cost_category if line.cost_items_ids.cost == True])

            if sale_amount != 0:
                ROI = cost_amount / sale_amount

        context = dict(self._context or {})

        context['message'] = 'Tổng tiền đã nạp: %s, Tổng doanh số MKT: %s, CHỈ SỐ ROI: %s' % ("{:,.0f}".format(cost_amount), "{:,.0f}".format(sale_amount), "{:,.0f}".format(ROI))

        return {
            'name': _('Thông báo'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('sci_notebook_accounting.note_account_message_wizard').id,
            'res_model': 'note.account.message.wizard',
            'target': 'new',
            'context': context,
        }
