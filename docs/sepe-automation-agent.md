# SEPE Automation Agent

## Overview

Automate end-to-end SEPE compliance reporting and billing workflow.

**One-liner:** "From visit → SEPE → invoice → payment, all automated."

## Business Value

| Metric | Target |
|--------|--------|
| SEPE admin time | -90% |
| Billing delays | -80% |
| Payment tracking | 100% visibility |

---

## Billing Status Flow

```
⚪ NOT BILLED      Visit completed, not yet processed
        ↓ [SEPE Export Submitted]
🟡 INVOICED        Invoice sent to client, awaiting payment
        ↓ [Invoice Paid]
🟠 CLIENT PAID     Client paid, partner payout pending
        ↓ [Partner Paid]
🟢 SETTLED         Partner paid, fully closed
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      wfm.visit (Extended)                        │
│  + billing_status, invoice_id, sepe_exported, sepe_export_date  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ wfm.sepe.    │ │ account.move │ │ Financial    │
    │ export       │ │ (Invoices)   │ │ Dashboard    │
    │ (Batches)    │ │              │ │              │
    └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Implementation Tasks

### Task 1: Add billing_status Field (2h) - CRITICAL

**File:** `addons/wfm_core/models/visit.py`

```python
# New fields on wfm.visit
billing_status = fields.Selection([
    ('not_billed', 'Not Billed'),
    ('invoiced', 'Invoiced'),
    ('client_paid', 'Client Paid'),
    ('settled', 'Settled'),
], string='Billing Status', default='not_billed', tracking=True)

invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)

partner_payment_amount = fields.Monetary(
    string='Partner Payment',
    compute='_compute_partner_payment',
    store=True,
    currency_field='currency_id'
)

currency_id = fields.Many2one(
    'res.currency',
    default=lambda self: self.env.company.currency_id
)

sepe_exported = fields.Boolean(default=False)
sepe_export_date = fields.Datetime(readonly=True)
```

**View Updates:** `addons/wfm_core/views/visit_views.xml`
- Add billing_status to form view (new notebook page or group)
- Add billing_status to list view columns
- Add search filters: Not Billed, Invoiced, Client Paid, Settled

---

### Task 2: Create wfm.sepe.export Model (4h) - CRITICAL

**File:** `addons/wfm_core/models/sepe_export.py` (NEW)

```python
from odoo import models, fields, api, _
from datetime import timedelta
import base64
import logging

_logger = logging.getLogger(__name__)


