from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _


class CostAllocation(models.Model):
    _name = 'cost.allocation'
    _description = 'Phân bổ chi phí'

    name = fields.Char(string='Số phân bổ', readonly=True, copy=False)
    ref = fields.Char(string='Mã phiếu')
    # create_date = fields.Date(string="Ngày kế toán")
    date = fields.Date(string="Ngày kế toán", required=True)
    account_journal_id = fields.Many2one('account.journal', string='Sổ nhật ký', required=True)
    account_move_ids = fields.Many2many('account.move', string='Bút toán', required=True,
                                        domain="[('company_id', '=', company_id)]")
    account_analytic_group_id = fields.Many2one('account.analytic.group', string='Nhóm tài khoản phân tích',
                                                required=True)

    cost_allocation_select_line_ids = fields.One2many('cost.allocation.select.line', 'cost_allocation_id',
                                                      string='Lựa chọn phân bổ')
    account_move_allocation_line_ids = fields.One2many('account.move.allocation.line', 'cost_allocation_id',
                                                       string='Bút toán')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    content = fields.Char(string='Nội dung')
    state = fields.Selection([('draft', 'Nháp'), ('done', 'Đã phân bổ')], readonly=True, default='draft', copy=False,
                             string="Status")
    check_company_access = fields.Boolean(compute='compute_company_access')
    auto_percentage = fields.Boolean(string='Tự động tính tỉ lệ', default=True)
    account_move_count = fields.Integer('Account move', compute='compute_account_move_count')

    def compute_account_move_count(self):
        for rec in self:
            rec.account_move_count = rec.env['account.move'].sudo().search_count(
                [('cost_allocation_id', '=', rec.id)])

    def open_allocation_account_move(self):
        self.ensure_one()
        context = {
            'create': False,
        }
        return {
            'name': _('Account move'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('cost_allocation_id', '=', self.id)],
            'context': context
        }

    @api.depends_context('allowed_companies')
    def compute_company_access(self):
        for rec in self:
            allowed_companies = rec.env.context.get('allowed_company_ids', False)
            companies = rec.env['res.company'].search([('id', 'in', allowed_companies)])
            if companies:
                if True in companies.mapped('x_is_corporation'):
                    check = True
                else:
                    check = False
            else:
                check = True
            rec.check_company_access = check

    @api.constrains('cost_allocation_select_line_ids')
    def validate_credit_total(self):
        select_line_ids = self.cost_allocation_select_line_ids
        account_move_ids = self.account_move_allocation_line_ids
        total_allocation = sum(select_line_ids.mapped('credit'))
        total_cost = sum(account_move_ids.mapped('credit'))
        if total_cost != total_allocation:
            raise ValidationError("Tổng phân bổ chưa bằng tổng chi phí")

    @api.onchange('account_move_ids')
    def onchange_account_move_ids(self):
        # self.create_date = self.account_move_ids.search([], limit=1).date
        self.account_move_allocation_line_ids.unlink()
        self.write({'account_move_allocation_line_ids': [(5, 0, 0)]})
        for rec in self:
            rec.write({'account_move_allocation_line_ids': self.create_account_move_allocation_line_ids()})

    def create_account_move_allocation_line_ids(self):
        account_move_allocation_line_ids = [(5, 0, 0)]
        for line in self.account_move_ids.line_ids:
            sci_account_id = self.env['account.account.equivalent'].sudo().search([
                ('account_equivalent_ids', '=', line.account_id.id),
            ], limit=1).account_sci_id

            account_move_allocation_line_ids.append((0, 0, {
                'cost_allocation_id': self.id,
                'account_id': sci_account_id.id,
                'debit': line.debit,
                'credit': line.credit
            }))
        return account_move_allocation_line_ids

    # Hiển thi checkbox
    @api.onchange('account_analytic_group_id')
    def onchange_account_analytic_group_id(self):
        self.cost_allocation_select_line_ids = [(5, 0, 0)]
        self.sudo().create_cost_allocation_select_line_ids(self.account_analytic_group_id)

    def create_cost_allocation_select_line_ids(self, account_analytic_group_id):
        for group_line_id in account_analytic_group_id.sudo().children_ids:
            cost_allocation_line = {
                'cost_allocation_id': self.id,
                'name': group_line_id.name,
                'company_id': group_line_id.company_id.id,
                'account_analytic_group_id': group_line_id.id,
                'choice': True,
            }
            if group_line_id.sudo().parent_id.sudo().parent_id:
                self.env['cost.allocation.select.line'].sudo().create(cost_allocation_line)
            if group_line_id.children_ids:
                self.sudo().create_cost_allocation_select_line_ids(group_line_id)

    def reload(self):
        self.cost_allocation_select_line_ids = [(5, 0, 0)]
        self.create_cost_allocation_select_line_ids(self.account_analytic_group_id)

    def write(self, vals):
        res = super(CostAllocation, self).write(vals)
        return res

    def unlink(self):
        if self.state == 'done':
            raise ValidationError('Không thể xóa khi đã vào sổ')
        res = super(CostAllocation, self).unlink()
        return res

    # lấy nhật ký tương đương
    def get_journal_equivalent(self, sci_journal, company_id):
        journal_equivalent_ids = self.env['account.journal.equivalent'].sudo().search([
            ('account_sci_id', '=', sci_journal.id),
        ], limit=1).account_equivalent_ids.filtered(lambda x: x.company_id.id == company_id.id)
        if len(journal_equivalent_ids) == 0:
            raise ValidationError('Chưa cấu hình nhật kí tương đương: ' + sci_journal.name)
        else:
            return journal_equivalent_ids

    # lấy tai khoan tương đương
    def get_account_equivalent(self, sci_account, company_id):
        account_equivalent_ids = self.env['account.account.equivalent'].sudo().search([
            ('account_sci_id', '=', sci_account.id),
        ], limit=1).account_equivalent_ids.filtered(lambda x: x.company_id.id == company_id.id)
        if len(account_equivalent_ids) == 0:
            raise ValidationError('Chưa cấu hình tài khoản tương đương: ' + sci_account.name)
        else:
            return account_equivalent_ids

    def action_confirm(self):
        select_line_ids = self.cost_allocation_select_line_ids.filtered(lambda x: x.credit != 0)
        account_move_ids = self.account_move_allocation_line_ids
        if not account_move_ids or len(account_move_ids) == 0:
            raise ValidationError('Chưa có bút toán phân bổ')

        # Tạo bút toán và phân bổ theo lựa chọn
        for cost_allocation in select_line_ids:
            # lấy nhật ký tương đương
            journal_id = self.get_journal_equivalent(self.account_journal_id, cost_allocation.company_id).ids[0]
            account_move_line_vals = []
            total_debit = 0
            total_credit = 0
            for move_line in account_move_ids:
                # lấy tai khoan tương đương
                account_id = self.get_account_equivalent(move_line.account_id, cost_allocation.company_id).ids[0]
                # tính nợ có theo tỷ lệ phân bổ
                percentage = cost_allocation.percentage
                debit = (move_line.debit * percentage) / 100
                if move_line.id == account_move_ids.filtered(lambda x: x.debit)[-1].id:
                    debit = cost_allocation.credit - total_debit
                credit = (move_line.credit * percentage) / 100
                if move_line.id == account_move_ids.filtered(lambda x: x.credit)[-1].id:
                    credit = cost_allocation.credit - total_credit

                tag_id = cost_allocation.account_analytic_group_id.tag_id.ids
                account_move_line_vals.append((0, 0, {
                    'account_id': account_id,
                    'analytic_tag_ids': tag_id,
                    'debit': debit,
                    'credit': credit,
                }))
                total_debit += debit
                total_credit += credit
            move_vals = {
                'date': self.date,
                'ref': self.ref,
                'lydo': self.content,
                'cost_allocation_id': self.id,
                'journal_id': journal_id,
                'currency_id': self.account_journal_id.currency_id.id,
                'line_ids': account_move_line_vals,
            }
            self.env['account.move'].sudo().create(move_vals)

            if self._context.get('name', _('New')) == _('New'):
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date))
                self.name = self.env['ir.sequence'].next_by_code('cost.allocation', sequence_date=seq_date) or _('New')
                self.write({'state': 'done'})

    # Kiểm tra quyền truy cập của công ty hoạt động
    # @api.model
    # def check_access_rule(self, operation):
    #     if self.check_company_access is False:
    #         raise ValidationError('Chỉ được phân bổ chi phí ở SCIGROUP')
    #     else:
    #         return super(CostAllocation, self).check_access_rule(operation)

    # Kiểm tra xem đã phân bổ cho nhóm và bút toán này chưa?
    @api.constrains('account_move_allocation_line_ids', 'account_move_ids')
    def check_debit_credit_total(self):
        for rec in self:
            if rec.account_move_allocation_line_ids:
                total_account_debit = sum(rec.account_move_ids.line_ids.mapped('debit'))
                total_debit = sum(rec.account_move_allocation_line_ids.mapped('debit'))
                total_credit = sum(rec.account_move_allocation_line_ids.mapped('credit'))
                if total_account_debit != total_debit:
                    raise ValidationError('Tổng nợ/có chưa bằng tổng nợ/có của các bút toán phân bổ!')
                if total_debit != total_credit:
                    raise ValidationError(_('Tổng nợ chưa bằng tổng có!'))
                elif total_credit == 0 or total_credit == 0:
                    raise ValidationError('Tổng nợ hoặc có phải khác 0')
            else:
                raise ValidationError(_('Chưa có bút toán phân bổ!'))


