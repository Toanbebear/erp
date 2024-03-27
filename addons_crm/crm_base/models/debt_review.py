from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class DebtReview(models.Model):
    _name = 'crm.debt.review'
    _description = 'Debt Review'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'money.mixin']

    name = fields.Text('Lý do nợ', tracking=True)
    order_id = fields.Many2one('sale.order', string='Order', tracking=True)
    booking_id = fields.Many2one('crm.lead', string='Booking', tracking=True)
    stage = fields.Selection([('offer', 'Đề xuất'), ('approve', 'Approve'), ('refuse', 'Refuse')], string='Stage',
                             default='offer', tracking=True)
    company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.user.company_id.id,
                                 tracking=True)
    partner_id = fields.Many2one('res.partner', string='Đối tác', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', related='order_id.currency_id',
                                  tracking=True)
    amount_total = fields.Monetary(string='Tổng tiền', compute='compute_amount_total', store=True, tracking=True)
    amount_owed = fields.Monetary('Số tiền nợ', tracking=True)
    paid = fields.Boolean('Đã trả nợ', tracking=True)
    user_approve = fields.Many2one('res.users', 'Người duyệt nợ', tracking=True)
    date_approve = fields.Datetime('Ngày duyêt', tracking=True)
    paid = fields.Boolean('Đã trả nợ', tracking=True)
    color = fields.Integer('color')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.booking_id = False
        if self.partner_id:
            return {'domain': {'booking_id': [
                ('id', 'in', self.env['crm.lead'].search(
                    [('type', '=', 'opportunity'), ('partner_id', '=', self.partner_id.id)]).ids)]}}

    @api.depends('order_id')
    def compute_amount_total(self):
        for record in self:
            record.amount_total = 0
            if record.order_id:
                record.amount_total = record.order_id.amount_total - record.order_id.amount_remain - record.order_id.amount_owed

    def action_paid(self):
        self.paid = True
        self.order_id.amount_owed -= self.amount_owed
        self.color = 0

    def set_approve(self):
        if (self.debt_type == 'service') and self.crm_line:
            if self.crm_line.amount_owed != 0:
                raise ValidationError('Không thể duyệt nợ cho dịch vụ này! \n Lí do: Dịch vụ đã được duyệt nợ trước đó rồi!')
        self.stage = 'approve'
        self.order_id.sudo().write({
            'debt_review_id': [(4, self.id)]
        })
        self.date_approve = fields.Datetime.now()
        self.user_approve = self.env.user.id

    def set_refuse(self):
        if self.stage == 'approve' and not self.env.user.has_group('crm_base.branch_management'):
            raise ValidationError('Khi phiếu đã được duyệt, chỉ GĐCN mới có quyền hủy phiếu!')
        elif self.stage == 'refuse':
            raise ValidationError('Phiếu này đã ở trạng thái hủy rồi!')
        else:
            self.stage = 'refuse'
