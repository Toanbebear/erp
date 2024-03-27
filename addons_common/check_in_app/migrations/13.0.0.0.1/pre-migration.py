# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("""
                ALTER TABLE crm_check_in DROP check_ctv;
                """)
    cr.execute("""
                UPDATE crm_check_in set check_type = 'event'
                """)
