# Copyright (C) 2025 - Scalizer (<https://www.scalizer.fr>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Scalizer INSEE',
    'version': '19.0.1.0.0',
    'author': 'Scalizer',
    'website': 'https://www.scalizer.fr',
    'summary': "INSEE and Sirene connector",
    'sequence': 0,
    'certificate': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'l10n_fr',
        'contacts',
    ],
    'external_dependencies': {
        'python': ['s6r-sirene', 'unidecode']
    },
    'category': 'Tools',
    'complexity': 'easy',
    'description': '''
This module allows to access INSEE data series and Sirene database
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
        'views/partner_naf_views.xml',
        'views/search_sirene_result_views.xml',
        'wizard/search_sirene_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            's6r_insee/static/src/scss/style.scss',
        ],
    },
    'auto_install': False,
    'installable': True,
    'application': False,
}
