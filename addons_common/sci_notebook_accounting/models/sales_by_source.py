from odoo import fields, models, api, _
import json
from lxml import etree
from odoo.exceptions import UserError, ValidationError


class SalesBySource(models.Model):
    _name = 'sales.by.source'
    _inherit = ['mail.activity.mixin', 'mail.thread', 'rating.parent.mixin']
    _description = 'Doanh số theo nguồn'

    name = fields.Char(string='Mã phiếu')
    state = fields.Selection(selection=[('draft', 'Draft'), ('wait', 'Chờ xử lý'), ('posted', 'Posted'), ('locked', 'Khóa sổ'), ('cancel', 'Cancelled')],
                             string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')
    sale_source_line_id = fields.One2many(comodel_name='sale.by.source.line', inverse_name='sale_source_id', string='Doanh số theo nguồn')
    sale_service_line_id = fields.One2many(comodel_name='sale.by.source.line', inverse_name='sale_service_id', string='Doanh số theo dịch vụ')
    sale_cost_line_id = fields.One2many(comodel_name='sale.by.source.line', inverse_name='sale_cost_id', string='Doanh số theo nhóm nguồn')
    sale_revenue_line_id = fields.One2many(comodel_name='sale.by.source.line', inverse_name='sale_revenue_id', string='Doanh số theo nguồn bán')

    date = fields.Date(string='Ngày ghi nhận', default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one(comodel_name='res.users', readonly=True, store=True, string='Người báo cáo', default=lambda self: self.env.user)
    company_id = fields.Many2one(comodel_name='res.company', string='Chi nhánh', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])
    brand_id = fields.Many2one(comodel_name='res.brand', string='Thương hiệu', readonly=True, store=True, related='company_id.brand_id')

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, string='Đơn vị tiền tệ', readonly=True, required=True)
    amount_subtotal_source = fields.Monetary(string='Tổng tiền theo nguồn', store=True, compute='_get_amount_source_subtotal')
    amount_subtotal_service = fields.Monetary(string='Tổng tiền theo dịch vụ', store=True, compute='_get_amount_service_subtotal')
    amount_subtotal_cost = fields.Monetary(string='Tổng tiền theo chi phí', store=True, compute='_get_amount_cost_subtotal')
    amount_subtotal_revenue = fields.Monetary(string='Tổng tiền theo nguồn bán', store=True, compute='_get_amount_revenue_subtotal')

    type = fields.Selection(string='Loại doanh thu', selection=[('01', 'Doanh thu thực hiện'), ('02', 'Doanh thu kế hoạch'), ('03', 'Chi phí phân bổ')])
    is_automatic = fields.Boolean(string='Là phân bộ tự động', default=False)

    # _sql_constraints = [
    #     ('unique_date_type', 'UNIQUE(date,type,user_id,company_id)', 'Đã tồn tại bản ghi ngày này.')
    # ]

    @api.constrains('date', 'type', 'user_id', 'company_id', 'state')
    def _check_record(self):
        self.env.cr.execute(""" 
            SELECT date, type, user_id, company_id, count(id) as check
            FROM sales_by_source
            WHERE state != 'cancel'
            GROUP BY date, type, user_id, company_id
        ;""")
        if any(check[4] > 1 for check in self._cr.fetchall()):
            raise ValidationError(_("Đã tồn tại bản ghi cùng ngày."))

    def get_data_sale_data(self):
        # result = {'category_source_id': 0, 'source_id': 0, 'amount': 0}
        result = dict()
        result_list = dict()

        for rec in self:
            if rec.date and rec.company_id:
                payment = self.env['account.payment'].search([('state', '=', 'posted'), ('payment_date', '=', rec.date), ('company_id', '=', rec.company_id.id)])
                for pay in payment:

                    amount = pay.amount_vnd
                    booking = pay.crm_id

                    source_id = booking.source_id
                    category_source_id = booking.category_source_id

                    str_key = str(source_id.id) + '-' + str(category_source_id.id)
                    val = {'category_source_id': category_source_id.id, 'source_id': source_id.id, 'amount': amount}

                    if str_key not in result.keys():
                        result[str_key] = val
                    else:
                        for key in result.keys():
                            if key == str_key:
                                result[key]['amount'] += amount
            for key, value in result:
                result_list.append(value)

        return result_list

    @api.depends('sale_source_line_id')
    def _get_amount_source_subtotal(self):
        for rec in self:
            lines = rec.sale_source_line_id
            amount_subtotal_source = 0.0
            for element in lines:
                if element.is_refund:
                    amount_source = -1 * element.amount_source
                else:
                    amount_source = element.amount_source
                amount_subtotal_source += amount_source

            rec.amount_subtotal_source = amount_subtotal_source

    @api.depends('sale_service_line_id')
    def _get_amount_service_subtotal(self):
        for rec in self:
            lines = rec.sale_service_line_id
            amount_subtotal_service = 0.0
            for element in lines:
                if element.is_refund:
                    amount_service = -1 * element.amount_service
                else:
                    amount_service = element.amount_service
                amount_subtotal_service += amount_service

            rec.amount_subtotal_service = amount_subtotal_service

    @api.depends('sale_cost_line_id')
    def _get_amount_cost_subtotal(self):
        for rec in self:
            lines = rec.sale_cost_line_id
            amount_subtotal_cost = 0.0
            for element in lines:
                if element.is_refund:
                    amount_cost = -1 * element.amount_cost
                else:
                    amount_cost = element.amount_cost
                amount_subtotal_cost += amount_cost

            rec.amount_subtotal_cost = amount_subtotal_cost

    @api.depends('sale_revenue_line_id')
    def _get_amount_revenue_subtotal(self):
        for rec in self:
            lines = rec.sale_revenue_line_id
            amount_subtotal_revenue = 0.0
            for element in lines:
                if element.is_refund:
                    amount_revenue = -1 * element.amount_revenue
                else:
                    amount_revenue = element.amount_revenue
                amount_subtotal_revenue += amount_revenue

            rec.amount_subtotal_revenue = amount_subtotal_revenue

    def action_confirm(self):
        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date))
            self.name = self.env['ir.sequence'].next_by_code('sales.by.source', sequence_date=seq_date) or _('New')
            self.write({'state': 'wait'})

    def unlink(self):
        if self.state == 'draft':
            return super(SalesBySource, self).unlink()
        else:
            raise ValidationError(_("Không thể xóa phiếu đã được xác nhận!"))

    def action_draft(self):
        self.ensure_one()
        self.name = _('New')
        self.state = 'draft'

    def accounting_action_confirm(self):
        self.ensure_one()
        self.state = 'posted'

    def accounting_manager_return_action_wait(self):
        self.ensure_one()
        self.state = 'wait'

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_locked(self):
        for rec in self:
            if rec.state == 'posted':
                rec.write({'state': 'locked'})

    def action_unlocked(self):
        for rec in self:
            if rec.state == 'locked':
                rec.write({'state': 'posted'})

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SalesBySource, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])

        if view_type == 'form':
            for node in doc.xpath("//field"):
                node.set("attrs", "{'readonly':[('state','!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = "[('state','!=','draft')]"
                node.set('modifiers', json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class SalesBySourceLine(models.Model):
    _name = 'sale.by.source.line'
    _description = 'Line doanh số theo nguồn'

    def get_selection_service_category(self):
        service_category = self.env['sh.medical.health.center.service.category'].sudo().search_read([], ['name'], order='name')
        result = [(element['name'].strip(), element['name'].strip()) for element in service_category] + [('Sản phẩm', 'SẢN PHẨM'), ('none', '')]
        return result

    sale_source_id = fields.Many2one(comodel_name='sales.by.source', string='Theo nguồn marketing')
    sale_service_id = fields.Many2one(comodel_name='sales.by.source', string='Theo dịch vụ')
    sale_cost_id = fields.Many2one(comodel_name='sales.by.source', string='Theo chi phí')
    sale_revenue_id = fields.Many2one(comodel_name='sales.by.source', string='Theo nguồn doanh thu')

    category_source = fields.Many2one(comodel_name='crm.category.source', string='Nhóm nguồn')
    category_source_utm = fields.Many2one(comodel_name='utm.source', string='Nguồn', domain="[('category_id', '=', category_source)]")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id, string='Đơn vị tiền tệ', readonly=True, required=True)

    amount_source = fields.Monetary(string='Tổng tiền theo nguồn')
    amount_service = fields.Monetary(string='Tổng tiền theo dịch vụ')
    amount_cost = fields.Monetary(string='Tổng tiền theo hạng mục chi phí')
    amount_revenue = fields.Monetary(string='Tổng tiền theo nguồn bán')
    note = fields.Char(string='Ghi chú')

    service_type = fields.Selection([('01', 'Spa'), ('02', 'Laser'), ('03', 'Nha'), ('04', 'Phẫu thuật'), ('05', 'Chi phí khác')], string='Loại dịch vụ')
    # service_catge = fields.Many2one(comodel_name='sh.medical.health.center.service.category', string='Nhóm dịch vụ')
    service_catge = fields.Selection(selection=get_selection_service_category, default='none', string='Nhóm dịch vụ')

    cost_source_ids = fields.Many2one(comodel_name='source.config.account', string='Nguồn/khối')
    cost_items_ids = fields.Many2one(comodel_name='cost.item.config', string='Nhóm chi phí', domain="[('source', '=', cost_source_ids)]")
    revenue_ids = fields.Many2one(comodel_name='config.source.revenue', string='Nhóm nguồn doanh thu')

    # Nhóm nguồn kiểu text
    text_category_source = fields.Char(string='Nhóm nguồn kế hoạch', compute='set_text_category_source', store=True)
    # Nguồn kiểu text
    text_category_source_utm = fields.Char(string='Nguồn kế hoạch', compute='set_text_category_source_utm', store=True)

    plan_cost_id = fields.Many2one(comodel_name='plan.cost', string='Chi phí kế hoạch')

    is_refund = fields.Boolean(string='Là hoàn tiền', default=False)

    @api.depends('category_source')
    def set_text_category_source(self):
        for rec in self:
            if rec.category_source:
                rec.text_category_source = rec.category_source.name
            else:
                rec.text_category_source = None

    @api.depends('category_source_utm')
    def set_text_category_source_utm(self):
        for rec in self:
            if rec.category_source_utm:
                rec.text_category_source_utm = rec.category_source_utm.name
            else:
                rec.text_category_source_utm = None


class ServiceCategoryNoteAccount(models.Model):
    _inherit = 'sh.medical.health.center.service.category'

    def name_get(self):
        if self._context.get('note_accounting'):
            result = []
            for rec in self:
                name = ' - '.join((rec.code, rec.name))
                result.append((rec.id, name))
            return result
        else:
            return super(ServiceCategoryNoteAccount, self).name_get()