class WfmSepeExport(models.Model):
    _name = 'wfm.sepe.export'
    _description = 'SEPE Export Batch'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True,
        default=lambda self: _('New'),
        readonly=True
    )

    # Date range
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    # Visits in this export
    visit_ids = fields.Many2many(
        'wfm.visit',
        string='Visits',
        domain=[('state', '=', 'done')]
    )
    visit_count = fields.Integer(
        compute='_compute_visit_count',
        string='Visit Count'
    )

    # Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('exported', 'Exported'),
        ('submitted', 'Submitted to SEPE'),
    ], default='draft', tracking=True)

    # Export file
    export_file = fields.Binary(
        string='Excel File',
        attachment=True
    )
    export_filename = fields.Char()

    # Audit
    exported_by = fields.Many2one('res.users', readonly=True)
    export_date = fields.Datetime(readonly=True)
    submitted_date = fields.Datetime(readonly=True)

    # Statistics
    total_hours = fields.Float(
        compute='_compute_totals',
        string='Total Hours'
    )
    total_amount = fields.Monetary(
        compute='_compute_totals',
        string='Total Amount',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for record in self:
            record.visit_count = len(record.visit_ids)

    @api.depends('visit_ids', 'visit_ids.duration', 'visit_ids.partner_id.hourly_rate')
    def _compute_totals(self):
        for record in self:
            record.total_hours = sum(record.visit_ids.mapped('duration'))
            record.total_amount = sum(
                v.duration * (v.partner_id.hourly_rate or 0)
                for v in record.visit_ids
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wfm.sepe.export') or _('New')
        return super().create(vals_list)
```

---

### Task 3: Excel Generation with SEPE Format (3h) - CRITICAL

**Dependency:** Add to `__manifest__.py`
```python
'external_dependencies': {
    'python': ['openpyxl'],
},
```

**File:** `addons/wfm_core/models/sepe_export.py` (add method)

```python
def action_generate_excel(self):
    """Generate SEPE-compliant Excel export."""
    self.ensure_one()

    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    except ImportError:
        raise UserError(_('openpyxl library is required. Install with: pip install openpyxl'))

    from io import BytesIO

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'SEPE Export'

    # Header styling
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_alignment = Alignment(horizontal='center', wrap_text=True)

    # Headers (Greek SEPE format)
    headers = [
        'Α/Α',
        'Ημερομηνία Επίσκεψης',
        'Επωνυμία Πελάτη',
        'ΑΦΜ Πελάτη',
        'Εγκατάσταση',
        'Διεύθυνση',
        'Πόλη',
        'Ώρα Έναρξης',
        'Ώρα Λήξης',
        'Διάρκεια (ώρες)',
        'Τύπος Υπηρεσίας',
        'Ονοματεπώνυμο Συνεργάτη',
        'Ειδικότητα',
        'Τηλέφωνο Συνεργάτη',
        'Κατάσταση',
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    # Data rows
    specialty_labels = {
        'physician': 'Ιατρός Εργασίας',
        'safety_engineer': 'Τεχνικός Ασφαλείας',
        'health_scientist': 'Επιστήμονας Υγείας',
    }

    for idx, visit in enumerate(self.visit_ids.sorted(key=lambda v: v.visit_date), 1):
        start_time = f"{int(visit.start_time):02d}:{int((visit.start_time % 1) * 60):02d}"
        end_time = f"{int(visit.end_time):02d}:{int((visit.end_time % 1) * 60):02d}"

        ws.append([
            idx,
            visit.visit_date.strftime('%d/%m/%Y') if visit.visit_date else '',
            visit.client_id.name or '',
            visit.client_id.vat or '',
            visit.installation_id.name or '',
            visit.installation_id.address or '',
            visit.installation_id.city or '',
            start_time,
            end_time,
            round(visit.duration, 2),
            dict(visit._fields['visit_type'].selection).get(visit.visit_type, ''),
            visit.partner_id.name or '',
            specialty_labels.get(visit.partner_id.specialty, visit.partner_id.specialty or ''),
            visit.partner_id.phone or '',
            dict(visit._fields['state'].selection).get(visit.state, ''),
        ])

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save to binary
    output = BytesIO()
    wb.save(output)

    filename = f"SEPE_Export_{self.date_from}_{self.date_to}.xlsx"

    self.write({
        'export_file': base64.b64encode(output.getvalue()),
        'export_filename': filename,
        'state': 'exported',
        'export_date': fields.Datetime.now(),
        'exported_by': self.env.user.id,
    })

    # Mark visits as exported
    self.visit_ids.write({
        'sepe_exported': True,
        'sepe_export_date': fields.Datetime.now(),
    })

    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Export Complete'),
            'message': _('Successfully exported %s visits to Excel.') % len(self.visit_ids),
            'type': 'success',
            'sticky': False,
        }
    }
```

---

### Task 4: SEPE Export Wizard (2h) - HIGH

**File:** `addons/wfm_core/wizard/sepe_export_wizard.py` (NEW)

```python
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SepeExportWizard(models.TransientModel):
    _name = 'wfm.sepe.export.wizard'
    _description = 'SEPE Export Wizard'

    date_from = fields.Date(
        required=True,
        default=lambda self: fields.Date.today().replace(day=1)
    )
    date_to = fields.Date(
        required=True,
        default=fields.Date.today
    )
    include_exported = fields.Boolean(
        default=False,
        string='Include Already Exported',
        help='Include visits that were previously exported'
    )

    visit_ids = fields.Many2many(
        'wfm.visit',
        compute='_compute_visits',
        string='Visits to Export'
    )
    visit_count = fields.Integer(compute='_compute_visits')
    total_hours = fields.Float(compute='_compute_visits')

    @api.depends('date_from', 'date_to', 'include_exported')
    def _compute_visits(self):
        for wizard in self:
            domain = [
                ('visit_date', '>=', wizard.date_from),
                ('visit_date', '<=', wizard.date_to),
                ('state', '=', 'done'),
            ]
            if not wizard.include_exported:
                domain.append(('sepe_exported', '=', False))

            visits = self.env['wfm.visit'].search(domain)
            wizard.visit_ids = visits
            wizard.visit_count = len(visits)
            wizard.total_hours = sum(visits.mapped('duration'))

    def action_create_export(self):
        """Create SEPE export batch and generate Excel."""
        self.ensure_one()

        if not self.visit_ids:
            raise UserError(_('No visits found for the selected date range.'))

        export = self.env['wfm.sepe.export'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'visit_ids': [(6, 0, self.visit_ids.ids)],
        })

        export.action_generate_excel()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wfm.sepe.export',
            'res_id': export.id,
            'view_mode': 'form',
            'target': 'current',
        }