class AccountMoveAllocationLine(models.Model):
    _name = 'account.move.allocation.line'
    _description = 'Bút toán phân bổ'

    cost_allocation_id = fields.Many2one('cost.allocation', 'Phân bổ chi phí')
    account_id = fields.Many2one('account.account', string='Account', index=True, required=True, ondelete="cascade",
                                 domain=[('deprecated', '=', False)])
    debit = fields.Monetary(string='Debit', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Credit', default=0.0, currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id',
                                          readonly=True,
                                          help='Utility field to express amount currency')
    company_id = fields.Many2one('res.company', string='Company', related='cost_allocation_id.company_id', store=True)

    def create(self, vals):
        res = super(AccountMoveAllocationLine, self).create(vals)
        return res


class CostAllocationLine(models.Model):
    _name = 'cost.allocation.select.line'
    _description = 'Lựa chọn phân bổ'

    name = fields.Text(string='Tên nhóm phân bổ')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id')
    company_id = fields.Many2one('res.company', string='Công ty')
    percent_brand = fields.Float(string='Tỷ trọng theo thương hiệu',
                                 related='account_analytic_group_id.parent_id.percentage')
    percent_company = fields.Float(string='Tỷ trọng theo công ty', related='account_analytic_group_id.percentage')
    percentage = fields.Float(string='Tỉ lệ tự động', digits='PERCENTAGE', compute='compute_percentage')
    credit_manual = fields.Monetary(string='Số tiền chỉnh tay', currency_field='company_currency_id')
    auto_percentage = fields.Boolean(related='cost_allocation_id.auto_percentage')
    credit = fields.Monetary(string='Số tiền phân bổ', default=0.0,
                             currency_field='company_currency_id',
                             compute='compute_credit_allocation')
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id',
                                          readonly=True,
                                          help='Utility field to express amount currency')
    cost_allocation_id = fields.Many2one('cost.allocation', 'Phân bổ chi phí')
    account_analytic_group_id = fields.Many2one('account.analytic.group', string='Nhóm tài khoản phân tích')
    account_analytic_group_parent_id = fields.Many2one('account.analytic.group', related='account_analytic_group_id.parent_id', string='Nhóm tài khoản phân tích')
    choice = fields.Boolean(string='Phân bổ', default=False, store=True)

    def create(self, vals):
        res = super(CostAllocationLine, self).create(vals)
        return res

    @api.depends('percentage', 'credit_manual', 'auto_percentage')
    def compute_credit_allocation(self):
        for rec in self:
            if rec.auto_percentage is True:
                account_move_line_ids = rec.cost_allocation_id.account_move_allocation_line_ids
                if account_move_line_ids:
                    sum_credit = sum(line.credit for line in account_move_line_ids)
                    rec.credit = (sum_credit * rec.percentage) / 100
            else:
                rec.credit = rec.credit_manual

    @api.depends('cost_allocation_id', 'choice', 'auto_percentage', 'credit_manual')
    def compute_percentage(self):
        for rec in self:
            if rec.auto_percentage is True:
                if rec.choice is False:
                    percentage = 0
                else:
                    allocation = rec.cost_allocation_id.cost_allocation_select_line_ids.filtered(lambda x:
                                                                                                 x.choice is True
                                                                                                 and x.percent_brand != 0
                                                                                                 and x.percent_company != 0)
                    if allocation:
                        brands = allocation.mapped('account_analytic_group_parent_id')
                        sum_brands = sum(brand.percentage for brand in brands)
                        parent_id = rec.account_analytic_group_parent_id
                        allocation = allocation.filtered(lambda x:
                                                         x.account_analytic_group_parent_id.id == parent_id.id
                                                         and x.percent_brand != 0
                                                         and x.percent_company != 0)
                        companies = allocation.mapped('account_analytic_group_id')
                        sum_companies = sum(company.percentage for company in companies)
                        if sum_brands > 0 and sum_companies > 0:
                            percentage = round((rec.percent_company/sum_companies)*(rec.percent_brand/sum_brands)*100, 2)
                        else:
                            percentage = 0
                    else:
                        percentage = 100
            elif rec.auto_percentage is False and rec.credit_manual:
                percentage = round(rec.credit_manual / sum(rec.cost_allocation_id.account_move_allocation_line_ids.mapped('credit')) * 100, 2)
            else:
                percentage = 0
            # Đảm bảo tổng tỷ lệ luôn = 100
            allocation = rec.cost_allocation_id.cost_allocation_select_line_ids.filtered(lambda x:
                                                                                         x.choice is True
                                                                                         and x.percent_brand != 0
                                                                                         and x.percent_company != 0)
            if allocation and rec.id == allocation[-1].id:
                percentage = 100 - sum(allocation.mapped('percentage'))

            rec.update({
                'percentage': percentage
            })

