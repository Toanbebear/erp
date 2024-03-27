# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import odoo.http as http
from odoo.http import request
import base64
import werkzeug

class SupportController(http.Controller):

    @http.route('/support/help', auth="public", website=True)
    def support_help(self, **kwargs):
        ticket_categories = http.request.env['sci.maintenance.equipment.category'].sudo().search([])
        person_name = ""
        person_email = ""
        person_phone = ""
        if http.request.env.user.employee_id:
            person_name = http.request.env.user.employee_id.name
            person_email = http.request.env.user.employee_id.work_email
            person_phone = http.request.env.user.employee_id.work_phone
        setting_max_ticket_attachments = request.env['ir.default'].get('website.support.settings', 'max_ticket_attachments')
        setting_max_ticket_attachment_filesize = request.env['ir.default'].get('website.support.settings', 'max_ticket_attachment_filesize')
        return http.request.render('sci_maintenance.support_help_submit_ticket', {'categories': ticket_categories, 'person_name': person_name, 'email': person_email, 'phone': person_phone, 'department': '', 'setting_max_ticket_attachments': setting_max_ticket_attachments, 'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize})

    @http.route('/support/ticket/process', type="http", auth="public", website=True, csrf=True)
    def support_process_ticket(self, **kwargs):
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if values['my_gold'] != "256":
            return "Bot Detected"
        create_dict = {'person_name': values['person_name'], 'phone': values['phone'],
                       'department': values['department'], 'category_id': int(values['category']), 'email': values['email'],
                       'description': values['description'], 'name': values['subject']}
        create_dict['channel'] = 'website'
        new_ticket_id = request.env['sci.maintenance.request'].sudo().create(create_dict)

        if 'file' in values:
            for c_file in request.httprequest.files.getlist('file'):
                data = c_file.read()

                if c_file.filename:
                    request.env['sci.base.attachment'].sudo().create({
                        'file_name': c_file.filename,
                        'file': base64.b64encode(data),
                        'user_id': http.request.env.user.id,
                        'support_ticket_id': new_ticket_id.id
                    })

        return werkzeug.utils.redirect("/support/ticket/thanks")

    @http.route('/support/ticket/thanks', type="http", auth="public", website=True)
    def support_ticket_thanks(self, **kw):
        return http.request.render('sci_maintenance.support_thank_you', {})

    @http.route('/support/survey/<portal_key>', type="http", auth="public", website=True)
    def support_ticket_survey(self, portal_key):
        """Display the survey"""

        support_ticket = request.env['sci.maintenance.request'].sudo().search([('portal_access_key', '=', portal_key)])

        if support_ticket.support_rating:
            return "Survey Already Complete"
        else:
            return http.request.render('sci_maintenance.support_ticket_survey_page', {'support_ticket': support_ticket})

    @http.route('/support/survey/process/<portal_key>', type="http", auth="public", website=True)
    def support_ticket_survey_process(self, portal_key, **kw):
        """Insert Survey Response"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        if 'rating' not in values:
            return "Please select a rating"

        support_ticket = request.env['sci.maintenance.request'].sudo().search([('portal_access_key', '=', portal_key)])

        if support_ticket.support_rating:
            return "Survey Already Complete"
        else:
            website_ticket_state = request.env['ir.model.data'].get_object('sci_maintenance', 'stage_5')
            support_ticket.state_id = website_ticket_state.id
            support_ticket.support_rating = values['rating']
            support_ticket.support_comment = values['comment']
            return http.request.render('sci_maintenance.support_survey_thank_you', {})