```

**File:** `addons/wfm_core/wizard/sepe_export_wizard_views.xml` (NEW)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="wfm_sepe_export_wizard_form" model="ir.ui.view">
        <field name="name">wfm.sepe.export.wizard.form</field>
        <field name="model">wfm.sepe.export.wizard</field>
        <field name="arch" type="xml">
            <form string="SEPE Export">
                <group>
                    <group>
                        <field name="date_from"/>
                        <field name="date_to"/>
                        <field name="include_exported"/>
                    </group>
                    <group>
                        <field name="visit_count" readonly="1"/>
                        <field name="total_hours" readonly="1"/>
                    </group>
                </group>
                <footer>
                    <button name="action_create_export"
                            string="Generate SEPE Export"
                            type="object"
                            class="btn-primary"
                            invisible="visit_count == 0"/>
                    <button string="Cancel" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>

    <record id="action_sepe_export_wizard" model="ir.actions.act_window">
        <field name="name">SEPE Export</field>
        <field name="res_model">wfm.sepe.export.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
    </record>
</odoo>
```

---

### Task 5: Daily SEPE Export Cron (2h) - HIGH

**File:** `addons/wfm_core/data/scheduled_actions.xml` (NEW)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <!-- Daily SEPE Auto-Export Cron Job -->
        <record id="ir_cron_sepe_daily_export" model="ir.cron">
            <field name="name">SEPE: Daily Auto-Export</field>
            <field name="model_id" ref="model_wfm_sepe_export"/>
            <field name="state">code</field>
            <field name="code">model._cron_daily_export()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="numbercall">-1</field>
            <field name="active">True</field>
        </record>
    </data>
</odoo>
```

**File:** `addons/wfm_core/models/sepe_export.py` (add method)

```python
@api.model
def _cron_daily_export(self):
    """Cron: Auto-export yesterday's completed visits.

    Called daily by scheduled action.
    """
    from datetime import timedelta

    yesterday = fields.Date.today() - timedelta(days=1)

    # Find unexported completed visits from yesterday
    visits = self.env['wfm.visit'].search([
        ('visit_date', '=', yesterday),
        ('state', '=', 'done'),
        ('sepe_exported', '=', False),
    ])

    if not visits:
        _logger.info(f"SEPE cron: No visits to export for {yesterday}")
        return True

    _logger.info(f"SEPE cron: Exporting {len(visits)} visits for {yesterday}")

    # Create export batch
    export = self.create({
        'name': f'Auto-Export {yesterday}',
        'date_from': yesterday,
        'date_to': yesterday,
        'visit_ids': [(6, 0, visits.ids)],
    })

    # Generate Excel
    export.action_generate_excel()

    _logger.info(f"SEPE cron: Successfully created export {export.name}")

    return True
```

---

### Task 6: Auto-Invoice on SEPE Submission (4h) - HIGH

**File:** `addons/wfm_core/models/sepe_export.py` (add methods)

```python
def action_submit_to_sepe(self):
    """Mark as submitted to SEPE and optionally create invoices."""
    self.ensure_one()

    if self.state != 'exported':
        raise UserError(_('You can only submit exported batches.'))

    self.write({
        'state': 'submitted',
        'submitted_date': fields.Datetime.now(),
    })

    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Submitted to SEPE'),
            'message': _('Export batch marked as submitted.'),
            'type': 'success',
        }
    }

def action_create_invoices(self):
    """Create invoices for clients from exported visits."""
    self.ensure_one()

    if self.state != 'submitted':
        raise UserError(_('Submit to SEPE before creating invoices.'))

    # Group visits by client
    client_visits = {}
    for visit in self.visit_ids:
        client = visit.client_id
        if client.id not in client_visits:
            client_visits[client.id] = {'client': client, 'visits': []}
        client_visits[client.id]['visits'].append(visit)

    invoices = self.env['account.move']

    for client_id, data in client_visits.items():
        client = data['client']
        visits = data['visits']

        # Create invoice
        invoice = self._create_client_invoice(client, visits)
        invoices |= invoice

        # Link visits to invoice and update billing status
        for visit in visits:
            visit.write({
                'invoice_id': invoice.id,
                'billing_status': 'invoiced',
            })

    return {
        'type': 'ir.actions.act_window',
        'name': _('Created Invoices'),
        'res_model': 'account.move',
        'domain': [('id', 'in', invoices.ids)],
        'view_mode': 'list,form',
    }

