# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Scalizer CRM Enrich',
    'version': '18.0.1.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "Add something",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        'base',
        's6r_insee',
        's6r_insee_ai',
        'crm',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
This module enriches the CRM with SIRENE data.
    ''',
    'qweb': [
    ],
    'demo': [
    ],
    'images': [
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/sirene_menus.xml',
        'data/prompt_template.xml',
        'data/ai_completion_data.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
