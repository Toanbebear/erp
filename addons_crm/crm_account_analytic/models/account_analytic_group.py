from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _


class AccountAnalyticGroup(models.Model):
    _inherit = 'account.analytic.group'

    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    tag_id = fields.Many2one('account.analytic.tag', string='Từ khoá khoản mục', store=True)
    percentage = fields.Float(string='Tỉ lệ (%)', digits='PERCENTAGE')
    start_date = fields.Date(string='Từ ngày', readonly=True)
    end_date = fields.Date(string='Đến ngày', readonly=True)
    update_date = fields.Datetime(string='Thời gian cập nhật tỉ lệ', readonly=True)
    note = fields.Text(string='Ghi chú')
    parent_id = fields.Many2one('account.analytic.group', string="Nhóm cấp trên", ondelete='cascade', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    def update_rate(self):
        self.ensure_one()
        view = self.env.ref('crm_account_analytic.account_analytic_group_update_rate_view')
        return {
            'name': _('Cập nhật tỉ lệ phân bổ'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.group.update.rate.wizard',
            'view_id': view.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.constrains('children_ids')
    def check_children_total(self):
        for record in self:
            total_percent = sum(record.children_ids.mapped("percentage"))
            if int(total_percent) != 100:
                raise ValidationError(_("Tổng tỉ lệ phân bổ phải bằng 100%"))

    @api.onchange('percentage')
    def on_change_allocation_rate(self):
        self.ensure_one()
        self.update_date = fields.Date.today()

