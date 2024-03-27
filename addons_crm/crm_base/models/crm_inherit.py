import json
import logging
from datetime import date, timedelta, datetime
from itertools import groupby
from lxml import etree
from odoo.tools import float_is_zero, float_compare
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class CrmStage(models.Model):
    _inherit = 'crm.stage'
    crm_type_id = fields.Many2many('crm.type', 'stage_type_crm_ref', 'stage', 'type_crm', string='Type crm')
    crm_stage_insight_id = fields.Integer('Insight stage id')


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    code = fields.Char('Mã chiến dịch')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    start_date = fields.Date('Ngày bắt đầu')
    end_date = fields.Date('Ngày kết thúc')
    CAMPAIGN_STATUS = [('1', 'Chưa bắt đầu'), ('2', 'Đang chạy'), ('3', 'Kết thúc')]
    campaign_status = fields.Selection(CAMPAIGN_STATUS, compute='set_campaign_status', store=True, default='1')
    text_code = fields.Char('Mã văn bản', tracking=True)
    doc_attachment_id = fields.Many2many('ir.attachment', string="Tệp đính kèm",
                                         help='You can attach the copy of your document', copy=False, tracking=True)
    active = fields.Boolean('Active', default=True)

    def set_new(self):
        self.campaign_status = '1'

    def set_active(self):
        self.campaign_status = '2'

    def set_expire(self):
        self.campaign_status = '3'

    @api.depends('start_date', 'end_date')
    def set_campaign_status(self):
        for record in self:
            record.campaign_status = '1'
            if record.start_date and record.end_date:
                if record.start_date > date.today():
                    record.campaign_status = '1'
                elif (record.start_date <= date.today()) and (date.today() <= record.end_date):
                    record.campaign_status = '2'
                else:
                    record.campaign_status = '3'

    @api.model
    def update_campaign_status(self):
        self.env.cr.execute(""" UPDATE utm_campaign
                                                    SET campaign_status = '3'
                                                    WHERE campaign_status != '3' and end_date < (CURRENT_DATE at time zone 'utc');""")
        self.env.cr.execute(""" UPDATE utm_campaign
                                                    SET campaign_status = '2'
                                                    WHERE campaign_status = '1' AND start_date <= (CURRENT_DATE at time zone 'utc') 
                                                                            AND end_date >= (CURRENT_DATE at time zone 'utc');""")


class ResCompany(models.Model):
    _inherit = 'res.company'

    brand_id = fields.Many2one('res.brand', string='Brand')
    brand_ids = fields.Many2many('res.brand', string='Brands')

    @api.onchange('brand_id')
    def set_brand_ids(self):
        if self.brand_id:
            self.brand_ids = [(4, self.brand_id.id)]


class PriceList(models.Model):
    _inherit = 'product.pricelist'

    brand_id = fields.Many2one('res.brand', string='Brand')
    start_date = fields.Date('Start date')
    end_date = fields.Date('End date')
    type = fields.Selection([('service', 'Service'), ('guarantee', 'Guarantee'), ('product', 'Product')],
                            string='Type price list',
                            default='service')


