{
    'name': 'WFM Partner Portal',
    'version': '19.0.1.1.0',
    'category': 'Services/Field Service',
    'summary': 'Backend portal for OHS partners to manage their assignments',
    'description': """
        WFM Partner Portal
        ==================

        This module provides a backend interface for OHS partners to:
        - View their assigned visits in standard Odoo interface
        - See visit details (client, location, date, time)
        - Accept/confirm assigned visits
        - Track visit status
        - Manage their availability calendar
        - Submit referrals for new partner candidates

        Partners access the system as internal users with restricted permissions,
        seeing only their own assigned visits.

        Part of the GEP OHS Workforce Management System.
    """,
    'author': 'Deep Runner AI',
    'website': 'https://deeprunner.ai',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'wfm_core',
    ],
    'data': [
        'security/wfm_portal_security.xml',
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'views/wfm_portal_views.xml',
        'views/wfm_availability_views.xml',
        'views/wfm_profile_views.xml',
        'views/wfm_referral_views.xml',
        'views/wfm_portal_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
