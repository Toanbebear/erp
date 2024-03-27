##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

{
    'name': 'SCI Health All In One',
    'version': '1.0',
    'sequence': 6,
    'author': "SCI Apps - Dungntp",
    'category': 'Generic Modules/Medical',
    'summary': 'Complete set of powerful features from shealth & shealth Extra Addons',
    'depends': ['base', 'stock_enterprise', 'stock_account_enterprise', 'stock_account', 'purchase_stock', 'l10n_vn', 'product', 'hr',
                'web', 'product_expiry', 'backend_theme_v13',
                'crm_base', 'sci_menu_icon', 'ms_templates', 'ees_tree_no_open', 'stock_picking_show_return',
                'web_form_dynamic_button', 'field_image_preview', 'sh_message', 'sci_brand',
                ],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'support': '',
    'description': """

About SCI Health
---------------

shealth is a multi-user, highly scalable, centralized Electronic Medical Record (EMR) and Hospital Information System for Odoo.

Manage your patients with their important details including family info, prescriptions, appointments, diseases, insurances, lifestyle,mental & social status, lab test details, invoices and surgical histories.

Administer all your doctors with their complete details, weekly consultancy schedule, prescriptions, inpatient admissions and many more.

Allow your doctors and patients to login inside your SCI Health system to manage their appointments. SCI Health is tightly integrated with Odoo’s calendar control so you will be always updated for your upcoming schedules.

""",
    "website": "http://scigroup.com.vn/",
    "data": [
        'views/shealth.xml',
        'security/sh_security.xml',

        # 'sequence/sh_sequence.xml',
        'sequence/sh_medicine_sequence.xml',
        'sh_navigation.xml',

        'sh_medical/views/res_partner_view.xml',
        'sh_medical/views/product_product_view.xml',
        'sh_medical/views/sh_medical_medicaments_view.xml',
        'sh_medical/views/sh_medical_pharmacy_view.xml',
        'sh_medical/views/sh_medical_healthcenters_view.xml',
        'sh_medical/views/sh_medical_pathology_view.xml',
        'sh_medical/views/sh_medical_inpatient_view.xml',
        'sh_medical/views/sh_medical_view.xml',
        'sh_medical/views/account_invoice_view.xml',
        # 'sh_medical/views/sh_medical_insurance_view.xml',
        'sh_medical/views/sh_medical_ethnic_groups_view.xml',
        'sh_medical/views/sh_medical_genetics_view.xml',

        'sh_medical/data/type_relative_data.xml',
        # 'sh_medical/data/res_company_data.xml',
        'sh_medical/data/sh_medical_health_center.xml',
        'sh_medical/data/sh_physician_specialities.xml',
        'sh_medical/data/sh_medical_team_role.xml',
        'sh_medical/data/sh_medical_team_role_update1.xml',
        'sh_medical/data/sh_medical_team_role_update2.xml',
        'sh_medical/data/sh_physician_degrees.xml',
        # 'sh_medical/data/sh_insurance_types.xml',
        'sh_medical/data/sh_ethnic_groups.xml',
        # 'sh_medical/data/institution/sh_medical_health_center_update1.xml',
        # 'sh_medical/data/institution/sh_medical_health_center_update2.xml',
        # 'sh_medical/data/institution/sh_medical_health_center_update3.xml',
        # 'sh_medical/data/institution/ah_medical_health_center_update4.xml',
        # 'sh_medical/data/institution/sh_medical_health_center_hongha.xml',
        # 'sh_medical/data/institution/sh_medical_health_center_hongha_hcm.xml',
        # 'sh_medical/data/sh_who_medicaments.xml',
        'sh_medical/views/sh_medical_service_view.xml',
        'sh_medical/views/sh_medical_teeth_view.xml',

        # 'sh_medical/data/sh_dose_units.xml',
        # 'sh_medical/data/sh_drug_administration_routes.xml',
        # 'sh_medical/data/sh_drug_form.xml',
        # 'sh_medical/data/sh_dose_frequencies.xml',
        # 'sh_medical/data/sh_genetic_risks.xml',
        'sh_medical/data/sh_report_paperformat.xml',
        'sh_medical/reports/report_patient_label.xml',
        'sh_medical/reports/report_patient_medicines.xml',
        'sh_medical/reports/report_appointment_receipt.xml',
        'sh_medical/reports/report_patient_prescriptions.xml',
        'sh_medical/reports/report_temp_service.xml',
        'sh_medical/views/sh_medical_report.xml',
        'sh_medical/views/conf_phone_call.xml',

        'sh_evaluation/views/sh_medical_evaluation_view.xml',
        'sh_evaluation/wizard/update_notes_complaint.xml',
        # 'sh_socioeconomics/views/sh_medical_socioeconomics_view.xml',
        # 'sh_socioeconomics/data/sh_occupations.xml',
        # 'sh_gyneco/views/sh_medical_gyneco_view.xml',
        'sh_lifestyle/views/sh_medical_lifestyle_view.xml',
        'sh_lifestyle/data/sh_recreational_drugs.xml',
        'sh_lab/data/sh_lab_test_units.xml',
        'sh_lab/data/sh_lab_test_types.xml',
        'sh_lab/views/report_patient_labtest.xml',
        'sh_lab/views/sh_medical_lab_report.xml',
        'sh_lab/views/sh_medical_lab_view.xml',

        # 'sh_pediatrics/views/res_partner_view.xml',
        # 'sh_pediatrics/views/sh_medical_pediatrics_newborn_view.xml',
        # 'sh_pediatrics/views/sh_medical_pediatrics_pcs_view.xml',
        # 'sh_pediatrics/views/sh_medical_pediatrics_growth_chart_view.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_boys_p.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_boys_z.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_girls_p.xml',
        # 'sh_pediatrics/data/sh_medical_wfa_girls_z.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_boys_p.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_boys_z.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_girls_p.xml',
        # 'sh_pediatrics/data/sh_medical_lhfa_girls_z.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_boys_p.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_boys_z.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_girls_p.xml',
        # 'sh_pediatrics/data/sh_medical_bmi_girls_z.xml',

        'sh_icd10pcs/views/sh_icd10pcs_view.xml',
        'sh_surgery/views/sh_medical_healthcenters_view.xml',
        'sh_surgery/views/sh_medical_surgery_view.xml',
        'sh_surgery/views/sh_medical_specialty_view.xml',
        'sh_surgery/views/sh_medical_service_view.xml',
        # 'sh_surgery/data/sh_medical_health_center_ot.xml',

        'sh_medical/views/sh_medical_medicaments_view.xml',

        # 'sh_ophthalmology/views/sh_medical_ophthalmology_view.xml',
        # 'sh_ophthalmology/views/sh_medical_ophthalmology_report.xml',
        # 'sh_ophthalmology/views/sh_medical_report.xml',

        "sh_nursing/views/sh_medical_nursing_view.xml",
        "sh_nursing/views/sh_medical_instruction_view.xml",
        "sh_nursing/views/sh_medical_rounding_report.xml",
        "sh_nursing/views/sh_medical_report.xml",
        "sh_nursing/views/report_nursings_inpatient.xml",

        "sh_imaging/data/sh_imaging_test_types.xml",
        "sh_imaging/data/sh_imaging_test_types_update1.xml",
        "sh_imaging/views/sh_medical_imaging_view.xml",
        "sh_imaging/views/report_patient_imaging.xml",
        "sh_imaging/views/sh_medical_imaging_report.xml",

        "sh_evaluation_history/views/sh_medical_evaluation_report.xml",
        "sh_evaluation_history/views/sh_medical_report.xml",

        # 'sh_medical_certificate/views/sh_medical_certificate_view.xml',
        # 'sh_medical_certificate/views/report_medical_certificate.xml',
        # 'sh_medical_certificate/views/sh_medical_report.xml',

        'sh_walkins/views/walkin/sh_medical_physician_view.xml',
        'sh_walkins/views/walkin/sh_medical_vaccines_view.xml',
        'sh_walkins/views/walkin/sh_medical_evaluation_view.xml',
        'sh_walkins/views/walkin/sh_medical_prescription_view.xml',
        'sh_walkins/views/walkin/sh_medical_inpatient_view.xml',
        'sh_walkins/views/walkin/sh_medical_lab_test_view.xml',
        'sh_walkins/views/walkin/sh_medical_imaging_view.xml',
        'sh_walkins/views/walkin/sh_medical_walkin_image_view.xml',
        'sh_walkins/views/walkin/sh_medical_appointment_register_walkin_view.xml',
        'sh_walkins/views/walkin/sh_medical_walking_material_view.xml',
        'sh_walkins/views/walkin/sh_medical_patient_view.xml',
        'sh_walkins/views/sh_medical_register_for_walkin_view.xml',

        'sh_walkins_cancel_medical/views/sh_walkin_cancel_medical_view.xml',
        'sh_walkin_evaluation/views/sh_walkin_evaluation.xml',

        'sh_walkin_evaluation/wizard/bao_cao_ket_qua_khao_sat_sau_phau_thuat/sh_walkin_report_evaluation_views.xml',
        'sh_walkin_evaluation/views/menu_report.xml',

        'sh_walkins/wizard/walkin_labtest_result.xml',
        'sh_walkins_cancel_medical/wizard/cancel_medical_view.xml',
        'sh_walkins/views/report_walkin_patient_labtest.xml',
        'sh_walkins/views/sh_medical_walkin_lab_report.xml',
        'sh_walkins/views/report_walkin_patient_imaging.xml',
        'sh_walkins/views/sh_medical_walkin_img_report.xml',
        'sh_walkins/views/report_walkin_patient_services.xml',
        'sh_walkins/views/report_walkin_patient_services_advisory.xml',
        'sh_walkins/views/sh_medical_walkin_services_report.xml',

        'sh_patient_call_log/views/sh_medical_patient_call_log_view.xml',

        'sh_patient_medical_history/views/sh_medical_patient_view.xml',

        'sh_medical/data/sh_medical_services.xml',
        'sh_medical/data/sh_medical_teeth.xml',
        'sh_medical/data/sh_medical_uom_guarantee.xml',

        'sh_reception/views/sh_reception_view.xml',
        'sh_reception/views/report_receptiont_patient.xml',

        'sh_payment/views/sh_payment_view.xml',
        # 'sh_payment/views/inherit_report_payment_receipt_templates.xml',
        'sh_payment/wizard/reindex_document.xml',
        'sh_payment/wizard/report_payment_deposit.xml',

        # REPORT
        'sh_report/data/template_attachment.xml',
        'sh_report/wizard/walkin_report.xml',
        'sh_report/wizard/inventory_report.xml',
        'sh_report/wizard/material_report.xml',
        # báo cáo doanh thu bệnh nhân
        'sh_report/data/report_revenue_patient.xml',
        # 'sh_report/wizard/report_revenue_patient.xml',
        # báo cáo doanh số ngày
        # 'sh_report/wizard/daily_sales_report.xml',
        'sh_report/views/inherit_product_view.xml',
        'sh_report/views/report_over_material.xml',
        'sh_report/views/sh_medical_over_material_report.xml',
        'sh_report/views/sh_medical_walkin_medicine_public_report.xml',
        'sh_report/views/report_re_examination_slip.xml',
        'sh_report/views/service_information_sheet.xml',
        'sh_report/views/report_hospital_discharge_sheet.xml',
        'sh_report/wizard/bao_cao_thuoc_gay_nghien_huong_than.xml',
        'sh_report/wizard/danh_sach_dich_vu_phau_thuat/danh_sach_dich_vu_phau_thuat.xml',
        'sh_report/wizard/bao_cao_phau_thuat_bo_sung.xml',
        'security/sh_menu_rights.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.xml',

        'sh_medical/data/sh_disease_categories.xml',
        'sh_medical/data/sh_medical_evaluation_services.xml',
        'sh_medical/data/sh_medical_evaluation_services_odontology.xml',
        # 'sh_medical/data/sh_diseases.xml',

        'sh_stock/data/stock_data.xml',
        'sh_stock/data/template_attachment.xml',
        'sh_stock/views/report_sh_stock_view.xml',
        'sh_stock/views/sh_stock_view.xml',
        'sh_stock/views/sh_sale_order_view.xml',
        'sh_stock/views/stock_warehouse_orderpoint.xml',
        # 'sh_stock/views/internal_delivery_bill.xml',
        # 'sh_stock/views/supplier_delivery_bill.xml',
        'sh_stock/views/stock_picking_bill.xml',
        'sh_stock/wizard/quick_add_stock_scrap.xml',

        'sh_account/views/res_currency_views.xml',

        # 'sh_icd10pcs/data/sh_icd_10_pcs_2009_part1.xml',
        # 'sh_icd10pcs/data/sh_icd_10_pcs_2009_part2.xml',
        # 'sh_icd10pcs/data/sh_icd_10_pcs_2009_part3.xml',
        'sh_walkins/views/tool_state_surgery_and_specialty.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "demo": [

    ],
    'test': [
    ],
    'css': [],
    'js': [

    ],
    'qweb': [

    ],
    'application': True,
    "active": False
}
