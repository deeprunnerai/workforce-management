{
    'name': 'WFM Field Service Management',
    'version': '19.0.4.0.0',
    'category': 'Services/Field Service',
    'summary': 'Kanban, Dashboard, Smart Assignment, Churn Prediction, AI Retention for GEP OHS Workforce Management',
    'description': """
        GEP OHS Workforce Management - Field Service Module
        ====================================================

        This module provides coordinator tools for managing OHS visits:
        - Enhanced Kanban view with drag-drop assignment
        - Dashboard with 4 color status cards (Green/Yellow/Orange/Red)
        - Calendar view with partner availability
        - Bulk assignment wizard
        - Advanced filters and search

        Smart Partner Assignment Engine:
        - AI-powered partner recommendations
        - Relationship-based scoring (35% weight)
        - Availability, Performance, Proximity, Workload scoring
        - Top 2 partner recommendations for quick decisions
        - Auto-tracking of partner-client relationships

        Churn Prediction Dashboard:
        - Partner health scoring (0-100 risk score)
        - 5-factor churn risk algorithm
        - Risk levels: Low, Medium, High, Critical
        - Intervention tracking for retention efforts
        - Daily automated health computation
        - Proactive alerts for at-risk partners

        AI-Powered Retention Engine (NEW):
        - Claude AI integration for personalized retention strategies
        - Automatic WhatsApp message generation in Greek
        - Risk-based urgency recommendations
        - One-click outreach to at-risk partners
        - Comprehensive partner context analysis

        Part of the GEP OHS Workforce Management System.
    """,
    'author': 'Deep Runner AI',
    'website': 'https://deeprunner.ai',
    'license': 'LGPL-3',
    'depends': [
        'wfm_core',
        'board',
        'web_timeline',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/visit_assign_wizard_views.xml',
        'wizard/smart_assign_wizard_views.xml',
        'views/partner_relationship_views.xml',
        'views/visit_fsm_views.xml',
        'views/gantt_views.xml',
        'views/visit_form_extension.xml',
        'views/dashboard_views.xml',
        'views/churn_dashboard_views.xml',
        'views/menu.xml',
        'data/cron_jobs.xml',
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
