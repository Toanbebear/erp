from odoo import models, api, fields, _

class PurchasOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def get_account_analytic(self):
        for line in self:
            if not line.product_id:
                break
            company_id = self.company_id.id if self.company_id else self.env.company
            if not line.product_id or not line.product_id.product_tmpl_id or not line.product_id.product_tmpl_id.categ_id:
                break
            account_analytic_id = line.product_id.product_tmpl_id.categ_id.with_context(
                force_company=company_id).property_category_account_analytic_id
            line.account_analytic_id = account_analytic_id.id if account_analytic_id else False

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account')

    @api.constrains('product_id')
    def get_account_analytic(self):
        for line in self:
            if not line.product_id:
                break
            company_id = self.company_id.id if self.company_id else self.env.company
            if not line.product_id or not line.product_id.product_tmpl_id or not line.product_id.product_tmpl_id.categ_id:
                break
            account_analytic_id = line.product_id.product_tmpl_id.categ_id.with_context(
                force_company=company_id).property_category_account_analytic_id
            line.account_analytic_id = account_analytic_id.id if account_analytic_id else False


class APIAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    booking_name = fields.Char(string='Tên Booking')
    source_name = fields.Char(string='Nguồn Booking')
    user_name = fields.Char(string='Tư vấn viên')

    @api.constrains('product_id')
    def get_account_analytic(self):
        for line in self.filtered(lambda m:m.product_id):
            company_id = self.company_id.id if self.company_id else self.env.company
            if not line.product_id or not line.product_id.product_tmpl_id or not line.product_id.product_tmpl_id.categ_id:
                break
            account_analytic_id = line.product_id.product_tmpl_id.categ_id.with_context(
                force_company=company_id).property_category_account_analytic_id
            line.analytic_account_id = account_analytic_id.id if account_analytic_id else False

    @api.model_create_multi
    def create(self, vals):
        #Todo: Onnet xem lại hàm này
        res = super(APIAccountMoveLine, self).create(vals)
        if res.sale_line_ids:
            crm_ids = res.sale_line_ids.mapped('crm_line_id.crm_id')
            consultant_ids = res.sale_line_ids.mapped('crm_line_id.consultants_1')
            res.write({
                'booking_name': crm_ids[0].name if crm_ids else '',
                'source_name': res.move_id.source_id.name if res.move_id.source_id else '',
                'user_name': consultant_ids[0].partner_id.name if consultant_ids else '',
            })
        return res




