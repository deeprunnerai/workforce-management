{
    'name': 'WFM AI Chat',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'AI-powered chat assistant for WFM using LLM',
    'description': """
        WFM AI Chat Assistant
        =====================

        Integrates an LLM-powered conversational assistant into Odoo's
        built-in Discuss chat interface via OdooBot.

        Users can:
        - Query visits, partners, clients using natural language
        - Perform actions like assigning partners, updating visits
        - Get dashboard summaries and statistics

        Powered by LiteLLM proxy with Claude Haiku.
    """,
    'author': 'Deep Runner AI',
    'website': 'https://deeprunner.ai',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'mail_bot',
        'wfm_core',
        'wfm_whatsapp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
    ],
    'external_dependencies': {
        'python': ['openai'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
