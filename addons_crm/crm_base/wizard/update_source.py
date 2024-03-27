from odoo import fields, models, api


class CrmLineUpdateSource(models.TransientModel):
    _name = 'crm.line.update.source'
    _description = 'Update source in crm line'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    crm_line_ids = fields.Many2many('crm.line', string='Dịch vụ')
    source_id = fields.Many2one('utm.source', string='Nguồn')

    @api.onchange('booking_id')
    def get_crm_line(self):
        if self.booking_id:
            return {'domain': {'crm_line_ids': [('id', 'in', self.env['crm.line'].search(
                [('stage', 'in', ['new', 'processing', 'waiting']), ('crm_id', '=', self.booking_id.id),
                 ('create_uid', '=', self.env.user.id)]).ids)]}}

    def update_source(self):
        for record in self.crm_line_ids:
            record.source_extend_id = self.source_id.id
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = 'Cập nhật nguồn thành công!!'
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
