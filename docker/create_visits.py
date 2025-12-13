#!/usr/bin/env python3
import odoo
from odoo import SUPERUSER_ID
from datetime import date, timedelta

# Initialize Odoo
odoo.tools.config.parse_config(['-d', 'odoo_deeprunner', '--no-http'])

with odoo.registry('odoo_deeprunner').cursor() as cr:
    env = odoo.api.Environment(cr, SUPERUSER_ID, {})

    # Get a WFM partner
    partner = env['res.partner'].search([('is_wfm_partner', '=', True)], limit=1)
    # Get installations
    installations = env['wfm.installation'].search([], limit=3)
    # Get the assigned stage
    stage = env['wfm.visit.stage'].search([('name', 'ilike', 'Assigned')], limit=1) or env['wfm.visit.stage'].search([], limit=1)

    if partner and installations and stage:
        for i, inst in enumerate(installations):
            visit = env['wfm.visit'].create({
                'installation_id': inst.id,
                'client_id': inst.client_id.id,
                'partner_id': partner.id,
                'visit_date': date.today() + timedelta(days=i+1),
                'stage_id': stage.id,
            })
            print(f"Created visit {visit.id}: {visit.name}")
        cr.commit()
        print("Done! Created 3 visits.")
    else:
        print(f"Partner found: {bool(partner)}")
        print(f"Installations found: {len(installations)}")
        print(f"Stage found: {bool(stage)}")
        print("Missing data to create visits")
