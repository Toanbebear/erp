from odoo import models, fields


class UpdateLineConsultants(models.TransientModel):
    _name = "update.line.consultants"
    _description = "Cập nhật tư vấn viên vào loại line dịch vụ"

    def _get_line(self):
        booking = self.env['crm.lead'].browse(self._context.get('default_booking'))
        line_ids = booking.crm_line_ids.filtered(lambda l: l.stage in ['new', 'processing'])
        # if self.env.company.brand_id.id == 3:
        #     line_ids = booking.crm_line_ids.filtered(lambda l: (l.stage in ['new', 'processing']) and not l.crm_information_ids)
        # else:
        #     line_ids = booking.crm_line_ids.filtered(
        #         lambda l: (l.stage in ['new', 'processing']) and not l.consultants_1)
        return [('id', 'in', line_ids.ids)]

    booking = fields.Many2one('crm.lead')
    consultant_id = fields.Many2one('res.users', string='Tư vấn viên')
    line_ids = fields.Many2many('crm.line', string='Dịch vụ cập nhật', domain=_get_line)

    def confirm(self):
        if (self.env.company.brand_id.id == 3) and self.line_ids:
            for line in self.line_ids:
                line.crm_information_ids = [(5, 0)]
                line.crm_information_ids = [(0, 0, {'role': 'recept', 'user_id': self.consultant_id.id})]
        elif (self.env.company.brand_id.id != 3) and self.line_ids:
            for line in self.line_ids:
                line.consultants_1 = self.consultant_id.id
