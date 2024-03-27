from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from lxml import etree
import json


class CrmComplain(models.Model):
    _name = 'crm.complain'
    _description = 'Crm Complain'

    name = fields.Char('Name')
    complain_group_id = fields.Many2one('crm.complain.group', string='Nhóm khiếu nại')
    brand_id = fields.Many2one('res.brand', string='Brand')
    # company_ids = fields.Many2many('res.company', domain="[('brand_id','in',brand_ids)]")
    department_ids = fields.Many2many('hr.department', string='Department')
    brand_sla_urgent = fields.Float('SLA Brand - Urgent')
    brand_sla_high = fields.Float('SLA Brand - High')
    brand_sla_normal = fields.Float('SLA Brand - Normal')
    brand_sla_low = fields.Float('SLA Brand - Low')
    cskh_sla_urgent = fields.Float('SLA CSKH - Urgent')
    cskh_sla_high = fields.Float('SLA CSKH - High')
    cskh_sla_normal = fields.Float('SLA CSKH - Normal')
    cskh_sla_low = fields.Float('SLA CSKH - Low')
    company_sla_urgent = fields.Float('SLA Company - Urgent')
    company_sla_high = fields.Float('SLA Company - High')
    company_sla_normal = fields.Float('SLA Company - Normal')
    company_sla_low = fields.Float('SLA Company - Low')
    time_urgent = fields.Selection([('hc', 'HC'), ('all', '24/24')], string='Processing Time - Urgent')
    time_high = fields.Selection([('hc', 'HC'), ('all', '24/24')], string='Processing Time - High')
    time_normal = fields.Selection([('hc', 'HC'), ('all', '24/24')], string='Processing Time - Normal')
    time_low = fields.Selection([('hc', 'HC'), ('all', '24/24')], string='Processing Time - Low')

    @api.onchange('brand_id')
    def onchange_brand_id(self):
        if self.brand_id:
            self.department_ids = False
            company_ids = self.env['res.company'].search([('brand_id', '=', self.brand_id.id)])
            return {'domain': {'department_ids': [
                ('id', 'in', self.env['hr.department'].search(
                    [('company_id', 'in', company_ids.ids)]).ids)]}}


class CrmComplainGroup(models.Model):
    _name = 'crm.complain.group'
    _description = 'Crm Complain Group'

    name = fields.Char('Name')


