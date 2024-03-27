import base64
import logging
from datetime import date, datetime, timedelta
from io import BytesIO
from odoo.http import request, content_disposition

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from .mailmerge import MailMerge

from odoo.tools.image import image_data_uri

_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta


class CollaboratorContract(models.Model):
    _name = 'collaborator.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hợp đồng'

    default_code = fields.Char('Mã hợp đồng', index=True, default='New')
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company,
                                 tracking=True)
    company_ids = fields.Many2many('res.company', string='Công ty cho phép', help='là nhưng cty cho phép khi công ty ký hợp đồng là không xác định')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True,
                               tracking=True)
    collaborator_id = fields.Many2one('collaborator.collaborator', string='Tên cộng tác viên', required=True,
                                      tracking=True,
                                      domain="[('source_id','=', source_id)]")
    passport = fields.Char('CMTND/CCCD', related='collaborator_id.passport')
    email = fields.Char('Email', related='collaborator_id.email')
    phone = fields.Char('Điện thoại 1', related='collaborator_id.phone')
    mobile = fields.Char('Điện thoại 2', related='collaborator_id.mobile')

    category_source_id = fields.Many2one('crm.category.source', string='Nhóm nguồn')
    source_id = fields.Many2one('utm.source', string='Nguồn', domain="[('is_collaborator', '=', True)]")
    description = fields.Text('Ghi chú')

    contract_type_id = fields.Many2one('collaborator.contract.type', string='Loại hợp đồng', tracking=True, domain="[('brand_id', '=', brand_id),('state', '=', 'effect')]")
    collaborator_agency = fields.Boolean('CTV đại lý', related='contract_type_id.collaborator_agency')
    start_date = fields.Date('Ngày bắt đầu', default=lambda self: fields.Datetime.now(), tracking=True,
                             help="Ngày bắt đầu hiệu lực hợp đồng")
    end_date = fields.Date('Ngày hết hạn', tracking=True, help="Ngày hết hạn hợp đồng")

    state = fields.Selection(
        [('new', 'Mới'), ('effect', 'Hiệu lực'), ('expired', 'Hết hiệu lực')],
        string='Trạng thái', default='new', tracking=True)

    document = fields.Binary(string="File hợp đồng", tracking=True)
    document_name = fields.Char(string="File name")

    # document_name = fields.Char(string="File name")
    active = fields.Boolean('Active', default=True)
    bank_id = fields.Many2one('collaborator.bank', 'Tài khoản ngân hàng',
                               domain="[('collaborator_id', '=', collaborator_id)]")

    referrer_id = fields.Many2one('res.partner', string='Người giới thiệu CTV',
                                  help='Nhân viên, khách hàng hoặc tổ chức giới thiệu cộng tác viên cho thương hiệu',
                                  tracking=True)
    manager_id = fields.Many2one('hr.employee', string='Quản lý CTV', tracking=True)
    expired_state = fields.Selection([('auto', 'Tự động gia hạn'), ('not_auto', 'Không tự động gia hạn')],
                                     compute='_compute_expired_state', store=True, string='Trạng thái gia hạn')
    type_legal_contract = fields.Selection([('1', 'Cá nhân'), ('2', 'Pháp nhân')], string='Loại', compute='_compute_type_legal_contract')
    # check mã
    _sql_constraints = [
        ('default_code_brand_unique', 'unique (default_code,brand_id)', 'Mã hợp đồng phải là duy nhất!')
    ]
    def _compute_type_legal_contract(self):
        if self.company_id:
            self.type_legal_contract = self.company_id.check_collaborator

    @api.constrains('start_date', 'end_date')
    def check_required_start_date_and_end_date(self):
        for record in self:
            if not record.start_date or not record.end_date:
                raise ValidationError("Bạn cần nhập ngày bắt đầu và kết thúc cho hợp đồng !!!")

    # @api.constrains('start_date', 'contract_type_id', 'manager_id')
    # def check_required_contract_type_id_and_manager_id(self):
    #     for record in self:
            # if not record.contract_type_id:
            #     raise ValidationError("Bạn cần chọn loại hợp đồng !!!")
            # if not record.manager_id:
            #     raise ValidationError("Bạn cần chọn người quản lý Cộng tác viên !!!")
    # chuyển name
    def name_get(self):
        if self._context.get('name_collaborator_contract'):
            result = super(CollaboratorContract, self).name_get()
            new_result = []
            for sub_res in result:
                record = self.env['collaborator.contract'].browse(sub_res[0])
                name = '[%s] - [%s]' % (record.default_code, record.company_id.name)
                if record.state == 'effect':
                    name += '- [Hiệu Lực]'
                elif record.state == 'new':
                    name += '- [Mới]'
                else:
                    name += '- [Hết hiệu Lực]'
                new_result.append((sub_res[0], name))
            return new_result
        # Mặc định
        record = []
        for rec in self:
            record.append((rec.id, '[' + rec.default_code + ']'))
        return record

    def set_to_effect(self):  # trạng thái
        """
        Chuyển hợp đồng sang Được sử dụng
        """
        if self.start_date > date.today():
            ngay_hieu_luc = self.start_date - date.today()
            raise ValidationError('Bạn chưa thể xác nhận hợp đồng vì còn %s ngày nữa mới đến ngày hợp đồng hiệu lực' % (ngay_hieu_luc.days))
        else:
            check_contract = self.env['collaborator.contract'].sudo().search(
                [('collaborator_id', '=', self.collaborator_id.id), ('state', '=', 'effect')])
            if check_contract:
                raise ValidationError(
                    'Cộng tác viên %s đang có hợp đồng %s có hiệu lực, bạn không thể xác nhận hợp đồng này' % (
                    check_contract.collaborator_id.name, check_contract.default_code))
            else:
                if self.contract_type_id.require_collaborator:
                    if self.collaborator_id.date_of_birth and self.collaborator_id.gender and self.collaborator_id.permanent_address and self.collaborator_id.country_id and self.collaborator_id.state_id and self.collaborator_id.district_id and self.collaborator_id.ward_id and self.collaborator_id.address and self.collaborator_id.passport_date and self.collaborator_id.passport_issue_by:
                        self.state = 'effect'
                        self.collaborator_id.company_id = self.company_id.id
                        self.collaborator_id.state = 'effect'
                    else:
                        raise ValidationError(
                            "Không thể chuyển hợp đồng sang hiệu lực vì CTV %s chưa nhập đầy đủ thông tin: \n"
                            "- Ngày sinh                                        - Giới tính\n"
                            "- Hộ khẩu thường trú                       - Địa chỉ\n"
                            "- Ngày cấp                                         - Nơi cấp\n"
                            " Vui lòng kiểm tra lại thông tin tại màn hình CTV"%self.collaborator_id.name)
                else:
                    self.state = 'effect'
                    self.collaborator_id.company_id = self.company_id.id
                    self.collaborator_id.state = 'effect'

    # # Lấy ra danh sách các line đã chọn để
    # @api.onchange('contract_type_id', )
    # def get_line_chose(self):
    #     self.chosen_line_ids = []
    #     if self.contract_type_id and len(self.contract_type_id) != 0:
    #         self.chosen_line_ids = self.contract_type_id.filtered(lambda fol: fol.stage in ('draft', 'new')).mapped('service_id').ids

    # def view_contract(self):
    #     return {
    #         'name': _('Chi tiết Hợp đồng'),  # label
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('collaborator.view_form_collaborator_contract').id,
    #         'res_model': 'collaborator.contract',  # model want to display
    #         'target': 'current',  # if you want popup,
    #         'context': {'form_view_initial_mode': 'edit'},
    #         # 'context': {},
    #         'res_id': self.id
    #     }

    # update trạng thái
    # def update_contract_collaborator(self):
    #     self.search([
    #         ('state', '=', 'effect'),
    #         ('end_date', '<', fields.Date.to_string(date.today() + relativedelta(days=0))),
    #     ]).write({
    #         'state': 'expired',
    #         'collaborator_id.state': 'new',
    #         'collaborator_id.check_contract': False,
    #     }),
    #     return True

    def update_contract_collaborator(self):
        expired_state = self.env['collaborator.contract'].sudo().search([
            ('expired_state', '=', 'auto'),
            ('end_date', '<', fields.Date.to_string(date.today() + relativedelta(days=0))),
        ])
        if expired_state:
            for rec in expired_state:
                rec.write({
                    'start_date': rec.end_date,
                    'end_date': rec.end_date + timedelta(days=365),
                })

        contracts_to_update = self.env['collaborator.contract'].sudo().search([
            ('state', '=', 'effect'),
            ('end_date', '<', fields.Date.to_string(date.today() + relativedelta(days=0))),
        ])
        if contracts_to_update:
            for rec in contracts_to_update:
                rec.write({
                    'state': 'expired',
                })
                rec.collaborator_id.write({
                    'state': 'expired',
                    # 'check_contract': False,
                    'company_id': False
                })

    @api.onchange('source_id')
    def onchange_collaborator_id(self):
        if self.source_id != self.collaborator_id:
            self.collaborator_id = False

    # @api.onchange('collaborator_id')
    # def onchange_collaborator_id(self):
    #     if self.collaborator_id != self.contract_type_id:
    #         self.contract_type_id = False
    #         self.chosen_line_ids = False

    @api.onchange('category_source_id')
    def onchange_source_id(self):
        if self.category_source_id != self.source_id:
            self.source_id = False

    # check ngày
    # @api.constrains('end_date')
    # def date_constrains(self):
    #     for rec in self:
    #         if rec.end_date and rec.start_date and rec.end_date < rec.start_date:
    #             raise ValidationError('Ngày hết hết không được nhỏ hơn ngày bắt đầu')
    #         if rec.end_date < date.today():
    #             raise ValidationError('Ngày kết thúc không được nhỏ hơn ngày hiện tại')

    @api.onchange('company_id')
    def _onchange_company_id_hd(self):
        if 'không xác định' in self.company_id.name.lower() and self.company_id.brand_id.id == 3:
            self.company_ids = self.env['res.company'].sudo().search([('brand_id', '=', 3)])
        else:
            self.company_ids = False
    def check_company_pa_kxd(self):
        if 'không xác định' in self.company_id.name.lower() and self.company_id.brand_id.id == 3:
            self.company_ids = self.env['res.company'].sudo().search([('brand_id', '=', 3)])
        else:
            self.company_ids = False
    # check cty
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id.brand_id:
            return {
                'domain': {'price_list_id': [('brand_id', '=', self.company_id.brand_id.id)]}
            }

    # @api.model
    # def create(self, vals):
    #     if vals.get('default_code', 'New') == 'New':
    #         vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborator.contract.knhn.sequence') or 'New'
    #     record = super(UtmSourceCtvContract, self).create(vals)
    #     return record

    @api.model
    def create(self, vals):
        if vals.get('default_code', 'New') == 'New':
            company_id = self.env['res.company'].sudo().search([('id', '=', vals['company_id'])])
            source_id = self.env['utm.source'].sudo().search([('id', '=', vals['source_id'])])
            # brand_id = self.env['res.brand'].search([('id', '=', vals['brand_id'])])
            # Fixme mỗi chi nhánh cần 1 sequence riêng @ToanNH xử lý
            sequence = self.env['ir.sequence'].next_by_code('collaborator.contract.sequence.%s' % company_id.code)
            if company_id.short_code and company_id.brand_id.code and source_id.tag:
                vals[
                    'default_code'] = company_id.brand_id.code + company_id.short_code + '-' + source_id.tag + sequence
            else:
                raise ValidationError(
                    'Bạn hãy cấu hình mã nguồn và mã viết tắt của công ty trước khi tạo thông tin cộng tác viên')
        record = super(CollaboratorContract, self).create(vals)
        return record

    def write(self, values):
        if 'active' in values and not values['active']:
            if self.state == 'effect':
                raise UserError(_('Bạn không thể lưu trữ khi hợp đồng còn hiệu lực.'))
            pass
        result = super(CollaboratorContract, self).write(values)
        return result

    def unlink(self):
        for rec in self:
            if rec.state != "new":
                raise UserError(_('Bạn chỉ có thể xoá hợp đồng khi ở trạng thái nháp'))
            else:
                hop_dong = self.env['collaborator.contract'].sudo().search(
                    [('collaborator_id', '=', rec.collaborator_id.id), ('state', '=', 'effect')])
                if not hop_dong:
                    rec.collaborator_id.state = "expired"
        return super(CollaboratorContract, self).unlink()

    # chuyển thành hết hiệu lực
    def expired_contract(self):
        """
        Chuyển hợp đồng sang Hết hiệu lực, cũng chuyển luôn
        """
        for rec in self:
            rec.state = 'expired'
            hop_dong = self.env['collaborator.contract'].sudo().search(
                [('collaborator_id', '=', rec.collaborator_id.id), ('state', '=', 'effect')])
            if not hop_dong:
                rec.collaborator_id.state = 'expired'
                rec.collaborator_id.company_id = False

    def extend_contract(self):
        for rec in self:
            check_contract = self.env['collaborator.contract'].sudo().search(
                [('collaborator_id', '=', rec.collaborator_id.id), ('state', '=', 'effect')])
            if check_contract:
                raise ValidationError(
                    'Cộng tác viên %s đang có hợp đồng %s có hiệu lực, bạn không thể gia hạn hợp đồng này' % (
                    check_contract.collaborator_id.name, check_contract.default_code))
            else:
                if self.contract_type_id.require_collaborator:
                    if self.collaborator_id.date_of_birth and self.collaborator_id.gender and self.collaborator_id.permanent_address and self.collaborator_id.country_id and self.collaborator_id.state_id and self.collaborator_id.district_id and self.collaborator_id.ward_id and self.collaborator_id.address and self.collaborator_id.passport_date and self.collaborator_id.passport_issue_by:
                        return {
                            'name': 'Thông tin gia hạn hợp đồng',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'view_id': self.env.ref('collaborator.collaborator_extebd_contract_wizard_view_form').id,
                            'res_model': 'collaborator.extend.contract',
                            'context': {
                                'default_contract_ids': self.id,
                                'default_collaborator': self.collaborator_id.id,
                                'default_company_id': self.company_id.id,
                                'default_contract_type_id': self.contract_type_id.id,
                                'default_end_date': self.end_date + relativedelta(days=365),
                                'default_start_date': self.end_date,
                                'default_referrer_id': self.referrer_id.id,
                                'default_manager_id': self.manager_id.id,
                            },
                            'target': 'new',
                        }
                    else:
                        raise ValidationError(
                            "Không thể chuyển hợp đồng sang hiệu lực vì CTV %s chưa nhập đầy đủ thông tin: \n"
                            "- Ngày sinh                                        - Giới tính\n"
                            "- Hộ khẩu thường trú                       - Địa chỉ\n"
                            "- Ngày cấp                                         - Nơi cấp\n"
                            " Vui lòng kiểm tra lại thông tin tại màn hình CTV" % self.collaborator_id.name)
                else:
                    return {
                        'name': 'Thông tin gia hạn hợp đồng',
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': self.env.ref('collaborator.collaborator_extebd_contract_wizard_view_form').id,
                        'res_model': 'collaborator.extend.contract',
                        'context': {
                            'default_contract_ids': self.id,
                            'default_collaborator': self.collaborator_id.id,
                            'default_company_id': self.company_id.id,
                            'default_contract_type_id': self.contract_type_id.id,
                            'default_end_date': self.end_date + relativedelta(days=365),
                            'default_start_date': self.end_date,
                            'default_referrer_id': self.referrer_id.id,
                            'default_manager_id': self.manager_id.id,
                        },
                        'target': 'new',
                    }

    def print_contract(self):
        contract_attachment = self.env.ref('collaborator.in_hop_dong_ctv_attachment')
        decode = base64.b64decode(contract_attachment.datas)
        doc = MailMerge(BytesIO(decode))
        data_list = []
        record_data = {}
        record_data['ma_hop_dong'] = self.default_code
        record_data['ten_phap_ly'] = self.company_id.collaborator_legal_name
        record_data['ten_ctv'] = self.collaborator_id.name
        record_data['tinh_tp'] = self.company_id.collaborator_state_id
        record_data['nguoi_dai_dien'] = self.company_id.collaborator_legal
        record_data['dia_chi_chi_nhanh'] = self.company_id.collaborator_street
        record_data['so_hop_dong'] = self.default_code
        record_data['ten_ctv_2'] = self.collaborator_id.name
        record_data['ten_ky'] = self.collaborator_id.name
        record_data['ma_ctv'] = self.collaborator_id.code
        record_data[
            'quoc_tich'] = self.collaborator_id.country_id.name if self.collaborator_id.country_id else '..............'
        record_data['nam_sinh'] = self.collaborator_id.date_of_birth.strftime(
            '%d/%m/%Y') if self.collaborator_id.date_of_birth else '.../.../......'
        record_data['ho_khau_thuong_tru'] = self.collaborator_id.permanent_address
        record_data['dia_chi'] = self.collaborator_id.address
        record_data['pass_port'] = self.collaborator_id.passport
        record_data['ngay_cap'] = self.collaborator_id.passport_date.strftime(
            '%d/%m/%Y') if self.collaborator_id.passport_date else '.../.../......'
        record_data['noi_cap'] = self.collaborator_id.passport_issue_by
        record_data['so_dien_thoai'] = self.collaborator_id.phone
        record_data['tao_hd'] = self.env.user.partner_id.name if self.env.user.partner_id else ''
        record_data['phong_ban'] = self.env.user.employee_ids.department_id.name if self.env.user.partner_id else ''
        record_data['ngan_hang'] = self.collaborator_id.bank_ids[
            0].bank_id.code if self.collaborator_id.bank_ids else ''
        record_data['chu_tai_khoan'] = self.collaborator_id.bank_ids[0].name if self.collaborator_id.bank_ids else ''
        record_data['so_tai_khoan'] = self.collaborator_id.bank_ids[
            0].card_number if self.collaborator_id.bank_ids else ''
        record_data['chi_nhanh'] = self.collaborator_id.bank_ids[0].chi_nhanh if self.collaborator_id.bank_ids else ''
        # record_data['tu_ngay'] = self.start_date.strftime('ngày %d tháng %m năm %Y')
        record_data['tu_ngay'] = self.start_date.strftime('NGAY %d THANG %m NAM %Y').replace('NGAY', 'ngày').replace(
            'THANG', 'tháng').replace('NAM', 'năm')
        record_data['den_ngay'] = self.end_date.strftime('NGAY %d THANG %m NAM %Y').replace('NGAY', 'ngày').replace(
            'THANG', 'tháng').replace('NAM', 'năm')
        # record_data['document_first'] = image_data_uri(self.document) if self.document else ''
        data_list.append(record_data)
        doc.merge_templates(data_list, separator='page_break')
        fp = BytesIO()
        doc.write(fp)
        doc.close()
        fp.seek(0)
        report = base64.encodebytes((fp.read()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({'name': 'hop_dong_ctv.docx',
                                                              'datas': report,
                                                              'res_model': 'temp.creation',
                                                              'public': True})
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % (attachment.id)
        return {'name': 'In hợp đồng CTV',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }

    def print_contract_pdf(self):
        if self.brand_id.id == 1:
            # Hợp đồng kangnam
            return self.env.ref('collaborator.action_report_file_template_collaborator_contract').report_action(self.id)
        elif self.brand_id.id == 3:
            # Hợp đồng Paris
            return self.env.ref('collaborator.action_report_file_template_collaborator_contract_pa').report_action(self.id)


    def print_contract_agency_pdf(self):
        if self.brand_id.id == 1:
            # Hợp đồng cộng tác viên đại lý dành riêng cho kangnam
            return self.env.ref('collaborator.action_report_file_template_collaborator_contract_agency').report_action(self.id)
        else:
            raise UserError(_('Vẫn chưa có hợp đồng Cộng tác viên đại lý cho thương hiệu này.'))

    @api.depends('collaborator_id.transaction_ids')
    def _compute_expired_state(self):
        for rec in self:
            if rec.collaborator_id:
                count = 0
                rec.expired_state = 'not_auto'
                for transaction in rec.collaborator_id.transaction_ids:
                    if transaction.create_date and rec.start_date and rec.end_date:
                        if transaction.create_date.date() >= rec.start_date and transaction.create_date.date() <= rec.end_date:
                            count += transaction.amount_total
                if count > 0:
                    rec.expired_state = 'auto'

    @api.model
    def action_contract_almost_expired(self): #hợp đồng sắp hết hạn
        action = self.env.ref('collaborator.collaborator_contract_almost_expired_action').read()[0]
        action['domain'] = [('end_date', '>=', datetime.now()),
                            ('end_date', '<=', datetime.now() + timedelta(days=30)),
                            ('company_id', 'in', self.env.user.company_ids.ids), ('state', '=', 'effect')]
        return action

    @api.model
    def action_contract_expired(self): #hợp dồng hết hạn
        action = self.env.ref('collaborator.collaborator_contract_expired_action').read()[0]
        action['domain'] = [('company_id', 'in', self.env.user.company_ids.ids), ('state', '=', 'expired')]
        return action