def _create_client_invoice(self, client, visits):
    """Create an invoice for a client from visits.

    Args:
        client: res.partner record
        visits: list of wfm.visit records

    Returns:
        account.move record (invoice)
    """
    invoice_lines = []

    for visit in visits:
        # Get hourly rate from partner or default
        unit_price = visit.partner_id.hourly_rate or 50.0

        invoice_lines.append((0, 0, {
            'name': f"OHS Visit: {visit.name} - {visit.installation_id.name} ({visit.visit_date})",
            'quantity': visit.duration,
            'price_unit': unit_price,
        }))

    invoice = self.env['account.move'].create({
        'move_type': 'out_invoice',
        'partner_id': client.id,
        'invoice_line_ids': invoice_lines,
        'invoice_origin': self.name,
        'narration': f"SEPE Export: {self.name}\nDate Range: {self.date_from} to {self.date_to}",
    })

    return invoice
```

---

### Task 7: Financial Dashboard View (6h) - HIGH

**File:** `addons/wfm_core/models/visit.py` (add method)

```python
@api.model
def _get_billing_dashboard_data(self):
    """Return billing statistics for dashboard."""
    Visit = self.env['wfm.visit']

    not_billed = Visit.search([
        ('state', '=', 'done'),
        ('billing_status', '=', 'not_billed')
    ])
    invoiced = Visit.search([('billing_status', '=', 'invoiced')])
    client_paid = Visit.search([('billing_status', '=', 'client_paid')])
    settled = Visit.search([('billing_status', '=', 'settled')])

    return {
        'not_billed_count': len(not_billed),
        'not_billed_hours': sum(not_billed.mapped('duration')),
        'invoiced_count': len(invoiced),
        'invoiced_amount': sum(invoiced.mapped(lambda v: v.duration * (v.partner_id.hourly_rate or 0))),
        'client_paid_count': len(client_paid),
        'client_paid_amount': sum(client_paid.mapped(lambda v: v.duration * (v.partner_id.hourly_rate or 0))),
        'settled_count': len(settled),
        'settled_amount': sum(settled.mapped(lambda v: v.duration * (v.partner_id.hourly_rate or 0))),
    }
```

**File:** `addons/wfm_core/views/billing_dashboard_views.xml` (NEW)

Dashboard with 4 color-coded cards:
- **White (⚪):** Not Billed - Completed visits pending export
- **Yellow (🟡):** Invoiced - Awaiting client payment
- **Orange (🟠):** Client Paid - Partner payout pending
- **Green (🟢):** Settled - Fully closed

---

## Files Summary

| File | Action | Description |
|------|--------|-------------|
| `models/visit.py` | Modify | Add billing_status, invoice_id, sepe fields |
| `models/sepe_export.py` | Create | SEPE export batch model |
| `models/__init__.py` | Modify | Import sepe_export |
| `views/visit_views.xml` | Modify | Add billing fields to form/list |
| `views/sepe_export_views.xml` | Create | Export batch form/list views |
| `views/billing_dashboard_views.xml` | Create | Financial dashboard |
| `views/menu.xml` | Modify | Add SEPE and Billing menus |
| `wizard/sepe_export_wizard.py` | Create | Export wizard |
| `wizard/sepe_export_wizard_views.xml` | Create | Wizard view |
| `wizard/__init__.py` | Create/Modify | Wizard imports |
| `data/scheduled_actions.xml` | Create | Daily cron job |
| `data/sequences.xml` | Modify | Add SEPE export sequence |
| `security/ir.model.access.csv` | Modify | Access for new models |
| `__manifest__.py` | Modify | Add files, openpyxl dependency |

---

## Effort Estimate

| Task | Effort | Priority |
|------|--------|----------|
| billing_status field | 2h | Critical |
| wfm.sepe.export model | 4h | Critical |
| Excel generation | 3h | Critical |
| Export wizard | 2h | High |
| Daily cron | 2h | High |
| Auto-invoice | 4h | High |
| Financial dashboard | 6h | High |
| **Total** | **23h** | |

---

## Dependencies

```python
# __manifest__.py
'external_dependencies': {
    'python': ['openpyxl'],
},
'depends': [
    'base',
    'contacts',
    'mail',
    'account',  # NEW - for invoicing
],
```

---

## User Workflow

### Manual SEPE Export

1. Navigate to **WFM → SEPE → Create Export**
2. Select date range
3. Review visits to be exported
4. Click **Generate Excel**
5. Download Excel file
6. Upload to SEPE portal
7. Click **Mark as Submitted**
8. Click **Create Invoices**

### Automated Daily Export

1. Cron runs at midnight
2. Finds yesterday's completed, unexported visits
3. Creates export batch
4. Generates Excel file
5. Sends notification to admin (optional)

### Billing Flow

1. **Not Billed:** Visit completed but not in SEPE export
2. **Invoiced:** SEPE submitted → invoice created → sent to client
3. **Client Paid:** Mark invoice as paid → update visits
4. **Settled:** Partner payment processed → close visits
