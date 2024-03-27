import json
from datetime import datetime
from odoo.addons.queue_job.job import job
from odoo import models, api, fields, _

from ..helper import call_api, update_record, get_ent_id, create_records, delete_record, remove_duplicate

api_url = "onnet_sci_api.accounting_api_url"
access_token = "onnet_sci_api.token_enterprise"


class ProductCategoryInherit(models.Model):
    _inherit = "product.category"

    code = fields.Char(string=_("Mã"), index=True)

    @job
    def sync_record(self, id):
        cate = self.sudo().browse(id)
        val = {
            "property_account_creditor_price_difference_categ": get_ent_id(self, 'account.account',
                                                                           cate.property_account_creditor_price_difference_categ.id),
            "property_account_expense_categ_id": get_ent_id(self, 'account.account',
                                                            cate.property_account_expense_categ_id.id),
            "property_account_income_categ_id": get_ent_id(self, 'account.account',
                                                           cate.property_account_income_categ_id.id),
            # "property_stock_account_input_categ_id": get_ent_id(self, 'account.account',
            #                                                     cate.property_stock_account_input_categ_id.id),
            # "property_stock_account_output_categ_id": get_ent_id(self, 'account.account',
            #                                                      cate.property_stock_account_output_categ_id.id),
            # "property_stock_valuation_account_id": get_ent_id(self, 'account.account',
            #                                                   cate.property_stock_valuation_account_id.id),
            "complete_name": cate.complete_name,
            "display_name": cate.display_name,
            "name": cate.name,
            "code": cate.code,
            # "property_cost_method": cate.property_cost_method,
            # "property_valuation": cate.property_valuation,
            "parent_id": get_ent_id(self, 'product.category', cate.parent_id.id),
            "com_id": id
        }
        return update_record(self, 'product.category', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductCategoryInherit, self).create(vals_list)
        if res:
            for cate in res:
                self.sudo().with_delay(channel='sync_product').sync_record(cate.id)

        return res

    def write(self, vals):
        res = super(ProductCategoryInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ProductCategoryInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.category', rec.id)


class UomCategoryInherit(models.Model):
    _inherit = "uom.category"

    @job
    def sync_record(self, id):
        uom_cate = self.sudo().browse(id)
        val = {
            "name": uom_cate.name
        }
        return update_record(self, 'uom.category', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(UomCategoryInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay(channel='sync_uom_category').sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(UomCategoryInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_uom_category')
                self.sudo().with_delay(channel='sync_uom_category').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(UomCategoryInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'uom.category', rec.id)


class UomInherit(models.Model):
    _inherit = "uom.uom"

    @job
    def sync_record(self, id):
        uom = self.sudo().browse(id)
        val = {
            "name": uom.name,
            "category_id": get_ent_id(self, 'uom.category', uom.category_id.id),
            "factor": uom.factor,
            "rounding": uom.rounding,
            "uom_type": uom.uom_type,
            "com_id": id
        }
        return update_record(self, 'uom.uom', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(UomInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay(channel='sync_uom_uom').sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(UomInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_uom_uom')
                self.sudo().with_delay(channel='sync_uom_uom').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(UomInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'uom.uom', rec.id)


class ProductAttributeInherit(models.Model):
    _inherit = "product.attribute"

    @job
    def sync_record(self, id):
        product_attr = self.sudo().browse(id)
        val = {
            "create_variant": product_attr.create_variant,
            "name": product_attr.name,
            "display_type": product_attr.display_type,
            "sequence": product_attr.sequence,
            "com_id": id
        }
        return update_record(self, 'product.attribute', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductAttributeInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(ProductAttributeInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ProductAttributeInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.attribute', rec.id)


class ProductAttributeValueInherit(models.Model):
    _inherit = "product.attribute.value"

    @job
    def sync_record(self, id):
        product_attr_value = self.sudo().browse(id)
        val = {
            "attribute_id": get_ent_id(self, 'product.attribute', product_attr_value.attribute_id.id),
            "name": product_attr_value.name,
            "html_color": product_attr_value.html_color,
            "is_custom": product_attr_value.is_custom,
            "sequence": product_attr_value.sequence,
            "com_id": id
        }
        return update_record(self, 'product.attribute.value', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductAttributeValueInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(ProductAttributeValueInherit, self).write(vals)
        if res:
            for rec in self:
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)

        return res

    def unlink(self):
        res = super(ProductAttributeValueInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.attribute.value', rec.id)


class ProductAttributeLineInherit(models.Model):
    _inherit = "product.template.attribute.line"

    @job
    def sync_record(self, id):
        product_attr_line = self.sudo().browse(id)
        value_ids = [get_ent_id(self, 'product.attribute.value', val_id) for val_id in product_attr_line.value_ids.ids]
        val = {
            "attribute_id": get_ent_id(self, 'product.attribute', product_attr_line.attribute_id.id),
            "product_tmpl_id": get_ent_id(self, 'product.template', product_attr_line.product_tmpl_id.id),
            "active": product_attr_line.active,
            "value_ids": [[6, False, value_ids]],
            "com_id": id
        }
        return update_record(self, 'product.template.attribute.line', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductAttributeLineInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(ProductAttributeLineInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ProductAttributeLineInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.template.attribute.line', rec.id)


class ProductTemplateAttributeValueInherit(models.Model):
    _inherit = "product.template.attribute.value"

    @job
    def sync_record(self, id):
        product_tmp_attr_value = self.sudo().browse(id)
        val = {
            "attribute_line_id": get_ent_id(self, 'product.template.attribute.line',
                                            product_tmp_attr_value.attribute_line_id.id),
            "price_extra": product_tmp_attr_value.price_extra,
            "product_attribute_value_id": get_ent_id(self, 'product.attribute.value',
                                                     product_tmp_attr_value.product_attribute_value_id.id),
            "ptav_active": product_tmp_attr_value.ptav_active,
            "com_id": id
        }
        return update_record(self, 'product.template.attribute.value', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductTemplateAttributeValueInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(ProductTemplateAttributeValueInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ProductTemplateAttributeValueInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.template.attribute.value', rec.id)


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    @job
    def sync_record(self, id):
        product_tml = self.sudo().browse(id)
        categ_id = get_ent_id(self, 'product.category', product_tml.categ_id.id)
        val = {
            "default_code": product_tml.default_code,
            "name": product_tml.name,
            "uom_name": product_tml.uom_id.name,
            "categ_id": categ_id,
            "uom_id": get_ent_id(self, 'uom.uom', product_tml.uom_id.id),
            "uom_po_id": get_ent_id(self, 'uom.uom', product_tml.uom_po_id.id),
            "com_id": id
        }
        return update_record(self, 'product.template', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductTemplateInherit, self).create(vals_list)
        if res:
            for product_tml in res:
                self.sudo().with_delay(channel='sync_product').sync_record(product_tml.id)

        return res

    def write(self, vals):
        res = super(ProductTemplateInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ProductTemplateInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.template', rec.id)


class ProductProductInherit(models.Model):
    _inherit = "product.product"

    @job
    def sync_record(self, id, keys=None):
        product = self.sudo().browse(id)
        categ_id = get_ent_id(self, 'product.category', product.categ_id.id)
        ent_attribute_value_ids = [get_ent_id(self, 'product.template.attribute.value', pro_attr_id) for pro_attr_id in product.product_template_attribute_value_ids.ids]
        val = {
            "combination_indices": ','.join([str(i) for i in sorted(ent_attribute_value_ids)]),
            "name": product.name,
            "categ_id": categ_id,
            "cost_currency_id": product.cost_currency_id.name,
            "uom_id": get_ent_id(self, 'uom.uom', product.uom_id.id),
            "uom_po_id": get_ent_id(self, 'uom.uom', product.uom_po_id.id),
            "default_code": product.default_code,
            "product_tmpl_id": get_ent_id(self, 'product.template', product.product_tmpl_id.id),
            "com_id": id
        }
        update = False
        if keys:
            for key in keys:
                if val.get(key, False):
                    update = True
                    break
        else:
            update = True
        if update:
            return update_record(self, 'product.product', val, id)
        else:
            return False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductProductInherit, self).create(vals_list)
        if res:
            for product in res:
                self.sudo().with_delay(channel='sync_product').sync_record(product.id)

        return res

    def write(self, vals):
        res = super(ProductProductInherit, self).write(vals)
        keys = [key for key in vals.keys()]
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id, keys)
        return res

    # def unlink(self):
    #     res = super(ProductProductInherit, self).unlink()
    #     if res:
    #         for rec in self:
    #             delete_record(self, 'product.product', rec.id)


class PriceListInherit(models.Model):
    _inherit = "product.pricelist"

    @job
    def sync_record(self, id):
        pricelist = self.sudo().browse(id)
        if pricelist:
            val = {
                "name": pricelist.name,
                "active": pricelist.active,
                "display_name": pricelist.display_name,
                "start_date": pricelist.start_date and pricelist.start_date.strftime('%Y-%m-%d') or False,
                "end_date": pricelist.end_date and pricelist.end_date.strftime('%Y-%m-%d') or False,
                "discount_policy": pricelist.discount_policy,
                "type": pricelist.type,
                "com_id": id
            }
            return update_record(self, 'product.pricelist', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(PriceListInherit, self).create(vals_list)
        if res:
            for pricelist in res:
                self.sudo().with_delay(channel='sync_product').sync_record(pricelist.id)

        return res

    def write(self, vals):
        res = super(PriceListInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_product')
                self.sudo().with_delay(channel='sync_product').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(PriceListInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'product.pricelist', rec.id)


class ResCurrencyInherit(models.Model):
    _inherit = "res.currency"

    @job
    def sync_record(self, id):
        currency = self.sudo().browse(id)
        val = {
            "currency_subunit_label": currency.currency_subunit_label,
            "active": currency.active,
            "currency_unit_label": currency.currency_unit_label,
            "display_name": currency.display_name,
            "name": currency.name,
            "rate": currency.rate,
            "rounding": currency.rounding,
            "position": currency.position,
            "decimal_places": currency.decimal_places,
            "symbol": currency.symbol,
            "com_id": id
        }
        return update_record(self, 'res.currency', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResCurrencyInherit, self).create(vals_list)
        if res:
            for currency in res:
                self.sudo().with_delay(channel='sync_res_currency').sync_record(currency.id)

        return res

    def write(self, vals):
        res = super(ResCurrencyInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_res_currency')
                self.sudo().with_delay(channel='sync_res_currency').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResCurrencyInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.currency', rec.id)


class ProjectProjectInherit(models.Model):
    _inherit = "project.project"

    @job
    def sync_record(self, id):
        project = self.sudo().browse(id)
        val = {
            "analytic_account_id": get_ent_id(self, 'account.analytic.account', project.analytic_account_id.id),
            "active": project.active,
            "display_name": project.display_name,
            "name": project.name,
            "date_start": project.date_start and project.date_start.strftime('%Y-%m-%d') or False,
            "label_tasks": project.label_tasks,
            "alias_name": project.alias_name,
            "alias_domain": project.alias_domain,
            "date": project.date and project.date.strftime('%Y-%m-%d') or False,
            "company_id": get_ent_id(self, 'res.company', project.company_id.id),
            "com_id": id
        }
        return update_record(self, 'project.project', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProjectProjectInherit, self).create(vals_list)
        if res:
            for project in res:
                self.sudo().with_delay(channel='sync_project_project').sync_record(project.id)

        return res

    def write(self, vals):
        res = super(ProjectProjectInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_project_project')
                self.sudo().with_delay(channel='sync_project_project').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ProjectProjectInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'project.project', rec.id)


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    @job
    def sync_record(self, id):
        partner = self.sudo().browse(id)
        val = {
            "property_purchase_currency_id": get_ent_id(self, 'res.currency', partner.property_purchase_currency_id.id),
            "property_account_receivable_id": get_ent_id(self, 'account.account', partner.property_account_receivable_id.id),
            "property_account_payable_id": get_ent_id(self, 'account.account', partner.property_account_payable_id.id),
            "active": partner.active,
            "employee": partner.employee,
            "display_name": partner.display_name,
            "name": partner.name,
            "has_unreconciled_entries": partner.has_unreconciled_entries,
            "code_customer": partner.code_customer,
            "is_company": partner.is_company,
            "company_name": partner.company_name,
            "email": partner.email,
            "function": partner.function,
            "mobile": partner.mobile,
            "phone": partner.phone,
            "street": partner.street,
            "street2": partner.street2,
            "ref": partner.ref,
            "birth_date": partner.birth_date and partner.birth_date.strftime('%Y-%m-%d') or False,
            "gender": partner.gender,
            "career": partner.career,
            "city": partner.city,
            "vat": partner.vat,
            "supplier_rank": partner.supplier_rank,
            "com_id": id
        }
        return update_record(self, 'res.partner', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResPartnerInherit, self).create(vals_list)
        if res:
            for partner in res:
                self.sudo().with_delay(channel='sync_res_company').sync_record(partner.id)

        return res

    def write(self, vals):
        res = super(ResPartnerInherit, self).write(vals)
        if res:
            for rec in self:
                # TODO: SCI rào lại: ảnh hưởng tới hiệu năng api tạo booking
                # remove_duplicate(rec, 'sync_res_company')
                self.sudo().with_delay(channel='sync_res_company').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResPartnerInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.partner', rec.id)


class ResBankInherit(models.Model):
    _inherit = "res.bank"

    @job
    def sync_record(self, id):
        bank = self.sudo().browse(id)
        val = {
            "active": bank.active,
            "bic": bank.bic,
            "city": bank.city,
            "country": get_ent_id(self, 'res.country', bank.country.id),
            "email": bank.email,
            "name": bank.name,
            "state": get_ent_id(self, 'res.country.state', bank.state.id),
            "street": bank.street,
            "street2": bank.street2,
            "zip": bank.zip,
            "com_id": id
        }
        return update_record(self, 'res.bank', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResBankInherit, self).create(vals_list)
        if res:
            for bank in res:
                self.sudo().with_delay(channel='res_bank').sync_record(bank.id)

        return res

    def write(self, vals):
        res = super(ResBankInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'res_bank')
                self.sudo().with_delay(channel='res_bank').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResBankInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.bank', rec.id)


class ResPartnerBankInherit(models.Model):
    _inherit = "res.partner.bank"

    @job
    def sync_record(self, id):
        bank = self.sudo().browse(id)
        val = {
            "acc_holder_name": bank.acc_holder_name,
            "acc_number": bank.acc_number,
            "bank_bic": bank.bank_bic,
            "bank_name": bank.bank_name,
            "display_name": bank.display_name,
            "sanitized_acc_number": bank.sanitized_acc_number,
            "acc_type": bank.acc_type,
            "bank_id": get_ent_id(self, 'res.bank', bank.bank_id.id),
            "partner_id": get_ent_id(self, 'res.partner', bank.partner_id.id),
            "com_id": id
        }
        return update_record(self, 'res.partner.bank', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResPartnerBankInherit, self).create(vals_list)
        if res:
            for bank in res:
                self.sudo().with_delay(channel='sync_res_partner_bank').sync_record(bank.id)

        return res

    def write(self, vals):
        res = super(ResPartnerBankInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_res_partner_bank')
                self.sudo().with_delay(channel='sync_res_partner_bank').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResPartnerBankInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.partner.bank', rec.id)


class ResPartnerCategoryInherit(models.Model):
    _inherit = "res.partner.category"

    @job
    def sync_record(self, id):
        partner_categ = self.sudo().browse(id)
        val = {
            "partner_ids": partner_categ.partner_ids and [ent.ent_id for ent in
                                                          self.env['records.com.ent.rel'].sudo().search(
                                                              [('model', '=', 'res.partner'),
                                                               ('com_id', 'in', partner_categ.partner_ids.ids)])] or [],
            "active": partner_categ.active,
            "display_name": partner_categ.display_name,
            "name": partner_categ.name,
            "com_id": id
        }
        return update_record(self, 'res.partner.category', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResPartnerCategoryInherit, self).create(vals_list)
        if res:
            for partner_categ in res:
                self.sudo().with_delay(channel='sync_res_partner_category').sync_record(partner_categ.id)

        return res

    def write(self, vals):
        res = super(ResPartnerCategoryInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_res_partner_category')
                self.sudo().with_delay(channel='sync_res_partner_category').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResPartnerCategoryInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.partner.category', rec.id)


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    @job
    def sync_record(self, id):
        company = self.sudo().browse(id)
        val = {
            "account_default_pos_receivable_account_id": company.account_default_pos_receivable_account_id.id and get_ent_id(
                self, 'account.account',
                company.account_default_pos_receivable_account_id.id) or False,
            "account_opening_journal_id": company.account_opening_journal_id.id and get_ent_id(self, 'account.journal',
                                                                                               company.account_opening_journal_id.id) or False,
            "account_opening_move_id": company.account_opening_move_id.id and get_ent_id(self, 'account.move',
                                                                                         company.account_opening_move_id.id) or False,
            "currency_exchange_journal_id": company.currency_exchange_journal_id.id and get_ent_id(self,
                                                                                                   'account.journal',
                                                                                                   company.currency_exchange_journal_id.id) or False,
            "default_cash_difference_expense_account_id": company.default_cash_difference_expense_account_id.id and get_ent_id(
                self, 'account.account',
                company.default_cash_difference_expense_account_id.id) or False,
            "default_cash_difference_income_account_id": company.default_cash_difference_income_account_id.id and get_ent_id(
                self, 'account.account',
                company.default_cash_difference_income_account_id.id) or False,
            "expense_accrual_account_id": company.expense_accrual_account_id.id and get_ent_id(self, 'account.account',
                                                                                               company.expense_accrual_account_id.id) or False,
            "expense_currency_exchange_account_id": company.expense_currency_exchange_account_id.id and get_ent_id(self,
                                                                                                                   'account.account',
                                                                                                                   company.expense_currency_exchange_account_id.id) or False,
            "income_currency_exchange_account_id": company.income_currency_exchange_account_id.id and get_ent_id(self,
                                                                                                                 'account.account',
                                                                                                                 company.income_currency_exchange_account_id.id) or False,
            "revenue_accrual_account_id": company.revenue_accrual_account_id.id and get_ent_id(self, 'account.account',
                                                                                               company.revenue_accrual_account_id.id) or False,
            "tax_cash_basis_journal_id": company.tax_cash_basis_journal_id.id and get_ent_id(self, 'account.journal',
                                                                                             company.tax_cash_basis_journal_id.id) or False,
            "transfer_account_id": company.transfer_account_id.id and get_ent_id(self, 'account.account',
                                                                                 company.transfer_account_id.id) or False,
            "anglo_saxon_accounting": company.anglo_saxon_accounting,
            "expects_chart_of_accounts": company.expects_chart_of_accounts,
            "bank_account_code_prefix": company.bank_account_code_prefix,
            "cash_account_code_prefix": company.cash_account_code_prefix,
            "currency_id": get_ent_id(self, 'res.currency', company.currency_id.id),
            "city": company.city,
            "code": company.code,
            "company_registry": company.company_registry,
            "display_name": company.display_name,
            "email": company.email,
            "name": company.name,
            "phone": company.phone,
            "street": company.street,
            "street2": company.street2,
            "transfer_account_code_prefix": company.transfer_account_code_prefix,
            "vat": company.vat,
            "zip": company.zip,
            "apply_transfer_type": company.apply_transfer_type,
            "base_onboarding_company_state": company.base_onboarding_company_state,
            "fiscalyear_last_month": company.fiscalyear_last_month,
            "tax_calculation_rounding_method": company.tax_calculation_rounding_method,
            "account_opening_date": company.account_opening_date and company.account_opening_date.strftime(
                '%Y-%m-%d') or datetime.today().strftime('%Y-%m-%d'),
            "website": company.website,
            "com_id": id
        }
        return update_record(self, 'res.company', val, id)

    def create_enterprise(self, id):
        company = self.sudo().browse(id)
        val = {
            "anglo_saxon_accounting": company.anglo_saxon_accounting,
            "expects_chart_of_accounts": company.expects_chart_of_accounts,
            "bank_account_code_prefix": company.bank_account_code_prefix,
            "cash_account_code_prefix": company.cash_account_code_prefix,
            "city": company.city,
            "code": company.code,
            "company_registry": company.company_registry,
            "display_name": company.display_name,
            "email": company.email,
            "name": company.name,
            "phone": company.phone,
            "street": company.street,
            "street2": company.street2,
            "transfer_account_code_prefix": company.transfer_account_code_prefix,
            "vat": company.vat,
            "zip": company.zip,
            "currency_id": get_ent_id(self, 'res.currency', company.currency_id.id),
            "apply_transfer_type": company.apply_transfer_type,
            "base_onboarding_company_state": company.base_onboarding_company_state,
            "fiscalyear_last_month": company.fiscalyear_last_month,
            "tax_calculation_rounding_method": company.tax_calculation_rounding_method,
            "account_opening_date": company.account_opening_date and company.account_opening_date.strftime(
                '%Y-%m-%d') or datetime.today().strftime('%Y-%m-%d'),
            "website": company.website,
            "partner_id": get_ent_id(self, 'res.partner', company.partner_id.id),
            "com_id": id
        }
        return update_record(self, 'res.company', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResCompanyInherit, self).create(vals_list)
        if res:
            for company in res:
                self.sudo().with_delay(channel='sync_res_company').create_enterprise(company.id)

        return res

    def write(self, vals):
        fields = ['account_default_pos_receivable_account_id', 'account_opening_journal_id', 'account_opening_move_id',
                  'currency_exchange_journal_id', 'default_cash_difference_expense_account_id',
                  "default_cash_difference_income_account_id", "expense_accrual_account_id",
                  "expense_currency_exchange_account_id", "income_currency_exchange_account_id",
                  "revenue_accrual_account_id", "tax_cash_basis_journal_id", "transfer_account_id",
                  "anglo_saxon_accounting", "expects_chart_of_accounts",
                  "bank_account_code_prefix", "cash_account_code_prefix", "city", "code",
                  "company_registry",
                  "display_name",
                  "currency_id",
                  "email",
                  "name",
                  "phone",
                  "street",
                  "street2",
                  "transfer_account_code_prefix",
                  "vat",
                  "zip",
                  "apply_transfer_type",
                  "base_onboarding_company_state",
                  "fiscalyear_last_month",
                  "tax_calculation_rounding_method",
                  "account_opening_date",
                  "website"]
        res = super(ResCompanyInherit, self).write(vals)
        sync = False
        for field in fields:
            if field in vals:
                sync = True
                break
        if res and sync:
            for rec in self:
                # TODO: SCI rào lại: ảnh hưởng tới hiệu năng api tạo booking
                # remove_duplicate(rec, 'sync_res_company')
                self.sudo().with_delay(channel='sync_res_company').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResCompanyInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.company', rec.id)


class AccountJournalInherit(models.Model):
    _inherit = "account.journal"

    @job
    def sync_record(self, id):
        journal = self.sudo().browse(id)
        val = {
            "name": journal.name,
            "active": journal.active,
            "name": journal.name,
            "activity_summary": journal.activity_summary,
            "bank_acc_number": journal.bank_acc_number,
            "code": journal.code,
            "currency_id": get_ent_id(self, 'res.currency', journal.currency_id.id),
            "invoice_reference_model": journal.invoice_reference_model,
            "invoice_reference_type": journal.invoice_reference_type,
            "type": journal.type,
            "company_id": get_ent_id(self, 'res.company', journal.company_id.id),
            "com_id": id
        }
        if journal.bank_account_id.id:
            val["bank_account_id"] = get_ent_id(self, 'res.partner.bank', journal.bank_account_id.id)
        return update_record(self, 'account.journal', val, id)


    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountJournalInherit, self).create(vals_list)
        if res:
            for journal in res:
                self.sudo().with_delay(channel='sync_account_journal').sync_record(journal.id)
        return res

    def write(self, vals):
        res = super(AccountJournalInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_journal')
                self.sudo().with_delay(channel='sync_account_journal').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountJournalInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.journal', rec.id)


class ResCountryInherit(models.Model):
    _inherit = "res.country"

    @job
    def sync_record(self, id):
        country = self.sudo().browse(id)
        val = {
            "code": country.code,
            "phone_code": country.phone_code,
            "display_name": country.display_name,
            "name": country.name,
            "currency_id": get_ent_id(self, 'res.currency', country.currency_id.id),
            "vat_label": country.vat_label,
            "com_id": id
        }
        return update_record(self, 'res.country', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResCountryInherit, self).create(vals_list)
        if res:
            for country in res:
                self.sudo().with_delay(channel='sync_res_country').sync_record(country.id)
        return res

    def write(self, vals):
        res = super(ResCountryInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_res_country')
                self.sudo().with_delay(channel='sync_res_country').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResCountryInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.country', rec.id)


class ResCountryStateInherit(models.Model):
    _inherit = "res.country.state"

    @job
    def sync_record(self, id):
        state = self.sudo().browse(id)
        val = {
            "country_id": get_ent_id(self, 'res.country', state.country_id.id),
            "code": state.code,
            "name": state.name,
            "com_id": id
        }
        return update_record(self, 'res.country.state', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResCountryStateInherit, self).create(vals_list)
        if res:
            for rec in res:
                self.sudo().with_delay().sync_record(rec.id)

        return res

    def write(self, vals):
        res = super(ResCountryStateInherit, self).write(vals)
        if res:
            for rec in self:
                self.sudo().with_delay().sync_record(rec.id)

        return res

    def unlink(self):
        res = super(ResCountryStateInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.country.state', rec.id)


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    @job
    def sync_record(self, id):
        user = self.sudo().browse(id)
        company_ids = []
        if user.company_ids:
            company_ids = [ent.ent_id for ent in self.env['records.com.ent.rel'].sudo().search(
                [('model', '=', 'res.company'), ('com_id', 'in', user.company_ids.ids)])]
        val = {
            "company_id": get_ent_id(self, 'res.company', user.company_id.id),
            "company_ids": company_ids,
            "currency_id": user.currency_id.name,
            "property_account_payable_id": get_ent_id(self, 'account.account', user.property_account_payable_id.id),
            "property_account_receivable_id": get_ent_id(self, 'account.account',
                                                         user.property_account_receivable_id.id),
            "display_name": user.display_name,
            "partner_id": get_ent_id(self, 'res.partner', user.partner_id.id),
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "login": user.login,
            "com_id": id
        }
        return update_record(self, 'res.users', val, id)

    def write(self, vals):
        res = super(ResUsersInherit, self).write(vals)
        if res:
            for rec in self:
                # # TODO: SCI rào lại: ảnh hưởng tới hiệu năng api tạo booking
                # remove_duplicate(rec, 'sync_res_company')
                self.sudo().with_delay(channel='sync_res_company').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(ResUsersInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'res.users', rec.id)


class AccountInherit(models.Model):
    _inherit = "account.account"

    @job
    def sync_record(self, id):
        account = self.sudo().browse(id)
        val = {
            "code": account.code,
            "company_id": get_ent_id(self, 'res.company', account.company_id.id),
            "display_name": account.display_name,
            "name": account.name,
            "user_type_id": account.user_type_id.id,
            "reconcile": account.reconcile,
            "type_third_parties": account.type_third_parties,
            "currency_id": get_ent_id(self, 'res.currency', account.currency_id.id),
            "com_id": id
        }
        return update_record(self, 'account.account', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountInherit, self).create(vals_list)
        if res:
            for account in res:
                self.sudo().with_delay(channel='sync_account_account').sync_record(account.id)

        return res

    def write(self, vals):
        res = super(AccountInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_account')
                self.sudo().with_delay(channel='sync_account_account').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.account', rec.id)


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    @job
    def sync_record(self, id):
        account_move = self.sudo().browse(id)
        val = {
            "display_name": account_move.display_name,
            "invoice_payment_ref": account_move.invoice_payment_ref,
            "name": account_move.name,
            "ref": account_move.ref,
            "move_type": account_move.type,
            "invoice_payment_state": account_move.invoice_payment_state,
            "state": account_move.state,
            "company_id": get_ent_id(self, 'res.company', account_move.company_id.id),
            "date": account_move.date and account_move.date.strftime('%Y-%m-%d') or False,
            "invoice_date": account_move.invoice_date and account_move.invoice_date.strftime('%Y-%m-%d') or False,
            "invoice_origin": account_move.invoice_origin,
            "invoice_user_id": get_ent_id(self, 'res.users', account_move.invoice_user_id.id),
            "invoice_date_due": account_move.invoice_date_due and account_move.invoice_date_due.strftime(
                '%Y-%m-%d') or False,
            "journal_id": get_ent_id(self, 'account.journal', account_move.journal_id.id),
            "partner_id": get_ent_id(self, 'res.partner', account_move.partner_id.id),
            "com_id": id
        }

        ent_id = update_record(self, 'account.move', val, id)

        if account_move.line_ids and ent_id:
            for move_line in account_move.line_ids:
                self.env['account.move.line'].sync_record(move_line.id, ent_id)
        return ent_id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMoveInherit, self).create(vals_list)
        if res:
            for account_move in res:
                self.sudo().with_delay(channel='sync_account_move').sync_record(account_move.id)

        return res

    def write(self, vals):
        res = super(AccountMoveInherit, self).write(vals)
        # Only change value in this fields will sync to EE server to reduce queue job records
        field_list = ["display_name", "invoice_payment_ref", "name", "ref", "type", "invoice_payment_state", "state", "invoice_date", "invoice_origin", "invoice_user_id", "invoice_date_due", "journal_id", "partner_id", "line_ids", "invoice_line_ids"]
        print(vals)
        sync = False
        for field in field_list:
            if field in vals:
                sync = True
        if sync and res:
            for rec in self:
                # Remove all pending job before
                remove_duplicate(rec, 'sync_account_move')
                self.sudo().with_delay(channel='sync_account_move').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountMoveInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.move', rec.id)


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    @job
    def sync_record(self, id, move_id):
        account_move_line = self.sudo().browse(id)
        val = {
            "account_id": get_ent_id(self, 'account.account', account_move_line.account_id.id),
            "name": account_move_line.name,
            "product_id": get_ent_id(self, 'product.product', account_move_line.product_id.id),
            "product_uom_id": get_ent_id(self, 'uom.uom', account_move_line.product_uom_id.id),
            "display_name": account_move_line.display_name,
            "company_id": get_ent_id(self, 'res.company', account_move_line.company_id.id),
            "move_name": account_move_line.move_name,
            "ref": account_move_line.ref,
            "price_unit": account_move_line.price_unit,
            "quantity": account_move_line.quantity,
            "price_subtotal": account_move_line.price_subtotal,
            "price_total": account_move_line.price_total,
            "date": account_move_line.date and account_move_line.date.strftime('%Y-%m-%d') or False,
            "date_maturity": account_move_line.date_maturity and account_move_line.date_maturity.strftime(
                '%Y-%m-%d') or False,
            "amount_currency": account_move_line.amount_currency,
            "balance": account_move_line.balance,
            "credit": account_move_line.credit,
            "debit": account_move_line.debit,
            "discount_cash": account_move_line.discount_cash,
            "move_id": move_id,
            "analytic_account_id": get_ent_id(self, 'account.analytic.account',
                                              account_move_line.analytic_account_id.id),
            "partner_id": get_ent_id(self, 'res.partner', account_move_line.partner_id.id),
            "exclude_from_invoice_tab": account_move_line.exclude_from_invoice_tab,
            "com_id": id
        }
        return update_record(self, 'account.move.line', val, id)


    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(AccountMoveLineInherit, self).create(vals_list)
    #     if res:
    #         for account_move_line in res:
    #             self.sudo().with_delay().sync_record(account_move_line.id)

    #     return res

    # def write(self, vals):
    #     res = super(AccountMoveLineInherit, self).write(vals)
    #     if res:
    #         for rec in self:
    #             self.sudo().with_delay().sync_record(rec.id)

    #     return res

    def unlink(self):
        res = super(AccountMoveLineInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.move.line', rec.id)


class AccountTaxInherit(models.Model):
    _inherit = "account.tax"

    @job
    def sync_record(self, id):
        account_tax = self.sudo().browse(id)
        val = {
            "cash_basis_transition_account_id": get_ent_id(self, 'account.account',
                                                           account_tax.cash_basis_transition_account_id.id),
            "name": account_tax.name,
            "display_name": account_tax.display_name,
            "company_id": get_ent_id(self, 'res.company', account_tax.company_id.id),
            "amount": account_tax.amount,
            "com_id": id,
        }
        return update_record(self, 'account.tax', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountTaxInherit, self).create(vals_list)
        if res:
            for account_tax in res:
                self.sudo().with_delay(channel='sync_account_tax').sync_record(account_tax.id)

        return res

    def write(self, vals):
        res = super(AccountTaxInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_tax')
                self.sudo().with_delay(channel='sync_account_tax').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountTaxInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.tax', rec.id)


class AccountPaymentTermInherit(models.Model):
    _inherit = "account.payment.term"

    @job
    def sync_record(self, id):
        account_payment_term = self.sudo().browse(id)
        val = {
            "note": account_payment_term.note,
            "name": account_payment_term.name,
            "display_name": account_payment_term.display_name,
            "company_id": get_ent_id(self, 'res.company', account_payment_term.company_id.id),
            "active": account_payment_term.active,
            "com_id": id
        }
        return update_record(self, 'account.payment.term', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountPaymentTermInherit, self).create(vals_list)
        if res:
            for account_payment_term in res:
                self.sudo().with_delay(channel='sync_account_payment_term').sync_record(account_payment_term.id)

        return res

    def write(self, vals):
        res = super(AccountPaymentTermInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_payment_term')
                self.sudo().with_delay(channel='sync_account_payment_term').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountPaymentTermInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.payment.term', rec.id)


class AccountAnalyticGroupInherit(models.Model):
    _inherit = "account.analytic.group"

    @job
    def sync_record(self, id):
        account_analytic_group = self.sudo().browse(id)
        val = {
            "name": account_analytic_group.name,
            "description": account_analytic_group.description,
            "company_id": get_ent_id(self, 'res.company', account_analytic_group.company_id.id),
            "parent_path": account_analytic_group.parent_path,
            "parent_id": get_ent_id(self, 'account.analytic.group', account_analytic_group.parent_id.id),
            "com_id": id
        }
        return update_record(self, 'account.analytic.group', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountAnalyticGroupInherit, self).create(vals_list)
        if res:
            for account_analytic in res:
                self.sudo().with_delay(channel='sync_account_analytic_account').sync_record(account_analytic.id)

        return res

    def write(self, vals):
        res = super(AccountAnalyticGroupInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_analytic_account')
                self.sudo().with_delay(channel='sync_account_analytic_account').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountAnalyticGroupInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.analytic.group', rec.id)


class AccountAnalyticAccountInherit(models.Model):
    _inherit = "account.analytic.account"

    @job
    def sync_record(self, id):
        account_analytic = self.sudo().browse(id)
        val = {
            "code": account_analytic.code,
            "name": account_analytic.name,
            "display_name": account_analytic.display_name,
            "company_id": get_ent_id(self, 'res.company', account_analytic.company_id.id),
            "active": account_analytic.active,
            "balance": account_analytic.balance,
            "credit": account_analytic.credit,
            "debit": account_analytic.debit,
            "group_id": get_ent_id(self, 'account.analytic.group', account_analytic.group_id.id),
            "com_id": id
        }
        return update_record(self, 'account.analytic.account', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountAnalyticAccountInherit, self).create(vals_list)
        if res:
            for account_analytic in res:
                self.sudo().with_delay(channel='sync_account_analytic_account').sync_record(account_analytic.id)

        return res

    def write(self, vals):
        res = super(AccountAnalyticAccountInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_analytic_account')
                self.sudo().with_delay(channel='sync_account_analytic_account').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountAnalyticAccountInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.analytic.account', rec.id)


class AccountAnalyticLineInherit(models.Model):
    _inherit = "account.analytic.line"

    @job
    def sync_record(self, id):
        analytic_line = self.sudo().browse(id)
        val = {
            "code": analytic_line.code,
            "name": analytic_line.name,
            "display_name": analytic_line.display_name,
            "company_id": get_ent_id(self, 'res.company', analytic_line.company_id.id),
            "ref": analytic_line.ref,
            "unit_amount": analytic_line.unit_amount,
            "amount": analytic_line.amount,
            "date": analytic_line.date and analytic_line.date.strftime('%Y-%m-%d') or False,
            "account_id": get_ent_id(self, 'account.analytic.account', analytic_line.account_id.id),
            "com_id": id
        }
        return update_record(self, 'account.analytic.line', val, id)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountAnalyticLineInherit, self).create(vals_list)
        if res:
            for analytic_line in res:
                self.sudo().with_delay(channel='sync_account_analytic_line').sync_record(analytic_line.id)

        return res

    def write(self, vals):
        res = super(AccountAnalyticLineInherit, self).write(vals)
        if res:
            for rec in self:
                remove_duplicate(rec, 'sync_account_analytic_line')
                self.sudo().with_delay(channel='sync_account_analytic_line').sync_record(rec.id)
        return res

    def unlink(self):
        res = super(AccountAnalyticLineInherit, self).unlink()
        if res:
            for rec in self:
                delete_record(self, 'account.analytic.line', rec.id)
