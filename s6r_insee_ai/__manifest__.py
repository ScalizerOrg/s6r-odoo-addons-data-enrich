# Copyright 2025 Scalizer (<https://www.scalizer.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Scalizer INSEE AI',
    'version': '19.0.1.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "AI features to enrich INSEE data",
    'sequence': 0,
    'license': 'LGPL-3',
    'depends': [
        'base',
        's6r_insee',
        'ai_connector',
    ],
    'category': 'Generic Modules/Scalizer',
    'complexity': 'easy',
    'description': '''
This module adds AI features to enrich INSEE data.
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
        'data/prompt_template.xml',
        'data/ai_completion_data.xml',
        'views/search_sirene_result_views.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
