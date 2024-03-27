from odoo import models, fields, api


class CrmLine(models.Model):
    _inherit = "crm.line"

    pr_done = fields.Boolean('Dịch vụ PR kết thúc')
    pr_date_done = fields.Date('Ngày kết thúc dịch vụ(PR)')
    # is_new = fields.Boolean('New', tracking=True)
    #
    # @api.depends('sale_order_line_id.state', 'number_used', 'quantity', 'cancel', 'discount_review_id.stage_id',
    #              'pr_done', 'brand_id', 'is_new')
    # def set_stage(self):
    #     for rec in self:
    #         rec.stage = 'chotuvan'
    #         sol_stage = rec.sale_order_line_id.mapped('state')
    #         if rec.is_new:
    #             rec.stage = 'new'
    #
    #         if rec.cancel:
    #             rec.stage = 'cancel'
    #         elif rec.discount_review_id and rec.discount_review_id.stage_id == 'offer':
    #             rec.stage = 'waiting'
    #         # elif (rec.number_used >= rec.quantity) and rec.pr_done and (rec.brand_id == self.env.ref('sci_brand.res_brand_paris')):
    #         elif (rec.number_used >= rec.quantity) and rec.pr_done and (rec.brand_id.id == 3):
    #             rec.stage = 'done'
    #         elif (rec.number_used >= rec.quantity) and not rec.odontology:
    #             rec.stage = 'done'
    #         elif 'draft' in sol_stage:
    #             rec.stage = 'processing'
    @api.depends('sale_order_line_id.state', 'number_used', 'quantity', 'cancel', 'discount_review_id.stage_id',
                 'pr_done', 'brand_id')
    def set_stage(self):
        for rec in self:
            rec.stage = 'new'
            sol_stage = rec.sale_order_line_id.mapped('state')
            if rec.cancel is True:
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