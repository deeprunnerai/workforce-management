{
    'name': 'WFM Field Service Management',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Kanban, Dashboard, and Coordinator Tools for GEP OHS Workforce Management',
    'description': """
        GEP OHS Workforce Management - Field Service Module
        ====================================================

        This module provides coordinator tools for managing OHS visits:
        - Enhanced Kanban view with drag-drop assignment
        - Dashboard with 4 color status cards (Green/Yellow/Orange/Red)
        - Calendar view with partner availability
        - Bulk assignment wizard
        - Advanced filters and search

        Part of the GEP OHS Workforce Management System.
    """,
    'author': 'Deep Runner AI',
    'website': 'https://deeprunner.ai',
    'license': 'LGPL-3',
    'depends': [
        'wfm_core',
        'board',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/visit_assign_wizard_views.xml',
        'views/visit_fsm_views.xml',
        'views/dashboard_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wfm_fsm/static/src/scss/dashboard.scss',
            'wfm_fsm/static/src/js/dashboard.js',
            'wfm_fsm/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
