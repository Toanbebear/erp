from odoo import fields, api, models, _
import logging
from odoo.exceptions import ValidationError,UserError
from datetime import date, datetime, time

_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError


class CollaboratorsContract(models.Model):
    _name = 'collaborators.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hợp đồng Cộng tác viên'

    default_code = fields.Char('Mã hợp đồng', index=True, default='New', tracking=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True,
                                 default=lambda self: self.env.company, )
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    collaborators_id = fields.Many2one('crm.collaborators', string='Tên cộng tác viên', required=True,
                                 domain="[('source_id', '=', source_id)]", tracking=True)  # translate=True
    pass_port = fields.Char('CMTND/CCCD ', tracking=True)
    email = fields.Char('Email', )
    phone = fields.Char('Điện thoại 1', )
    mobile = fields.Char('Điện thoại 2', )
    category_source_id = fields.Many2one('crm.category.source', string='Nhóm nguồn', )
    source_id = fields.Many2one('utm.source', string='Nguồn', domain="[('category_id', '=', category_source_id)]", )
    description = fields.Text('Ghi chú')
    crm_line_ids = fields.Many2one('products.discount', string='Loại hợp đồng', tracking=True)
    start_date = fields.Date('Ngày bắt đầu', default=lambda self: fields.Datetime.now(), tracking=True)
    end_date = fields.Date('Ngày hết hạn hợp đồng', help="Ngày hết hạn đối với hợp đồng đã ký", tracking=True)
    stage = fields.Selection(
        [('draft', 'Nháp'), ('open', 'Mở lại'), ('new', 'Có hiệu lực'), ('done', 'Hết hiệu lực'), ('cancel', 'Đã hủy')],
        string='Trạng thái', store=True, default='draft', tracking=True)
    documents = fields.Binary(string="Update file hợp đồng", tracking=True)
    document_name = fields.Char(string="File name")


    # huy hợp đông

    REASON_LINE_CANCEL = [('change_service', 'Đổi sang hợp dồng khác'), ('consider_more', 'Cân nhắc thêm'),
                          ('create_wrong_service', 'Thao tác tạo sai hợp đồng'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy hợp đồng')
    cancel_user = fields.Many2one('res.users', 'Người hủy')
    cancel_date = fields.Datetime('Thời gian hủy')
    note = fields.Text('Ghi chứ', )

    # check mã
    _sql_constraints = [
        ('unique_source_default_code', 'unique (default_code)', 'Mã hợp đồng phải là duy nhất!')
    ]

    # chuyển name
    def name_get(self):
        record = []
        for rec in self:
            record.append((rec.id, '[' + rec.default_code + ']'))
        return record

    def set_to_new(self):  # trạng thái
        # self.stage = 'new'
        # check = self.env['collaborators.contract'].search(
        #     [('stage', 'in', ['new', 'open']), ('company_id', '=', self.company_id.ids)])
        check = self.collaborators_id.contract_ids.filtered(lambda fol: fol.stage in ('new', 'open') and fol.company_id in self.company_id)
        if not check:
            self.stage = 'new'
        else:
            raise ValidationError('Bạn không thể xác nhận vì vẫn đang có hợp đồng được sử dụng' + " " + str(check.default_code))

    def reopen_contract(self):
        self.stage = 'new'

    def set_to_draft(self):  # trạng thái
        self.stage = 'open'

    # # Lấy ra danh sách các line đã chọn để
    # @api.onchange('crm_line_ids', )
    # def get_line_chose(self):
    #     self.chosen_line_ids = []
    #     if self.crm_line_ids and len(self.crm_line_ids) != 0:
    #         self.chosen_line_ids = self.crm_line_ids.filtered(lambda fol: fol.stage in ('draft', 'new')).mapped('service_id').ids

    def view_contract(self):
        return {
            'name': _('Chi tiết Hợp đồng'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_collaborators.view_form_collaborators_contract').id,
            'res_model': 'collaborators.contract',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            # 'context': {},
            'res_id': self.id
        }

    def set_to_cancel(self):
        return {
            'name': 'HỦY HỢP ĐỒNG',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_collaborators.view_form_cancel_collaborators_contract').id,
            'res_model': 'cancel.collaborators.contract',
            'context': {
                'default_crm_line_id': self.id,
            },
            'target': 'new',
        }

    # update trạng thái
    def update_contract_collaborators(self):
        self.search([
            ('stage', 'in', ['new', 'open']),
            ('end_date', '<', fields.Date.to_string(date.today() + relativedelta(days=0))),
        ]).write({
            'stage': 'done',
        }),
        return True

    @api.onchange('source_id')
    def onchange_collaborators_id(self):
        if self.source_id != self.collaborators_id:
            self.collaborators_id = False

    # @api.onchange('collaborators_id')
    # def onchange_collaborators_id(self):
    #     if self.collaborators_id != self.crm_line_ids:
    #         self.crm_line_ids = False
    #         self.chosen_line_ids = False

    @api.onchange('category_source_id')
    def onchange_source_id(self):
        if self.category_source_id != self.source_id:
            self.source_id = False
    # check ngày
    @api.constrains('end_date')
    def date_constrains(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.end_date < rec.start_date:
                raise ValidationError('Ngày hết hết không được nhỏ hơn ngày bắt đầu')
            if rec.end_date < date.today():
                raise ValidationError('Ngày kết thúc không được nhỏ hơn ngày hiện tại')


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
    #         vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.knhn.sequence') or 'New'
    #     record = super(UtmSourceCtvContract, self).create(vals)
    #     return record

    @api.model
    def create(self, vals):
        if vals['company_id']:
            company_id = self.env['res.company'].search([('id', '=', vals['company_id'])])
            if company_id.code == 'SCI.HO.01':  ########1
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.sci.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'KB.HN.02':  ##########2
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.knhn.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'PN.HCM.14':  ##########3
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.pnhcm.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'KN.HCM.01':  ##########4
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.knhcm.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'DB.HN.01':  ##########5
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.dbhn.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'DB.HP.03':  ##########6
                vals['666666666'] = self.env['ir.sequence'].next_by_code('collaborators.contract.dbhp.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'DN.HCM.08':  ############12
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.dnhcm.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'PB.HN.01':  ##########13
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.pbhn.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'PB.HN.08':  ##########14
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.pbhn08.sequence')
            elif company_id.code == 'PB.HP.05':  ##########15
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.pbhp05.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'PB.HN.11':  ############23
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.pbhn.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'BVHH.HN.01':  ############24
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.bvhhhn01.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'KN.HCM.03':  ##########29
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.kn84.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'BVHH.HCM.01':  ##########32
                vals['default_code'] = self.env['ir.sequence'].next_by_code(
                    'collaborators.contract.bvhhhcm01.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'DN.BMT.11':  ########37
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.dnbmt11.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            elif company_id.code == 'PN.BMT.15':  ########38
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.pnbtm15.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            else:
                vals['default_code'] = self.env['ir.sequence'].next_by_code('collaborators.contract.else.sequence')
                record = super(CollaboratorsContract, self).create(vals)
                return record
            # raise ValidationError('duwnfg')

    def write(self, vals):
        return super(CollaboratorsContract, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.stage != "draft":
                raise UserError(_('Bạn chỉ có thể xoá hợp đồng khi ở trạng thái nháp'))

            rec.collaborators_id.state = "unprocessed"

        return super(CollaboratorsContract, self).unlink()