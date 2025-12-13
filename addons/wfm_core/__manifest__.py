{
    'name': 'WFM Core',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Core models for GEP OHS Workforce Management',
    'description': """
        GEP OHS Workforce Management - Core Module
        ==========================================

        This module provides the core data models for managing:
        - Clients (companies purchasing OHS services)
        - Installations (physical locations/branches)
        - Partners (external OHS professionals)
        - Visits (scheduled OHS service appointments)

        Part of the GEP OHS Workforce Management System.
    """,
    'author': 'Deep Runner AI',
    'website': 'https://deeprunner.ai',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/visit_stages.xml',
        'data/workflow_cron.xml',
        'views/partner_views.xml',
        'views/visit_views.xml',
        'views/installation_views.xml',
        'views/installation_service_views.xml',
        'views/contract_service_views.xml',
        'views/contract_views.xml',
        'views/workflow_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