class CrmPayment(models.Model):
    _inherit = 'account.payment'

    crm_id = fields.Many2one('crm.lead', string='Booking/lead', tracking=True)
    brand_id = fields.Many2one('res.brand', string='Brand', related='company_id.brand_id', store=True)
    # company2_id = fields.Many2one('res.company', string='Company shared')
    currency_rate_id = fields.Many2one('res.currency.rate', string='Currency rate',
                                       domain="[('currency_id','=',currency_id)]")
    amount_vnd = fields.Float('Amount vnd', compute='set_amount_vnd', store=True, digits=(3, 0))
    payment_method = fields.Selection(
        [('tm', 'Tiền mặt'), ('ck', 'Chuyển khoản'), ('nb', 'Thanh toán nội bộ'), ('pos', 'Quẹt thẻ qua POS'),
         ('vdt', 'Thanh toán qua ví điện tử')], string='Payment method')
    format_phone = fields.Char('Điện thoại', compute='_get_format_phone')
    communication = fields.Text(string='Memo', readonly=True, states={
        'draft': [('readonly', False)]})  # Kế thừa field này từ base và đổi kiểu từ Char -> Text
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True,
                                 store=True)

    @api.constrains('payment_date', 'crm_id')
    def validate_payment_date(self):
        for record in self:
            if record.payment_date and (record.payment_date.strftime('%d-%m-%Y') != '31-10-2021') and record.crm_id and (record.payment_date > (record.create_date + timedelta(days=2)).date()):
                raise ValidationError('Ngày thanh toán chỉ hợp lệ trong vòng 2 ngày kể từ ngày tạo')
            if record.payment_date and (record.payment_date.strftime('%d-%m-%Y') != '31-10-2021') and record.crm_id and (record.payment_date < (record.create_date - timedelta(days=2)).date()):
                raise ValidationError('Ngày thanh toán chỉ hợp lệ trong vòng 2 ngày kể từ ngày tạo')

    def unlink(self):
        if any(rec.state not in ['draft'] for rec in self):
            raise ValidationError("Bạn chỉ có thể xóa phiếu ở trạng thái Nháp")
        return super(CrmPayment, self).unlink()

    @api.onchange('partner_id', 'payment_type')
    def get_crm_id(self):
        """
        Đối với những phiếu thu là thu tiền thì chỉ chọn được Booking không phải out sold hoặc hủy
        """
        domain = [('partner_id', '=', self.partner_id.id), ('type', '=', 'opportunity')]
        if self.partner_id and self.payment_type != 'outbound':
            domain += [('stage_id', 'not in',
                        [self.env.ref('crm_base.crm_stage_cancel').id, self.env.ref('crm_base.crm_stage_out_sold').id])]
        return {'domain': {'crm_id': [('id', 'in', self.env['crm.lead'].search(domain).ids)]}}

    @api.depends('partner_id')
    def _get_format_phone(self):
        """ Chức năng của hàm:
        Với mỗi số điện thoại được truyền vào, sẽ đưa số điện thoại về dạng 000xxx0000
        """
        for record in self:
            record.format_phone = False
            if record.partner_id.phone:
                str_phone = str(record.partner_id.phone)
                record.format_phone = str(str_phone)[:3] + '***' + str(str_phone)[6:]

    @api.constrains('amount_vnd')
    def check_refund(self):
        for rec in self:
            if rec.payment_type == 'outbound' and rec.amount_vnd and rec.crm_id and \
                    rec.amount_vnd > rec.crm_id.amount_remain:
                raise ValidationError(_('The refund amount larger than the existing customer amount'))

    @api.onchange('currency_id')
    def back_value(self):
        self.currency_rate_id = False
        # quy đổi tiền về tiền việt
        self.text_total = self.num2words_vnm(round(self.amount_vnd)) + " đồng"

    @api.depends('currency_rate_id', 'amount', 'currency_id')
    def set_amount_vnd(self):
        for rec in self:
            rec.amount_vnd = 0
            if rec.amount:
                if rec.currency_id and rec.currency_id == self.env.ref('base.VND'):
                    rec.amount_vnd = rec.amount * 1
                elif rec.currency_rate_id and rec.currency_id != self.env.ref('base.VND'):
                    rec.amount_vnd = rec.amount / rec.currency_rate_id.rate

                # quy đổi tiền về tiền việt
                rec.text_total = self.num2words_vnm(round(rec.amount_vnd)) + " đồng"

    # overwrite lại hàm thay đổi tiền
    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount and self.amount > 0:
            # neu currency là VND
            if self.currency_id == self.env.ref('base.VND'):
                self.text_total = self.num2words_vnm(round(self.amount)) + " đồng"
            # neu currency khác
            else:
                self.text_total = self.num2words_vnm(round(self.amount_vnd)) + " đồng"
        elif self.amount and self.amount < 0:
            raise ValidationError(
                _('Số tiền thanh toán không hợp lệ!'))
        else:
            self.text_total = "Không đồng"

    @api.onchange('crm_id')
    def set_partner(self):
        for rec in self:
            if rec.crm_id and rec.state == 'draft':
                rec.partner_id = rec.crm_id.partner_id.id

    def post(self):
        res = super(CrmPayment, self).post()
        crm = self.crm_id
        if crm and crm.type == 'opportunity' and crm.stage_id in [self.env.ref('crm_base.crm_stage_not_confirm'),
                                                                  self.env.ref('crm_base.crm_stage_no_come'),
                                                                  self.env.ref('crm_base.crm_stage_confirm')]:
            crm.stage_id = self.env.ref('crm_base.crm_stage_paid').id
            crm.day_expire = False
        if (crm.amount_paid == 0) and (crm.stage_id == self.env.ref('crm_base.crm_stage_paid')) and (
                crm.customer_come == 'yes'):
            crm.stage_id = self.env.ref('crm_base.crm_stage_out_sold').id
            crm.reason_out_sold = 'think_more'
            crm.effect = 'expire'
            crm.crm_line_ids.write({
                'stage': 'cancel',
                'note': 'Booking out sold',
                'status_cus_come': 'come_no_service'
            })
        if (crm.amount_paid == 0) and (crm.stage_id == self.env.ref('crm_base.crm_stage_paid')) and (
                crm.customer_come == 'no'):
            crm.stage_id = self.env.ref('crm_base.crm_stage_cancel').id
            crm.reason_cancel_booking = 'cus_cancel_booking_date'
            crm.effect = 'expire'
            crm.crm_line_ids.write({
                'stage': 'cancel',
                'reason_line_cancel': 'consider_more',
                'note': 'Booking hủy',
                'status_cus_come': 'come_no_service',
                'cancel_user': self.env.user,
                'cancel_date': datetime.now()
            })

        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CrmPayment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
        doc = etree.XML(res['arch'])

        VND = self.env.ref('base.VND').id

        if view_type == 'form':
            for node in doc.xpath("//field[@name='currency_rate_id']"):
                node.set("attrs", "{'required':[('currency_id','!=',%s)]}" % VND)
                modifiers = json.loads(node.get("modifiers"))
                modifiers['required'] = "[('currency_id','!=',%s)]" % VND
                node.set('modifiers', json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    crm_line_id = fields.Many2one('crm.line', string='Crm line')
    brand_id = fields.Many2one('res.brand', string='Brand', related='company_id.brand_id', store=True)
    amount_remain = fields.Monetary('Amount remain', related='booking_id.amount_remain', store=True)
    document_related = fields.Char('Document related')
    booking_id = fields.Many2one('crm.lead', string='Booking', domain="[('type','=','opportunity')]")
    # amount_receivable = fields.Monetary('Tổng tiền phải thu', compute='compute_amount_receivable', store='True')
    debt_review_id = fields.Many2many('crm.debt.review', 'sale_order_debt_review_rel', 'sale_order_id',
                                      'debt_review_id', 'Phiếu duyệt nợ')
    amount_owed = fields.Monetary('Số tiền được duyệt nợ', compute='compute_amount_owed', store=True)
    code_customer = fields.Char(related='partner_id.code_customer', string='Mã khách hàng')
    phone_customer = fields.Char(related='partner_id.phone', string='Điện thoại')
    pricelist_type = fields.Selection(related='pricelist_id.type', string='Loại bảng giá', store=True)
    company_allow_ids = fields.Many2many('res.company', 'sale_order_company_allow_ref', string='Công ty cho phép')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(SaleOrder, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone_customer']:
                fields[field_name]['exportable'] = False

        return fields

    @api.depends('debt_review_id')
    def compute_amount_owed(self):
        for record in self:
            record.amount_owed = 0
            if record.debt_review_id:
                owed = 0
                for debt in record.debt_review_id:
                    if not debt.paid:
                        owed += debt.amount_owed
                record.amount_owed = owed

    # @api.depends('debt_review_id.amount_owed', 'debt_review_id.paid', 'amount_total', 'amount_remain')
    # def compute_amount_receivable(self):
    #     for record in self:
    #         record.amount_receivable = 0
    #         if record.debt_review_id and not record.debt_review_id.paid:
    #             record.amount_receivable = record.amount_total - record.amount_remain - record.amount_owed
    #         else:
    #             record.amount_receivable = record.amount_total - record.amount_remain

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # self.pricelist_id = None
        if self.company_id.brand_id:
            return {
                'domain': {
                    'pricelist_id': [('brand_id', '=', self.company_id.brand_id.id), ('type', '=', 'product')]}
            }

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        self.pricelist_id = None
        if self.company_id.brand_id:
            return {
                'domain': {
                    'pricelist_id': [('brand_id', '=', self.company_id.brand_id.id), ('type', '=', 'product')]}
            }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.booking_id and self.pricelist_type != 'product':
            self.booking_id.stage_id = self.env.ref('crm.stage_lead4').id
            self.booking_id.effect = 'expire'
            self.booking_id.booking_notification = "Booking thành công. Bạn chỉ có thể tạo được phiếu khám từ Booking này."
        return res

    def open_discount_review(self):
        if not self.order_line:
            raise ValidationError(_('SO does not contain services'))
        else:
            return {
                'name': 'GIẢM GIÁ SÂU',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_base.view_discount_review').id,
                'res_model': 'discount.review',
                'context': {
                    'default_order_id': self.id,
                    'default_type': 'so',
                    'default_partner_id': self.partner_id.id,
                },
                'target': 'new',
            }

    def _create_invoices(self, grouped=False, final=False, journal_id=False, invoice_date=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Hải IT: Nếu có truyền vào invoice_date thì đem ngày này đi tạo hóa đơn
            if invoice_date:
                invoice_vals['invoice_date'] = invoice_date

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(
                    _('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)
        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list,
                                                   key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs),
                    'invoice_origin': ', '.join(origins),
                    'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Manage 'final' parameter: transform out_invoice to out_refund if negative.
        out_invoice_vals_list = []
        refund_invoice_vals_list = []
        if final:
            for invoice_vals in invoice_vals_list:
                if sum(l[2]['quantity'] * l[2]['price_unit'] for l in invoice_vals['invoice_line_ids']) < 0:
                    for l in invoice_vals['invoice_line_ids']:
                        l[2]['quantity'] = -l[2]['quantity']
                    invoice_vals['type'] = 'out_refund'
                    refund_invoice_vals_list.append(invoice_vals)
                else:
                    out_invoice_vals_list.append(invoice_vals)
        else:
            out_invoice_vals_list = invoice_vals_list
        # Cho phép tạo account.move với journal_id được chỉ định (Hải IT)
        if journal_id:
            out_invoice_vals_list[0].update({'journal_id': journal_id})
        # Create invoices.
        moves = self.env['account.move'].with_context(default_type='out_invoice').create(out_invoice_vals_list)
        moves += self.env['account.move'].with_context(default_type='out_refund').create(refund_invoice_vals_list)

        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                                        values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                        subtype_id=self.env.ref('mail.mt_note').id
                                        )
        return moves

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        doc = etree.XML(res['arch'])

        if view_type == 'form':
            for node in doc.xpath("//field[@name='order_line']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='partner_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='partner_invoice_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='partner_shipping_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='sale_order_template_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='date_order']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='pricelist_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='set_total']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='user_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='company_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='warehouse_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='sh_room_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            # for node in doc.xpath("//field[@name='booking_id']"):
            #     node.set("attrs", "{'readonly':['|',('pricelist_type', '=', 'service'), ('state', '!=', 'draft')]}")
            #     modifiers = json.loads(node.get("modifiers"))
            #     modifiers['readonly'] = "['|',('pricelist_type', '=', 'service'), ('state', '!=', 'draft')]"
            #     node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='booking_id']"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))

            for node in doc.xpath("//field[@name='campaign_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='medium_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='source_id']"):
                node.set("attrs",
                         "{'readonly':['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers[
                    'readonly'] = "['|',('pricelist_type', 'in', ['service', 'guarantee']), ('state', '!=', 'draft')]"
                node.set('modifiers', json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    crm_line_id = fields.Many2one('crm.line', string='Crm line')
    booking_id = fields.Many2one('crm.lead', related='order_id.booking_id')
    partner_id = fields.Many2one('res.partner', related='order_id.partner_id')
    pricelist_type = fields.Selection('res.partner', related='order_id.pricelist_type', store=True)
    date_order = fields.Datetime('Ngày đặt hàng', related='order_id.date_order', store=True)
    order_state = fields.Selection('Trạng thái', related='order_id.state')
    discount_cash = fields.Monetary('Discount cash')
    sale_to = fields.Monetary('Sale to')
    other_discount = fields.Monetary('Other discount')
    uom_price = fields.Float('cm2/cc/unit/...', default=1)

    # @api.constrains('price_unit')
    # def error_discount_cash(self):
    #     for rec in self:
    #         if rec.discount_cash > rec.price_unit * (1 - (rec.discount or 0.0) / 100.0) or rec.discount_cash < 0:
    #             raise ValidationError(_('Invalid discount'))
    @api.onchange('order_id', 'product_id')
    def onchange_product(self):
        if self.order_id and self.product_id:
            price_list = self.order_id.pricelist_id
            pricelist_item = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', price_list.id), ('product_id', '=', self.product_id.id)])
            if pricelist_item:
                self.price_unit = pricelist_item.fixed_price

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'uom_price', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    if line.uom_price:
                        line.qty_to_invoice = (line.product_uom_qty * line.uom_price) - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('product_uom_qty', 'discount', 'discount_cash', 'price_unit', 'tax_id', 'uom_price', 'other_discount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.sale_to == 0:
                price = line.price_unit * (
                        1 - (line.discount or 0.0) / 100.0) - line.discount_cash - line.other_discount
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)
                total = line.price_unit * line.product_uom_qty * line.uom_price * (
                        1 - (line.discount or 0.0) / 100.0) - line.discount_cash - line.other_discount
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': total,
                    'price_subtotal': total,
                })
            else:
                total = line.sale_to * line.product_uom_qty
                line.update({
                    'price_total': total,
                    'price_subtotal': total,
                })

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()

        # check giá phải > 0 thì mới tính discount
        if (self.price_unit > 0) and (self.uom_price * self.product_uom_qty != 0):
            discount = 100 * (1 - self.price_subtotal / self.price_unit / self.product_uom_qty / self.uom_price)
        else:
            discount = 0
        self._get_to_invoice_qty()
        return {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            # 'quantity': self.qty_to_invoice * self.uom_price,
            'quantity': self.qty_to_invoice,
            'discount': discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }


class ProductCategory(models.Model):
    _inherit = 'product.category'

    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    code = fields.Char("Mã")

    def name_get(self):
        if self.env.context.get('s_product_cate'):
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            return [(template.id, '%s%s' % (template.code and '[%s] ' % template.code or '', template.name))
                    for template in self]
        return super(ProductCategory, self).name_get()


class Product(models.Model):
    _inherit = 'product.product'

    type_product_crm = fields.Selection([('course', 'Course'), ('service_crm', 'Service'), ('product', 'Product')],
                                        string='Type Product crm')


class TypeSource(models.Model):
    _name = 'type.source'
    _description = 'Type source'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)


class CategorySource(models.Model):
    _name = 'crm.category.source'
    _description = 'Category Source'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('code_category_source_uniq', 'unique(code)', 'This code already exists!')
    ]


class TagSource(models.Model):
    _name = 'crm.tag.source'
    _description = 'Tag Source'
    name = fields.Char('Name')
    code = fields.Integer('Code tag source')

    # đồng bộ source mkt
    # @api.model
    # def sync_source_mkt(self):
    # tags = self.env['crm.tag.source'].search([]).mapped('code')
    #
    # sync = self.env.ref('crm_base.sync_insight')
    # odoo = odoorpc.ODOO(host=sync.ip, port=sync.port)
    # odoo.login(sync.database, sync.user, sync.password)
    # source_mkt = odoo.env['source.mkt'].search_read(domain=[('id', 'not in', tags)], fields=['name'])
    # for sr in source_mkt:
    #     self.env['crm.tag.source'].create({
    #         'name': sr['name'],
    #         'code': sr['id'],
    #     })


class UtmSource(models.Model):
    _inherit = 'utm.source'

    type_source_id = fields.Many2one('type.source', string='Type source')
    active = fields.Boolean('Active', default=True)
    code = fields.Char('Code')
    category_id = fields.Many2one('crm.category.source', string='Category source')
    utm_source_ins_id = fields.Integer('Insight source')
    tag_ids = fields.Many2many('crm.tag.source', string='Tags source')
    type_source = fields.Selection([('online', 'Online'), ('offline', 'Offline')], string='Loại')
    original_source = fields.Boolean('Nguồn ban đầu')
    extend_source = fields.Boolean('Nguồn mở rộng')
    accounting_source_category = fields.Many2one('crm.category.source', string='Nhóm nguồn dành cho kế toán')
    khach_hang_gioi_thieu = fields.Boolean('Cần điền khách hàng giới thiệu')

    _sql_constraints = [
        ('code_source_uniq', 'unique(code)', 'This code already exists!')
    ]


class PriceUnitItem(models.Model):
    _inherit = 'product.pricelist.item'

    price_currency_usd = fields.Float('Unit price usd')
    rate_currency_id = fields.Many2one('res.currency.rate', string='Rate currency')
    product_default_code = fields.Char(related='product_id.default_code', string='Mã biến thể', store=True)

    @api.onchange('rate_currency_id', 'price_currency_usd')
    def set_fix_price(self):
        self.fixed_price = 0
        if self.rate_currency_id:
            self.fixed_price = self.price_currency_usd / self.rate_currency_id.rate

    @api.model
    def cron_set_rate(self, list_item=[]):
        if list_item:
            items = self.env['product.pricelist.item'].search(
                [('price_currency_usd', '>', 0), ('id', 'not in', list_item)], limit=200).ids
            if items:
                list_item += items
            else:
                list_item = []
                self.env.ref('crm_base.set_rate').nextcall = (fields.Datetime.now() + timedelta(days=1)).replace(
                    hour=9, minute=0, second=0)

        else:
            items = self.env['product.pricelist.item'].search([('price_currency_usd', '>', 0)], limit=200).ids
            if items:
                list_item += items
                self.env.ref('crm_base.set_rate').nextcall = fields.Datetime.now() + timedelta(minutes=10)
            else:
                self.env.ref('crm_base.set_rate').nextcall = (fields.Datetime.now() + timedelta(days=1)).replace(
                    hour=9, minute=0, second=0)

        self.env.ref('crm_base.set_rate').code = 'model.cron_set_rate(%s)' % (list_item)
        rate = self.env['res.currency.rate'].search([('currency_id', '=', self.env.ref("base.USD").id)])[0]

        if items:
            for item in items:
                self.env['product.pricelist.item'].browse(item).rate_currency_id = rate.id
                self.env['product.pricelist.item'].browse(item).set_fix_price()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_cash = fields.Monetary('Discount cash')


class GuaranteeCustomer(models.Model):
    _inherit = 'res.partner'

    def booking_guarantee(self):
        return {
            'name': 'Booking bảo hành',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_create_booking_guarantee').id,
            'res_model': 'crm.create.guarantee',
            'context': {
                'default_partner_id': self.id,
                'default_brand_id': self.env.company.brand_id.id,
            },
            'target': 'new',
        }

    def cron_sms_birth_date(self):
        today = fields.Date.today()
        month = today.month
        day = today.day
        data_customer = self.env['res.partner'].search([('code_customer', '!=', None)])
        for lt in data_customer:
            if lt.id not in [412835]:
                continue
            if lt.birth_date and lt.birth_date.month == month \
                    and lt.birth_date.day == day:
                my_dict = {}
                for booking in lt.crm_ids:
                    if not my_dict.get(booking.brand_id.id):
                        # gửi SMS chúc mừng sinh nhật khách hàng
                        script_sms = booking.company_id.script_sms_id
                        content_sms = ''
                        for item in script_sms:
                            if item.run:
                                if item.type == 'CMSN':
                                    content_sms = item.content.replace('[Ten_KH]', booking.contact_name)
                                    content_sms = content_sms.replace('[Ma_Booking]', booking.name)
                                    content_sms = content_sms.replace('[Booking_Date]',
                                                                      booking.booking_date.strftime('%d-%m-%Y'))
                                    content_sms = content_sms.replace('[Location_Shop]',
                                                                      booking.company_id.location_shop)
                                    content_sms = content_sms.replace('[Ban_Do]', booking.company_id.map_shop)
                                    if booking.company_id.health_declaration:
                                        content_sms = content_sms.replace('[Khai_Bao]',
                                                                          booking.company_id.health_declaration)
                                    break
                        if content_sms:
                            my_dict[booking.brand_id.id] = {
                                'name': 'SMS chúc mừng sinh nhật KH',
                                'contact_name': booking.contact_name,
                                'partner_id': booking.partner_id.id,
                                'phone': booking.phone,
                                'company_id': booking.company_id.id,
                                'crm_id': booking.id,
                                'send_date': fields.Datetime.now().replace(hour=1, minute=0, second=0),
                                'create_by': 1,
                                'desc': content_sms,
                            }
                for key in my_dict:
                    sms = self.env['crm.sms'].sudo().create(my_dict[key])


class CtvLead(models.Model):
    _inherit = 'crm.lead'

    check_country = fields.Boolean('check country', compute='_check_country', store=False)

    @api.depends('country_id', 'brand_id')
    def _check_country(self):
        for record in self:
            record.check_country = False
            if record.brand_id.code == 'DA' and record.country_id.code == 'VN':
                record.check_country = True
            else:
                record.check_country = False
