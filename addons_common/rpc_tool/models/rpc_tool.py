from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

TYPE = [('binary', 'Nhị phân'), ('boolean', 'Boolean'), ('char', 'Char'), ('date', 'Ngày'), ('datetime', 'Ngày giờ'),
        ('float', 'float'), ('integer', 'Số nguyên'), ('many2one', 'Many2one'), ('selection', 'Lựa chọn'),
        ('text', 'Văn bản')]

STAGE = [('0', 'Chưa chạy'), ('1', 'Đã chạy')]


class RPCTool(models.Model):
    _name = "rpc.tool"
    _description = 'Cập nhật dữ liệu'

    model_id = fields.Many2one('ir.model', string='Model')
    record_id = fields.Integer(string='ID bản ghi')
    line_ids = fields.One2many('rpc.tool.line', 'rpc_tool_record_id', string='Trường thay đổi')
    date_run = fields.Datetime(string='Ngày chạy RPC')
    uid_run = fields.Many2one('res.users', string='Người chạy RPC')
    stage = fields.Selection(STAGE, string='Trạng thái', default='0')
    log = fields.Text(string='Giá trị trước khi chạy RPC')

    def run_rpc(self):
        vals = {}
        if not self.record_id or self.record_id == 0:
            raise ValidationError(_('Chưa chọn bản ghi'))
        for line in self.line_ids:
            if line.type == 'binary':
                if not line.new_value_binary:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                vals[line.field.name] = line.new_value_binary
            elif line.type == 'boolean':
                if not line.new_value_boolean:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                vals[line.field.name] = line.new_value_boolean
            elif line.type in ['char', 'text']:
                if not line.new_value_text:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                vals[line.field.name] = line.new_value_text
            elif line.type == 'selection':
                if not line.new_value_text:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                domain_selection = []
                for rec in line.field.selection_ids:
                    domain_selection.append(rec.value)
                if line.new_value_text not in domain_selection:
                    raise ValidationError(
                        _('Trường %s đang nhập sai giá trị, trường này chỉ nhận các giá trị sau: %s') % (
                            line.field.name, ', '.join(domain_selection)))
                vals[line.field.name] = line.new_value_text
            elif line.type == 'date':
                if not line.new_value_date:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                vals[line.field.name] = line.new_value_date
            elif line.type == 'datetime':
                if not line.new_value_datetime:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                vals[line.field.name] = line.new_value_datetime
            elif line.type == 'integer':
                if not line.new_value_integer:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                vals[line.field.name] = line.new_value_integer
            elif line.type == 'many2one':
                if not line.new_value_integer:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %') % line.field.name)
                ob = self.env[line.field.relation].sudo().search([('id', '=', line.new_value_integer)])
                if ob:
                    vals[line.field.name] = line.new_value_integer
                else:
                    raise ValidationError(
                        _('Trường %s đang nhập sai giá trị, không tim thấy bản ghi %s có id %s') % (
                            line.field.name, line.field.relation, line.new_value_integer))
            else:
                if not line.new_value_float:
                    raise ValidationError(_('Chưa chọn giá trị cho trường %s') % line.field.name)
                vals[line.field.name] = line.new_value_float

        record = self.env[self.model_id.model].browse(int(self.record_id))
        log = self.env[self.model_id.model].search_read(domain=[('id', '=', self.record_id)], fields=vals.keys())
        self.log = log
        record.sudo().write(vals)

        self.date_run = fields.Datetime.now()
        self.uid_run = self.env.user
        self.stage = '1'

        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Cập nhật bản ghi thành công!!'
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view_id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }


class RPCToolLine(models.Model):
    _name = "rpc.tool.line"
    _description = 'Trường dữ liệu cập nhật'

    rpc_tool_record_id = fields.Many2one('rpc.tool', string='Bản ghi')

    model_id = fields.Many2one('ir.model', string='Model')
    field = fields.Many2one('ir.model.fields', string='Trường',
                            domain="[('model_id','=',model_id), ('ttype','in', ['binary', 'boolean', 'char', 'date', 'datetime', 'float', 'integer', 'many2one', 'selection', 'text'])]")
    type = fields.Selection(TYPE, string='Kiểu dữ liệu')

    # giá trị mới
    new_value_date = fields.Date(string='Ngày')
    new_value_datetime = fields.Datetime(string='Ngày giờ')
    new_value_boolean = fields.Boolean(string='Boolean')
    new_value_text = fields.Char(string='Chữ')
    new_value_integer = fields.Integer(string='Số nguyên')
    new_value_float = fields.Float(string='Số thập phân')
    new_value_binary = fields.Binary(string='Ảnh')

    @api.onchange('field')
    def _onchange_field(self):
        if self.field:
            self.type = self.field.ttype
        else:
            self.type = False