class CaseCrm(models.Model):
    _name = 'crm.case'
    _description = 'Case Crm'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', tracking=True)
    # subject_case = fields.Char('Subject')
    code = fields.Char('ID case', tracking=True)
    type_case = fields.Selection(
        [('complain', 'Complain'), ('warning', 'Warning'), ('gop_y', 'Góp ý - Phản ánh')],
        string='Type case', tracking=True)
    create_by = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, tracking=True)
    department_create_by = fields.Many2one('hr.department', string='Phòng ban', tracking=True, compute='set_department', store=True)
    create_on = fields.Datetime('Create on', default=fields.Datetime.now(), tracking=True)
    brand_id = fields.Many2one('res.brand', string='Brand', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', tracking=True)
    user_id = fields.Many2one('res.users', string='Handler', tracking=True, domain="[('company_id', '=', company_id)]")
    start_date = fields.Datetime('Start date', default=datetime.now())
    end_date = fields.Datetime('End date')
    duration = fields.Char('Duration', compute='set_duration')
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    phone = fields.Char('Phone', tracking=True)
    country_id = fields.Many2one('res.country', string='Country', related='partner_id.country_id', tracking=True)
    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id', tracking=True)
    street = fields.Char('Street', related='partner_id.street', tracking=True)
    account_facebook = fields.Char('Account facebook', tracking=True)
    booking_id = fields.Many2one('crm.lead', string='Booking', tracking=True)
    phone_call_id = fields.Many2one('crm.phone.call', string='Phone call', tracking=True)
    documents = fields.Many2many('ir.attachment', string="Tệp đính kèm", copy=False, tracking=True)
    crm_content_complain = fields.One2many('crm.content.complain', 'crm_case', string='Content Complain')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CaseCrm, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone']:
                fields[field_name]['exportable'] = False

        return fields

    @api.depends('create_by')
    def set_department(self):
        for rec in self:
            rec.department_create_by = False
            if rec.create_by:
                employee_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', rec.create_by.id)])
                rec.department_create_by = employee_id.department_id.id

    @api.constrains('start_date', 'start_date')
    def check_date(self):
        """ Check that the total percent is not bigger than 100.0 """
        for rec in self:
            if rec.end_date and rec.start_date >= rec.end_date:
                raise ValidationError(
                    _('The start date must not be greater than or coincide with the end date !'))

    @api.depends('start_date', 'end_date')
    def set_duration(self):
        for rec in self:
            rec.duration = 'Received'
            if rec.start_date and rec.end_date:
                rec.duration = (rec.end_date - rec.start_date)
            else:
                rec.duration = '00:00:00'

    @api.onchange('end_date')
    def set_stage_done(self):
        for rec in self:
            if rec.end_date:
                rec.stage_id = 'done'
            else:
                rec.stage_id = 'processing'

    @api.model
    def create(self, vals):
        res = super(CaseCrm, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code('crm.case')
        return res

    @api.onchange('phone')
    def check_partner(self):
        if self.phone:
            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            if partner:
                self.partner_id = partner.id
                self.country_id = partner.country_id.id
                self.state_id = partner.state_id.id
                self.street = partner.street
                self.account_facebook = partner.acc_facebook

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CaseCrm, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                   submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field[@name='brand_id']"):
                node_domain = "[('id', 'in', %s)]" % self.env.user.company_ids.mapped('brand_id').ids
                node.set("domain", node_domain)
                modifiers = json.loads(node.get("modifiers"))
                modifiers['domain'] = node_domain
                node.set("modifiers", json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class CrmContentComplain(models.Model):
    _name = 'crm.content.complain'
    _description = 'Crm Content Complain'
    _rec_name = 'complain_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    crm_case = fields.Many2one('crm.case', string='Case khiếu nại')
    type_crm_case = fields.Selection(related='crm_case.type_case', store=True)
    code_crm_case = fields.Char(related='crm_case.code', store=True)
    brand_id = fields.Many2one(related='crm_case.brand_id', store=True)
    company_id = fields.Many2one(related='crm_case.company_id', store=True)
    partner_id = fields.Many2one(related='crm_case.partner_id', store=True)
    phone_partner = fields.Char(related='crm_case.phone', store=True)
    booking_id = fields.Many2one(related='crm_case.booking_id', store=True)
    complain_group_id = fields.Many2one('crm.complain.group', string='Complain Group')
    complain_id = fields.Many2one('crm.complain', string='Khiếu nại chi tiết')
    receive_source = fields.Selection(
        [('call', 'Call center'), ('email', 'Email'), ('inbox', 'Inbox'), ('directly', 'Directly'),
         ('comment', 'Comment'), ('zalo', 'Zalo')],
        string='Receive source', tracking=True)
    product_ids = fields.Many2many('product.product', string='Dịch vụ')
    department_ids = fields.Many2many('hr.department', string='Khiếu nại phòng ban')
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High'), ('3', 'Urgency')], string='Priority')
    desc = fields.Text('Phản ánh khách hàng')
    solution = fields.Text('Giải pháp')
    stage = fields.Selection(
        [('new', 'New'), ('processing', 'Processing'), ('finding', 'Finding more Information'),
         ('waiting_response', 'Waiting response'), ('need_to_track', 'Need to track'), ('resolve', 'Resolve'),
         ('complete', 'Complete')],
        String='stage', default='new', tracking=True)
    brand_sla = fields.Char('SLA Brand')
    cskh_sla = fields.Char('SLA CSKH')
    branch_sla = fields.Char('SLA BV/Chi nhánh')
    note = fields.Text('Ghi chú')
    documents = fields.Many2many('ir.attachment', string="Tệp đính kèm", copy=False, tracking=True)
    create_by = fields.Many2one('res.users', string='Người tạo', default=lambda self: self.env.user, tracking=True)
    department_create_by = fields.Many2one('hr.department', string='Phòng ban người tạo', tracking=True, compute='set_department',
                                           store=True)
    PROCESSING_RESULTS = [('1', 'Đồng ý sử dụng dịch vụ'),
                          ('2', 'Hỗ trợ chi phí'),
                          ('3', 'Bảo hành và hỗ trợ chi phí'),
                          ('4', 'Theo dõi và chăm sóc')]
    processing_results = fields.Selection(PROCESSING_RESULTS, string='Kết quả xử lý')
    support_cost = fields.Float('Chi phí hỗ trợ')
    POST_PROCESSING_EVALUATION = [('1', 'Rất tệ'),
                                  ('2', 'Không hài lòng'),
                                  ('3', 'Bình thường'),
                                  ('4', 'Hài lòng'),
                                  ('5', 'Rất hài lòng')]
    post_processing_evaluation = fields.Selection(POST_PROCESSING_EVALUATION, string='Đánh giá KH sau xử lý', default='3')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CrmContentComplain, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone_partner']:
                fields[field_name]['exportable'] = False

        return fields

    @api.depends('create_by')
    def set_department(self):
        for rec in self:
            rec.department_create_by = False
            if rec.create_by:
                employee_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', rec.create_by.id)])
                rec.department_create_by = employee_id.department_id.id

    @api.onchange('complain_group_id', 'crm_case')
    def onchange_complain(self):
        self.complain_id = False
        if self.complain_group_id and self.crm_case:
            return {'domain': {'complain_id': [
                ('id', 'in', self.env['crm.complain'].search([('complain_group_id', '=', self.complain_group_id.id),
                                                              ('brand_id', '=', self.crm_case.brand_id.id)]).ids)],
                'department_ids': [
                    ('id', 'in',
                     self.env['hr.department'].search([('company_id', '=', self.crm_case.company_id.id)]).ids)]}}


class CrmCaseSolution(models.Model):
    _name = 'crm.case.solution'
    _description = 'Crm Case Solution'
    # Todo: Bỏ model này

    desc = fields.Text('Phản ánh khách hàng')
    solution = fields.Text('Giải pháp')


class CrmComplainCode(models.Model):
    _name = 'crm.complain.code'
    _description = 'Crm Complain Code'

    # Todo: Bỏ model này

    name = fields.Char('Name')
    code = fields.Char('Code')
    # brand_ids = fields.Many2many('res.brand', string='Brand')
    # company_ids = fields.Many2many('res.company', domain="[('brand_id','in',brand_ids)]")
    department_ids = fields.Many2many('hr.department', string='Department')

    _sql_constraints = [
        ('code_complain_uniq', 'unique(code)', 'This code already exists!')
    ]
