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
    'name': 'SCI Introduce Service',
    'version': '1.0',
    'sequence': 6,
    'author': "SCI Apps - Tungpd",
    'category': 'Generic Modules/Medical',
    'summary': 'Complete set of powerful features from shealth & shealth Extra Addons',
    'depends': ['base', 'crm_sale_payment', 'purchase'],
    'support': '',
    'description': """""",
    "website": "http://scigroup.com.vn/",
    "data": [
        'views/account_payment_view.xml',
        'views/crm_lead_views.xml',
        'views/res_company_views.xml',
        'views/purchase_order_line.xml',
        'views/account_journal.xml'
    ],
    "images": [],
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
