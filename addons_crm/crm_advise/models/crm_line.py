from odoo import models, api, fields


class CrmLine(models.Model):
    _inherit = 'crm.line'

    @api.model
    def create(self, vals):
        res = super(CrmLine, self).create(vals)
        if res:
            advise_line_ids = self.env['crm.advise.line'].sudo().search([('group_service', '=', res.service_id.service_category.id),
                                                                         ('crm_id', '=',res.crm_id.id),
                                                                         ('desire_ids', '!=', False),
                                                                         ('pain_point_ids', '!=', False),
                                                                         ('state_ids', '!=', False)])
            if 'is_pk' in vals:
                self.env['crm.advise.line'].sudo().create({
                    'crm_id': res.crm_id.id,
                    'service': res.service_id.id,
                    'crm_line_id': res.id,
                    'conclude': "Đã chốt",
                    'desire_ids': advise_line_ids[0].desire_ids if advise_line_ids else False,
                    'pain_point_ids': advise_line_ids[0].pain_point_ids if advise_line_ids else False,
                    'state_ids': advise_line_ids[0].state_ids if advise_line_ids else False
                })
            else:
                self.env['crm.advise.line'].sudo().create({
                    'crm_id': res.crm_id.id,
                    'service': res.service_id.id,
                    'crm_line_id': res.id,
                    'desire_ids': advise_line_ids[0].desire_ids if advise_line_ids else False,
                    'pain_point_ids': advise_line_ids[0].pain_point_ids if advise_line_ids else False,
                    'state_ids': advise_line_ids[0].state_ids if advise_line_ids else False
                })
        return res

    is_new = fields.Boolean('New', help="Có giá trị True khi đã chốt trong phiếu tư vẫn, có giá trị False khi chưa chốt trong phiếu tư vấn.")
    is_potential = fields.Boolean('Tiềm năng')


    @api.depends('sale_order_line_id.state', 'number_used', 'quantity', 'cancel', 'discount_review_id.stage_id',
                 'brand_id', 'is_new')
    def set_stage(self):
        for rec in self:
            rec.stage = 'chotuvan'
            sol_stage = rec.sale_order_line_id.mapped('state')
            if rec.is_new:
                rec.stage = 'new'

            if rec.cancel:
                rec.stage = 'cancel'
            elif rec.discount_review_id and rec.discount_review_id.stage_id == 'offer':
                rec.stage = 'waiting'
            # elif (rec.number_used >= rec.quantity) and rec.pr_done and (rec.brand_id == self.env.ref('sci_brand.res_brand_paris')):
            elif (rec.number_used >= rec.quantity) and rec.pr_done and (rec.brand_id.id == 3):
                rec.stage = 'done'
            elif (rec.number_used >= rec.quantity) and not rec.odontology:
                rec.stage = 'done'
            elif 'draft' in sol_stage:
                rec.stage = 'processing'


class ResPartner(models.Model):
    _inherit = "res.partner"

    booking_ids = fields.One2many('crm.lead', 'partner_id', string='Booking',
                                  domain=[('type', '=', 'opportunity')], auto_join=True)
    lead_ids = fields.One2many('crm.lead', 'partner_id', string='Lead',
                               domain=[('type', '=', 'lead')], auto_join=True)

    def view_crm_advise_potential(self):
        return {'type': 'ir.actions.act_window',
                'name': ('Danh sách dịch vụ tiềm năng của khách hàng'),
                'res_model': 'crm.advise.line',
                # 'target': 'fullscreen',
                'view_mode': 'tree,form',
                'domain': [('brand_id', 'in', self.env.user.company_ids.brand_id.ids),
                           ('is_potential', '=', True), ('partner_id', '=', self.id)],
                'context': {},
                'views': [[self.env.ref('crm_advise.crm_advise_line_potential_tree_view').id, 'tree'],
                          [self.env.ref('crm_advise.crm_advise_line_potential_form_view').id, 'form']],
                }

class AppoinmentRegisterWalkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    def set_to_completed(self):
        res = super(AppoinmentRegisterWalkin, self).set_to_completed()
        advise_ids = self.env['crm.advise.line'].sudo().search([('service', 'in', self.service.ids), ('crm_id', '=', self.booking_id.id), ('is_potential', '=', True), ('stage_potential', '!=', 'exploited')])
        if advise_ids:
            for advise_id in advise_ids:
                advise_id.stage_potential = 'exploited'
                advise_id.company_done = self.booking_id.company_id.id
        return res