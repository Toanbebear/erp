ERP
----

# Cấu hình redis:

    1. Thêm tham số: redis_url = redis://:password@host:port/db
       - password: Mật khẩu của redis
       - host: Host redis
       - port: port redis vd: 6379
       - db: port redis, ex: 0, 1
  
# Cấu hình Queue:
[queue_job]
channels = root:100,channel_job_create_crm_collaborators:1,channel_job_create_crm_lead:1, channel_job_update_payment:1,  sync_partner:1, sync_product:1, sync_category:1, sync_uom_category:1, sync_uom_uom:1, sync_product_attribute:1, sync_product_attribute_value:1, sync_product_template_attribute_line:1, sync_product_template_attribute_value:1, sync_product_pricelist:1, sync_res_currency:1, sync_project_project:1, sync_res_bank:1, sync_res_partner_bank:1, sync_res_partner_category:1, sync_res_company:1, sync_account_journal:1, sync_res_country:1, sync_res_users:1, sync_account_account:1, sync_account_move:1, sync_account_tax:1, sync_account_payment_term:1, sync_account_analytic_account:1, sync_account_analytic_line:1, sync_all:1, sync_survey_crm_case:1,sync_app_member_walkin:1, sync_app_member_eva:1, sync_app_member_loyalty:1, sync_seeding_crm_lead:1, sync_seeding_sale_order:1, sync_seeding_account_payment:1, sync_seeding_crm_sale_payment:1,sync_seeding_sale_order_line:1,sync_sales_report:1,sync_bc_thu_chi:1, action_done_sale_order_loyalty:1, action_done_crm_line_product_loyalty:1, write_crm_line_loyalty:1,sync_app_member_walkin:1,sync_app_member_account:1,sync_app_member_reexam:1,sync_app_member_eva:1,sync_app_member_reexam_line:1,sync_app_member_loyalty:1,validate_picking_surgery:1,validate_picking_specialty:1,sync_app_member_history_point:1