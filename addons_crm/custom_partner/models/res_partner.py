from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime, date, timedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Chuyển từ module custom_partner_extend
    aliases = fields.Char('Bí danh')

    birth_date = fields.Date('Birth date', tracking=True)
    year_of_birth = fields.Char('Year of birth', tracking=True)
    age = fields.Integer('Age', compute='set_age', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('transguy', 'Transguy'),
                               ('transgirl', 'Transgirl'), ('other', 'Other')], string='Gender', tracking=True)
    pass_port = fields.Char('Pass port', tracking=True)
    relation_ids = fields.One2many('relation.partner', 'partner_id', string='Relation partner', tracking=True)
    code_customer = fields.Char('Code customer', tracking=True)
    crm_ids = fields.One2many('crm.lead', 'partner_id', string='CRM', tracking=True)
    payment_ids = fields.One2many('account.payment', 'partner_id', string='Payments', tracking=True)
    source_id = fields.Many2one('utm.source', string='Source', tracking=True)
    career = fields.Char('Nghề nghiệp')
    pass_port_date = fields.Date('Pass port Date', tracking=True)
    pass_port_issue_by = fields.Char('Pass port Issue by', tracking=True)
    pass_port_address = fields.Text('Permanent address')
    overseas_vietnamese = fields.Selection(
        [('no', 'No'), ('marketing', 'Marketing - Overseas Vietnamese'), ('branch', 'Branch - Overseas Vietnamese')],
        string='Khách hàng việt kiều', default='no', tracking=True)
    allergy_history = fields.Text('Allergy history')
    district_id = fields.Many2one('res.country.district', string='District', tracking=True)
    customer_classification = fields.Selection(
        [('5', 'Khách hàng V.I.P'), ('4', 'Đặc biệt'), ('3', 'Quan tâm hơn'), ('2', 'Quan tâm'), ('1', 'Bình thường')],
        string='Phân loại khách hàng', default='1')
    ward_id = fields.Many2one('res.country.ward', string='Phường/xã', tracking=True)

    _sql_constraints = [
        ('name_phone', 'unique(phone)', "Số điện thoại này đã tồn tại!!!"),
    ]
    type_data_partner = fields.Selection([('old', 'Cũ'), ('new', 'Mới')], string='Loại data')
    return_custom = fields.Boolean('Khách hàng quay lại ?', compute='check_return_custom', store=True)

    @api.constrains('pass_port_date')
    def validate_passport_date(self):
        for rec in self:
            date_check_max = date.today() + timedelta(days=365 * 20)
            date_check_min = date.today() - timedelta(days=365 * 20)
            if rec.pass_port_date and (rec.pass_port_date.year > date_check_max.year):
                raise ValidationError('Ngày cấp CMT/CCCD không hợp lệ.\nCMT/CCCD đã hết hạn')
            if rec.pass_port_date and (rec.pass_port_date.year < date_check_min.year):
                raise ValidationError('Ngày cấp CMT/CCCD không hợp lệ.\nCMT/CCCD đã hết hạn')

    @api.depends('type_data_partner')
    def check_return_custom(self):
        for record in self:
            record.return_custom = False
            if record.type_data_partner == 'old':
                record.return_custom = True

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(ResPartner, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone', 'mobile', 'phone_sanitized']:
                fields[field_name]['exportable'] = False

        return fields

    @api.model
    def default_get(self, fields):
        """ Hack :  when going from the pipeline, creating a stage with a sales team in
            context should not create a stage for the current Sales Team only
        """
        ctx = dict(self.env.context)
        if ctx.get('default_type') == 'lead' or ctx.get('default_type') == 'opportunity':
            ctx.pop('default_type')
        return super(ResPartner, self.with_context(ctx)).default_get(fields)

    # @api.model
    # def create(self, vals):
    #     res = super(ResPartner, self).create(vals)
    #     if res.company_type == 'person':
    #         res.code_customer = self.env['ir.sequence'].next_by_code('res.partner')
    #     return res
    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.company_type == 'company':
            res.code_customer = self.env['ir.sequence'].next_by_code('res.partner.vendor')
        return res

    def set_age(self):
        for rec in self:
            rec.age = 0
            if rec.year_of_birth and rec.year_of_birth.isdigit() is True:
                rec.age = fields.Datetime.now().year - int(rec.year_of_birth)

    @api.constrains('phone')
    def constrain_phone_number(self):
        for rec in self:
            if rec.phone and rec.phone.isdigit() is False:
                raise ValidationError('Điện thoại không được phép chứa ký tự chữ !!!')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', '|', ('name', operator, name), ('phone', operator, name),
                      ('mobile', operator, name), ('aliases', operator, name), ('code_customer', operator, name)]
        partner_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(partner_id).name_get()


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('login', operator, name)]
        partner_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(partner_id).name_get()

    def name_get(self):
        result = super(ResUsers, self).name_get()
        if self._context.get('name_code_employee_of_user'):
            new_result = []
            for sub_result in result:
                user = self.env['res.users'].browse(sub_result[0])
                employee = self.env['hr.employee']
                if len(user.employee_ids) == 1:
                    employee += user.employee_ids[0]
                else:
                    employee += self.env['hr.employee'].sudo().search(['|', ('user_id', '=', user.id),
                                                               ('work_email', '=', user.login), ('active', '=', True)], limit=1)
                name = '[%s]' % employee.employee_code + sub_result[1]
                if employee.birthday:
                    name += ' - ' + str(employee.birthday.year)
                else:
                    name += ' - Năm sinh'
                if employee.sudo().job_id:
                    name += ' - ' + employee.sudo().job_id.name
                else:
                    name += ' - Chức vụ'
                new_result.append((sub_result[0], name))
            return new_result
        return result

#     kế thừa lưu trữ
    def toggle_active(self):
        res = super(ResUsers, self).toggle_active()
        today = datetime.now().strftime('%d-%m-%Y')
        for act in self:
            if act.active:
                act.write({
                    'login': act.login[:-11]
                })
                if act.partner_id:
                    new_login = act.partner_id.email[:-11]
                    act.partner_id.write({
                        'email': new_login,
                        'active': True
                    })

                if act.employee_ids:
                    act.employee_ids.write({
                        'work_email': act.work_email[:-11],
                        'active': True
                    })
            else:
                act.write({
                    'login': act.login + '.' + today
                })
                if act.partner_id:
                    new_login = act.partner_id.email + '.' + today
                    act.partner_id.write({
                        'email': new_login,
                        'active': False
                    })

                if act.employee_ids:
                    act.employee_ids.write({
                        'work_email': act.employee_ids.work_email + '.' + today,
                        'active': False
                    })
        return res
