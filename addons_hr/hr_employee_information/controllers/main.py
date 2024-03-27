# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)
import json


class InformationEmployee(http.Controller):

    @http.route('/welcome-employee/<string:token>', type='http', auth='public',
                website=True)
    def welcome_employee(self, token):
        data = {
                'token': token
                }
        return request.render('hr_employee_information.welcome_employee', data)


    @http.route('/information-employee/<string:token>', type='http', auth='public',
                website=True)
    def information(self, token, **post):
        hr_employee = request.env['hr.employee'].search([('token', '=', token)])
        countries = request.env['res.country.state'].search([('country_id.id', '=', request.env.ref('base.vn').id)])
        nation = request.env['nation'].search([])
        skill_type = request.env['hr.skill.type'].search([])
        skill = request.env['hr.skill'].search([])
        skill_level = request.env['hr.skill.level'].search([])
        source = request.env['utm.source'].search([('flag', '=', True)])

        dict_skills = {}
        list_skills = []
        for type in skill_type:
            list_skills.append({'id': type.id, 'name': type.name})
            if type.id in dict_skills.keys():
                continue
            else:
                skill_val = {}
                level_val = {}
                for skil in skill:
                    if skil.skill_type_id.id == type.id:
                        skill_val[skil.id] = skil.name
                for level in skill_level:
                    if level.skill_type_id.id == type.id:
                        level_val[level.id] = level.name
                skill_type_vals = {
                    'name': type.name,
                    'skills': skill_val,
                    'levels': level_val,
                }
                dict_skills[type.id] = skill_type_vals

        json_skill = json.dumps(dict_skills)

        data = {'hr_employee': hr_employee,
                'employee_code': hr_employee.employee_code,
                'marital': hr_employee.marital,
                'countries': countries,
                'skill_type': skill_type,
                'skill': skill,
                'skill_level': skill_level,
                'skills': json_skill,
                'list_skills': json.dumps(list_skills),
                'name_employee': hr_employee.name,
                'nation': nation,
                'token': token,
                'source': source,
                'start': True
                }

        return request.render('hr_employee_information.employee_information', data)

    @http.route('/information-employee/state/<model("res.country.state"):state_id>', type='json', auth='public',
                website=True)
    def get_district(self, state_id):
        districts = dict(((district['id'], district['name']) for district in state_id.district_ids))
        return districts

    @http.route('/information-employee/district/<model("res.country.district"):district_id>', type='json',
                auth='public',
                website=True)
    def get_wards(self, district_id):
        wards = dict(((ward['id'], ward['name']) for ward in district_id.ward_ids))
        return wards

    @http.route(['/information-submit/<string:token>'], type='http',
                methods=['POST'], csrf=False, auth='public', website=True)
    def information_submit(self, token, **post):

        hr_employee = request.env['hr.employee'].search([('token', '=', token)])

        # family_relations__2

        family_relations = []
        work_experience = []
        skill = []

        for key in post.keys():
            if '__' in key:
                key_splits = key.split('__')
                if 'family_relations' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(family_relations):
                        family_relations[index]['relation'] = post[key]
                    else:
                        family_relations.append({
                            'relation': post[key]
                        })

                if 'name' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(family_relations):
                        family_relations[index]['member_name'] = post[key]
                    else:
                        family_relations.append({
                            'member_name': post[key]
                        })

                if 'birth' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(family_relations):
                        family_relations[index]['date_of_birth'] = post[key]
                    else:
                        family_relations.append({
                            'date_of_birth': post[key]
                        })

                if 'occupation' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(family_relations):
                        family_relations[index]['member_contact'] = post[key]
                    else:
                        family_relations.append({
                            'member_contact': post[key]
                        })
                if 'type_skill' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(skill):
                        skill[index]['skill_type_id'] = post[key]
                    else:
                        skill.append({
                            'skill_type_id': post[key]
                        })

                if 'skill' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(skill):
                        skill[index]['skill_id'] = post[key]
                    else:
                        skill.append({
                            'skill_id': post[key]
                        })

                if 'ability' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(skill):
                        skill[index]['skill_level_id'] = post[key]
                    else:
                        skill.append({
                            'skill_level_id': post[key]
                        })

                if 'start_date' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(work_experience):
                        work_experience[index]['date_start'] = post[key]
                    else:
                        work_experience.append({
                            'date_start': post[key]
                        })

                if 'end_date' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(work_experience):
                        work_experience[index]['date_end'] = post[key]
                    else:
                        work_experience.append({
                            'date_end': post[key]
                        })

                if 'name_company' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(work_experience):
                        work_experience[index]['name'] = post[key]
                    else:
                        work_experience.append({
                            'name': post[key]
                        })

                if 'reason_to_leave' == key_splits[0]:
                    # Giá trị sau __
                    index = int(key_splits[1])
                    if index < len(work_experience):
                        work_experience[index]['description'] = post[key]
                    else:
                        work_experience.append({
                            'description': post[key]
                        })

        country = request.env['res.country.state'].search([('id', '=', post['birthplace'])])

        # id_issue_place = request.env['res.country.state'].search([('id', '=', post['issued_by'])])

        hr_employee.write({
            'name': post['employee_name'],
            'birthday': post['birth_day'],
            'gender': post['gender_employee'],
            'place_of_birth': country.name,
            'identification_id': post['identification'],
            'id_issue_date': post['date_issue'],
            'id_issue_place': post['issued_by'],
            'emergency_contact': post['emergency_contact'],
            'emergency_address': post['emergency_address'],
            'mobile_phone': post['employee_phone'],
            'email': post['email'],
            'name_relative': post['name_relatives'],
            'relationship': post['employee_relations'],
            'emergency_phone': post['phone_relatives'],
            # 'hr_source_id': post['hr_source'],
            'social_insurance': post['social_insurance'],
            'personal_income_tax': post['personal_income_tax'],
            'certificate': post['academic_level'],
            'study_field': post['specialized'],
            'study_school': post['name_school'],
            'graduation_year': post['graduation_year'],
            'classification': post['classification']
        })

        hr_employee_family = request.env['hr.employee.family'].sudo().create(family_relations)

        hr_employee_work_experience = request.env['hr.resume.line']

        hr_employee_skill = request.env['hr.employee.skill']

        for ret in work_experience:
            if ret['name'] and ret['date_start'] and ret['date_end']:
                hr_employee_work_experience.create({
                    'name': ret['name'],
                    'date_start': ret['date_start'] + '-01',
                    'date_end': ret['date_end'] + '-01',
                    'description': ret['description'],
                    'employee_id': hr_employee.id,
                    'line_type_id': int(1)
                })
        hr_employee.write({'resume_line_ids': [(4, hr_employee_work_experience.id)]})

        for c in skill:
            if c['skill_type_id'] and c['skill_id'] and c['skill_level_id']:
                hr_employee_skill.create({
                    'skill_type_id': int(c['skill_type_id']),
                    'skill_id': int(c['skill_id']),
                    'skill_level_id': int(c['skill_level_id']),
                    'employee_id': hr_employee.id
                })
        hr_employee.write({'employee_skill_ids': [(4, hr_employee_skill.id)]})

        for i in hr_employee_family:
            hr_employee.write({'fam_ids': [(4, i.id)]})

        return request.render('hr_employee_information.sfinished')
