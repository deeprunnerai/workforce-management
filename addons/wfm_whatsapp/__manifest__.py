{
    'name': 'WFM WhatsApp Integration',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'WhatsApp notifications for WFM visits via Twilio',
    'description': """
        WFM WhatsApp Integration
        ========================

        Autonomous notification agent for partner communications:

        * Automatic notifications on visit assignment
        * Confirmation and reminder messages
        * Manual messaging from coordinators
        * Full message logging and audit trail

        Requires Twilio account with WhatsApp Business API.
    """,
    'author': 'DeepRunner AI',
    'website': 'https://deeprunner.ai',
    'depends': ['wfm_core', 'wfm_fsm'],
    'external_dependencies': {
        'python': ['twilio'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/message_templates.xml',
        'data/scheduled_actions.xml',
        'views/whatsapp_message_views.xml',
        'views/visit_whatsapp_views.xml',
        'wizard/whatsapp_compose_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
