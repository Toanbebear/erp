# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("""
                ALTER TABLE crm_guarantee_reason DROP general;
                """)
