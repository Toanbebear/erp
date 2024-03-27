# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment  # Import the class
from odoo.addons.website_form.controllers.main import WebsiteForm  # Import the class
from werkzeug import urls, utils
from odoo.http import request
import base64
import json
from psycopg2 import IntegrityError
from odoo.exceptions import ValidationError
from odoo.http import request
from werkzeug.exceptions import NotFound

_logger = logging.getLogger(__name__)


class CustomWebsiteHrRecruitmentController(WebsiteHrRecruitment):

    @http.route('''/jobs/detail/<model("hr.job", "[('website_id', 'in', (False, current_website_id))]"):job>''',
                type='http', auth="public", website=True)
    def jobs_detail(self, job, **kwargs):
        job = job.sudo()
        res = super(CustomWebsiteHrRecruitmentController, self).jobs_detail(job, **kwargs)
        if kwargs.get('source'):
            base_url = http.request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            res.set_cookie('job_source', kwargs.get('source'), '/', 'localhost')
            cook_lang = request.httprequest.cookies.get('job_source')
            _logger.info(cook_lang)
        else:
            res.set_cookie('job_source', '')

        # render hightlight recruiment
        domain = [('website_published', '=', True), ('highlight', '=', True)]
        base_url = request.httprequest.url
        url_split = base_url.split('.')
        if len(url_split) > 1:
            result_brand = url_split[1]
        else:
            result_brand = 'sci'
        if result_brand == 'kangnam':
            domain += [('root_department', 'ilike', 'kangnam')]
        else:
            domain += [('root_department', '!=', 'kangnam')]
        hot_recruitment = request.env['hr.job'].sudo().search(domain, limit=5, order='write_date desc')
        result = []
        for rec in hot_recruitment:
            if rec.id != job.id:
                result.append(rec)
        if hot_recruitment:
            value = {
                'highlight_job': result,
                'job': job,
                'main_object': job,
            }
            return request.render("website_hr_recruitment.detail", value)
        else:
            value = {
                'job': job,
                'main_object': job,
            }
            return request.render("website_hr_recruitment.detail", value)
        return res

    @http.route('''/jobs/apply/<model("hr.job", "[('website_id', 'in', (False, current_website_id))]"):job>''',
                type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        if not job.can_access_from_current_website():
            raise NotFound()

        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        return request.render("sci_hrms.apply_inherit", {
            'job': job,
            'error': error,
            'default': default,
        })


class CustomWebsiteForm(WebsiteForm):

    # Check and insert values from the form on the model <model>
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):

        if model_name == 'hr.applicant':
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name), ('website_form_access', '=', True)])

            if not model_record:
                return json.dumps(False)

            try:
                data = self.extract_data(model_record, request.params)

                cook_source = request.httprequest.cookies.get('job_source')

                if cook_source:
                    source_record = request.env['utm.source'].sudo().search([('name', '=', cook_source)])
                    data['record']['source_id'] = source_record.id

            # If we encounter an issue while extracting data
            except ValidationError as e:
                # I couldn't find a cleaner way to pass data to an exception
                return json.dumps({'error_fields': e.args[0]})

            try:

                id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
                if id_record:
                    self.insert_attachment(model_record, id_record, data['attachments'])
                    applicant = request.env['hr.applicant'].sudo().search(
                        [('id', '=', id_record)])
                    if applicant.user_id:
                        applicant.create_mail_person_in_charge()  #gọi đến hàm gửi mail đến người phụ trách


            # Some fields have additional SQL constraints that we can't check generically
            # Ex: crm.lead.probability which is a float between 0 and 1
            # TODO: How to get the name of the erroneous field ?
            except IntegrityError:
                return json.dumps(False)

            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record

            return json.dumps({'id': id_record})
        else:
            return super(CustomWebsiteForm, self).website_form(model_name, **kwargs)


class WebsiteFormCustom(WebsiteForm):
    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'hr.applicant':
            if 'g-recaptcha-response' in kwargs:
                if request.website.is_captcha_valid(kwargs['g-recaptcha-response']):
                    del kwargs['g-recaptcha-response']
                    return super(WebsiteFormCustom, self).website_form(model_name, **kwargs)
                else:
                    return super(WebsiteFormCustom, self).website_form(model_name, **kwargs)
            else:
                return super(WebsiteFormCustom, self).website_form(model_name, **kwargs)
        return super(WebsiteFormCustom, self).website_form(model_name, **kwargs)


class WebsiteSearchJob(http.Controller):
    @http.route('/jobs', type='http', auth='public', website=True)
    def search_job(self, search='', industry='', location='', **post):
        # get url domain
        base_url = request.httprequest.url
        url_split = base_url.split('.')
        if len(url_split) > 1:
            result_brand = url_split[1]
        else:
            result_brand = 'sci'
        domain = [('website_published', '=', True)]
        # get industries
        industries = request.env['hr.industry.job'].search([])

        location_dict = {}
        results = None

        if result_brand == 'kangnam':
            domain += [('root_department', 'ilike', 'kangnam')]
        else:
            domain += [('root_department', '!=', 'kangnam')]
        if search:
            post["search_key"] = search
            domain += [('name', 'ilike', search)]
        if industry:
            post["industry"] = industry
            if industry == 0:
                industry = None
            else:
                domain += [('job_industry.id', '=', industry)]
        if location:
            post['location'] = location
            domain += [('address_location', 'ilike', location_dict[location])]
        results = request.env['hr.job'].sudo().search(domain)
        count = len(results)
        if not results:
            values = {
                'jobs': None,
                'industries': industries,
            }
            return request.render("website_hr_recruitment.index", values)
        else:
            values = {
                'jobs': results,
                'industries': industries,
                'count_result': count,
            }
            return request.render("website_hr_recruitment.index", values)


class WebsiteSearchTag(http.Controller):
    @http.route('''/jobs/tag/<model("hr.job", "[('website_id', 'in', (False, current_website_id))]"):tag>''',
                type='http', auth='public', website=True)
    def search_tag(self, tag, **kwargs):
        base_url = request.httprequest.url
        domain = [('website_published', '=', True)]
        url_split = base_url.split('.')
        if len(url_split) > 1:
            result_brand = url_split[1]
        else:
            result_brand = 'sci'
        if result_brand == 'kangnam':
            domain += [('root_department', 'ilike', 'kangnam')]
        else:
            domain += [('root_department', '!=', 'kangnam')]
        industries = request.env['hr.industry.job'].search([])
        results = None
        if tag:
            domain += [('categ_ids', 'ilike', tag.id)]
        results = request.env['hr.job'].sudo().search(domain)
        count = len(results)
        if not results:
            values = {
                'jobs': None,
                'industries': industries,
            }
            return request.render("website_hr_recruitment.index", values)
        else:
            values = {
                'jobs': results,
                'count_results': count,
                'industries': industries,
            }
            return request.render("website_hr_recruitment.index", values)
