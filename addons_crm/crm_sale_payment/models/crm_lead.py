from odoo import api, fields, models

SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'), ('ChiPhi', 'Chi phí khác')]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def compute_remaining_amount(self):
        # for record in self:
        #     for line in record.crm_line_ids:
        #         line.total_received = 0
        #     for line in record.crm_line_product_ids:
        #         line.total_received = 0
        #
        #     payment = record.payment_ids
        #     for p in payment:
        #         p.service_ids._calculate_total_received()
        #         p.product_ids._calculate_total_received()
        #         p.service_ids.update_total_received_crm_line(p.payment_type)
        #         p.product_ids.update_total_received_crm_line_product(p.payment_type)
        # Hải SCI viết lại
        sale_payment = self.env['crm.sale.payment'].search([('booking_id', '=', self.id)])
        if self.crm_line_ids:
            for line in self.crm_line_ids:
                sub_sp = sale_payment.filtered(lambda sp: sp.crm_line_id == line)
                if sub_sp:
                    line.total_received = sum(sub_sp.mapped('amount_proceeds'))
        if self.crm_line_product_ids:
            for line in self.crm_line_product_ids:
                sub_sp = sale_payment.filtered(lambda sp: sp.product_id == line)
                if sub_sp:
                    line.total_received = sum(sub_sp.mapped('amount_proceeds'))

    # reformat The Anh code
    def recompute_remaining_amount(self):
        for record in self:
            for line in record.crm_line_ids:
                crm_sale_payment = self.env['crm.sale.payment'].search([('crm_line_id', '=', line.id)])
                line.total_received = sum(crm_sale_payment.mapped('amount_proceeds'))
            for line in record.crm_line_product_ids:
                crm_sale_payment = self.env['crm.sale.payment'].search([('crm_line_product_id', '=', line.id)])
                line.total_received = sum(crm_sale_payment.mapped('amount_proceeds'))

    def edit_account_payment_line(self):
        # Lay list account payment
        account_payment_list = self.env['account.payment'].sudo().search([
            ('crm_id', '=', self.id),
        ])
        for rec in account_payment_list:
            # total_prepayment = sum(rec.service_ids.mapped('prepayment_amount')) + sum(rec.product_ids.mapped('prepayment_amount'))
            if rec.state != 'draft':
                # rec.sudo().edit() # Hải SCI
                rec.is_old_payment = True
                # Xoa toan bo account payment line
                if rec.service_ids:
                    rec.service_ids.sudo().unlink()
                if rec.product_ids:
                    rec.product_ids.sudo().unlink()
        # Lay list transfer payment
        # Xoa toan bo transfer
        transfer_list = self.env['crm.transfer.payment'].sudo().search([('crm_id', '=', self.id)])
        for rec in transfer_list:
            rec.state = 'draft'
            rec.sudo().unlink()

        self.env['crm.sale.payment'].sudo().search([('booking_id', '=', self.id)]).sudo().unlink()
        # Cap nhat lai tien da thu
        self.recompute_remaining_amount()



class CrmLineProduct(models.Model):
    _inherit = 'crm.line.product'

    department = fields.Selection(SERVICE_HIS_TYPE, string='Phòng ban')







