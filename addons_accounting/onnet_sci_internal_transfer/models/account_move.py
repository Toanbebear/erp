
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    stock_picking_id = fields.Many2one('stock.picking', string=_('Transfer picking'))
    is_netoff = fields.Boolean('Is Netoff', default=False)


    def post(self):
        res = super(AccountMoveInherit, self).post()
        if not self._context.get('is_netoff_transfer'):
            for rec in self.filtered(lambda m: not m.is_netoff and m.state == 'posted' and m.journal_id == self.company_id.journal_internal_transfer_product_id and m.stock_picking_id.intercompany_transfer_inbound):
                stock_picking_B = rec.stock_picking_id
                transfer_company = stock_picking_B.transfer_company
                journal = transfer_company.sudo().journal_internal_transfer_product_id
                if not journal.id:
                    raise ValidationError(_('Không có sổ nhật ký điều chuyển nội bộ'))
                product_id = rec.line_ids[-1].product_id
                stock_move_line = stock_picking_B.move_line_ids_without_package.filtered(lambda l: l.product_id == product_id)
                if stock_move_line:
                    price_product = stock_move_line.move_id.price_unit

                    vals = [[0,6,{
                            "account_id": transfer_company.internal_transfer_account.id,
                            "product_id": stock_move_line.product_id.id,
                            "debit": price_product * stock_move_line.qty_done,
                            "partner_id": self.company_id.partner_id.id,
                        }],[0,6,{
                            "account_id": stock_move_line.product_id.sudo().categ_id.with_context(allowed_company_ids=[transfer_company.id]).property_stock_account_input_categ_id.id,
                            "product_id": stock_move_line.product_id.id,
                            "credit": price_product * stock_move_line.qty_done,
                        }
                    ]]
                    account_move = self.env['account.move'].sudo().create({
                        "ref": 'Điều chuyển nội bộ ' + transfer_company.name + ' tới ' + self.company_id.name + ' - ' + stock_picking_B.name,
                        "company_id": transfer_company.id,
                        "journal_id": journal.id,
                        "line_ids": vals,
                        "stock_picking_id": stock_picking_B.transfer_picking.id,
                    })
                    account_move.post()
            for rec in self.filtered(
                    lambda m: m.stock_picking_id.intercompany_transfer or m.stock_picking_id.intercompany_transfer_inbound):
                netoff_am = False
                if rec.stock_picking_id and not rec.is_netoff:
                    netoff_account_move = self.env['account.move'].sudo().search(
                        [('stock_picking_id', '=', rec.stock_picking_id.id)]).filtered(
                        lambda m: m.line_ids and m.line_ids[-1].product_id == rec.line_ids[
                            -1].product_id and m.is_netoff)
                    netoff_am = True if not netoff_account_move else False
                if netoff_am:
                    rec.create_internal_transfer_netoff()

        return res

    def create_internal_transfer_netoff(self):
        product_id = self.line_ids[-1].product_id

        stock_picking = self.stock_picking_id
        picking = self.env['stock.picking'].sudo().search([('transfer_picking', '=', stock_picking.id)])
        if stock_picking.intercompany_transfer and stock_picking.receiving_company.sudo() and picking:
            account_move = self.env['account.move'].sudo().search([('stock_picking_id', '=', picking.id)]).filtered(
            lambda m: m.line_ids and m.line_ids[-1].product_id == product_id and not m.is_netoff)
        elif stock_picking.transfer_picking.sudo():
            account_move = self.env['account.move'].sudo().search([('stock_picking_id', '=', stock_picking.transfer_picking.id)]).filtered(
                lambda m: m.line_ids and m.line_ids[-1].product_id == product_id and not m.is_netoff)
        cr_account_move = self.env['account.move'].sudo().search([('stock_picking_id', '=', stock_picking.id)]).filtered(
            lambda m: m.line_ids and m.line_ids[-1].product_id == product_id and not m.is_netoff)

        # Tạo Netoff điều chuyển nội bộ:
        if account_move and all(move.state == 'posted' for move in account_move) and cr_account_move and all(move.state == 'posted' for move in cr_account_move):
            sci_company = self.env['res.company'].sudo().search([('name', '=', 'SCIGROUP')], limit=1)
            if stock_picking.intercompany_transfer and stock_picking.receiving_company.sudo() and picking:
                for stock_move_line in picking.move_line_ids_without_package.filtered(lambda l: l.product_id == product_id):
                    # Netoff tại cty chuyển
                    price_product = stock_move_line.move_id.price_unit
                    journal = stock_picking.sudo().company_id.journal_internal_transfer_product_id
                    vals = [[0, 6, {
                        "account_id": stock_picking.company_id.x_internal_payable_account_id.id,
                        "product_id": stock_move_line.product_id.id,
                        "amount_currency": price_product * stock_move_line.qty_done,
                        "debit": price_product * stock_move_line.qty_done,
                        "partner_id": sci_company.partner_id.id,
                    }], [0, 6, {
                        "account_id": stock_picking.company_id.internal_transfer_account.id,
                        "product_id": stock_move_line.product_id.id,
                        "amount_currency": -(price_product * stock_move_line.qty_done),
                        "credit": price_product * stock_move_line.qty_done,
                        "partner_id": stock_picking.receiving_company.partner_id.id,
                    }
                    ]]
                    account_move_A = self.env['account.move'].sudo().create({
                        "ref": 'Netoff Điều chuyển nội bộ ' + stock_picking.company_id.name + ' tới ' + stock_picking.receiving_company.name + ' - ' + stock_picking.name + ' - ' + product_id.name,
                        "company_id": stock_picking.company_id.id,
                        "stock_picking_id": stock_picking.id,
                        "journal_id": journal.id,
                        "is_netoff": True,
                        "lydo": 'Netoff - ' + stock_picking.company_id.name + ': ' + stock_picking.name + ' - ' + product_id.name,
                        "line_ids": vals,
                    })
                    account_move_A.sudo().with_context(is_netoff_transfer=True).post()

                    # Netoff tại cty nhận
                    journal_B = picking.sudo().company_id.journal_internal_transfer_product_id
                    vals_B = [[0, 6, {
                        "account_id": picking.company_id.x_internal_payable_account_id.id,
                        "product_id": stock_move_line.product_id.id,
                        "amount_currency": price_product * stock_move_line.qty_done,
                        "debit": price_product * stock_move_line.qty_done,
                        "partner_id": picking.transfer_picking.company_id.partner_id.id,
                    }], [0, 6, {
                        "account_id": picking.company_id.x_internal_payable_account_id.id,
                        "product_id": stock_move_line.product_id.id,
                        "amount_currency": -(price_product * stock_move_line.qty_done),
                        "credit": price_product * stock_move_line.qty_done,
                        "partner_id": sci_company.partner_id.id,
                    }
                    ]]
                    account_move_B = self.env['account.move'].sudo().create({
                        "ref": 'Netoff Điều chuyển nội bộ ' + stock_picking.company_id.name + ' tới ' + stock_picking.receiving_company.name + ' - ' + picking.name + ' - ' + product_id.name,
                        "company_id": picking.company_id.id,
                        "stock_picking_id": picking.id,
                        "journal_id": journal_B.id,
                        "is_netoff": True,
                        "lydo": 'Netoff - ' + picking.company_id.name + ': ' + picking.name + ' - ' + product_id.name,
                        "line_ids": vals_B,
                    })
                    account_move_B.sudo().with_context(is_netoff_transfer=True).post()

                    # Netoff tại SCI:
                    journal_SCI = sci_company.journal_internal_transfer_product_id
                    vals_SCI = [[0, 6, {
                        "account_id": sci_company.internal_transfer_account.id,
                        "product_id": stock_move_line.product_id.id,
                        "amount_currency": price_product * stock_move_line.qty_done,
                        "debit": price_product * stock_move_line.qty_done,
                        "partner_id": picking.company_id.partner_id.id,
                    }], [0, 6, {
                        "account_id": sci_company.internal_transfer_account.id,
                        "product_id": stock_move_line.product_id.id,
                        "amount_currency": -(price_product * stock_move_line.qty_done),
                        "credit": price_product * stock_move_line.qty_done,
                        "partner_id": stock_picking.company_id.partner_id.id,
                    }
                         ]]
                    account_move_SCI = self.env['account.move'].sudo().create({
                        "ref": 'Netoff Điều chuyển nội bộ ' + stock_picking.company_id.name + ' tới ' + stock_picking.receiving_company.name + '  tại SCI Group - ' + product_id.name,
                        "company_id": sci_company.id,
                        "stock_picking_id": None,
                        "journal_id": journal_SCI.id,
                        "is_netoff": True,
                        "lydo": 'Netoff Điều chuyển nội bộ ' + stock_picking.company_id.name + ' tới ' + stock_picking.receiving_company.name + '  tại SCI Group - ' + stock_picking.name + ' tới ' + picking.name + ' - ' + product_id.name,
                        "line_ids": vals_SCI,
                    })

                    account_move_SCI.with_context(is_netoff_transfer=True).post()


