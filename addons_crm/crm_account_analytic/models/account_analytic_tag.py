from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _

SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'), ('ChiPhi', 'Chi phí khác')]
dict_type = dict((key, value) for key, value in SERVICE_HIS_TYPE)


class AccountAnalyticTag(models.Model):
    _inherit = 'account.analytic.tag'

    def update_rate(self):
        self.ensure_one()
        view = self.env.ref('crm_account_analytic.account_analytic_tag_update_rate_view')
        return {
            'name': _('Cập nhật tỉ lệ phân bổ'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.tag.update.rate.wizard',
            'view_id': view.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.constrains('analytic_distribution_ids')
    def check_children_total(self):
        for record in self:
            total_percent = sum(record.analytic_distribution_ids.mapped("percentage"))
            if int(total_percent) != 0 and int(total_percent) != 100:
                raise ValidationError(_("Tổng tỉ lệ phân bổ phải bằng 100%"))


class AccountAnalyticTagDepartment(models.Model):
    _name = 'account.analytic.tag.department'
    _description = 'Account analytic tag department'

    department = fields.Selection(SERVICE_HIS_TYPE, string='Phòng ban')
    allocation_rate = fields.Float(string='Tỉ lệ (%)', digits='ALLOCATION_RATE')
    update_date = fields.Datetime(string='Thời gian cập nhật tỉ lệ', readonly=True)
    start_date = fields.Date(string='Từ ngày', readonly=True)
    end_date = fields.Date(string='Đến ngày', readonly=True)
    note = fields.Text(string='Ghi chú')


class AccountAnalyticDistribution(models.Model):
    _inherit = 'account.analytic.distribution'

    account_id = fields.Many2one(required=False)
    department = fields.Selection(SERVICE_HIS_TYPE, string='Phòng ban', required=True)
    start_date = fields.Date(string='Từ ngày')
    end_date = fields.Date(string='Đến ngày')
    note = fields.Text(string='Ghi chú')
    percentage = fields.Float(readonly=False)

