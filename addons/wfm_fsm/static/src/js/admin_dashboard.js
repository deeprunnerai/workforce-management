/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";

/**
 * WFM Admin Dashboard Component
 * Comprehensive dashboard with Financial, Operational, and Visit metrics
 * Plus live activity feed
 */
export class WfmAdminDashboard extends Component {
    static template = "wfm_fsm.AdminDashboard";
    static props = {
        action: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            // Financial metrics
            monthly_revenue: 0,
            outstanding_invoices: 0,
            partner_payments_due: 0,
            profit_margin: 0,
            // Operational metrics
            active_clients: 0,
            active_partners: 0,
            sepe_pending: 0,
            partner_utilization: 0,
            // Visit status counts (from coordinator)
            green: 0,
            yellow: 0,
            orange: 0,
            red: 0,
            total: 0,
            today: 0,
            unassigned: 0,
            this_week: 0,
            // Activity feed
            activities: [],
            // Loading states
            loading: true,
            activitiesLoading: false,
        });

        onWillStart(async () => {
            await Promise.all([
                this.loadAdminDashboardData(),
                this.loadActivityFeed(),
            ]);
        });

        // Auto-refresh activity feed every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadActivityFeed();
        }, 30000);

        onWillDestroy(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    async loadAdminDashboardData() {
        try {
            const data = await this.orm.call(
                "wfm.visit",
                "get_admin_dashboard_data",
                []
            );
            Object.assign(this.state, data, { loading: false });
        } catch (error) {
            console.error("Failed to load admin dashboard data:", error);
            this.state.loading = false;
        }
    }

    async loadActivityFeed() {
        try {
            this.state.activitiesLoading = true;
            const activities = await this.orm.call(
                "wfm.visit",
                "get_activity_feed",
                [15]
            );
            this.state.activities = activities;
            this.state.activitiesLoading = false;
        } catch (error) {
            console.error("Failed to load activity feed:", error);
            this.state.activitiesLoading = false;
        }
    }

    async refreshData() {
        this.state.loading = true;
        await Promise.all([
            this.loadAdminDashboardData(),
            this.loadActivityFeed(),
        ]);
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('el-GR', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value || 0);
    }

    formatPercent(value) {
        return `${(value || 0).toFixed(1)}%`;
    }

    formatTimeAgo(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    async openVisits(filter) {
        const action = await this.orm.call(
            "wfm.visit",
            "get_visits_action",
            [filter]
        );
        this.action.doAction(action);
    }

    openGreen() { this.openVisits("green"); }
    openYellow() { this.openVisits("yellow"); }
    openOrange() { this.openVisits("orange"); }
    openRed() { this.openVisits("red"); }
    openToday() { this.openVisits("today"); }
    openUnassigned() { this.openVisits("unassigned"); }

    openSEPEExport() {
        this.action.doAction('wfm_core.action_sepe_export_wizard');
    }

    openBillingOverview() {
        this.action.doAction('wfm_core.action_billing_overview');
    }

    openPartnerPerformance() {
        this.action.doAction('wfm_fsm.action_churn_dashboard');
    }

    openPipeline() {
        this.action.doAction({
            name: "Visit Pipeline",
            type: "ir.actions.act_window",
            res_model: "wfm.visit",
            view_mode: "kanban,list,form,calendar",
            views: [
                [false, "kanban"],
                [false, "list"],
                [false, "form"],
                [false, "calendar"],
            ],
            context: { search_default_group_by_stage: 1 },
        });
    }

    openClients() {
        this.action.doAction({
            name: "Clients",
            type: "ir.actions.act_window",
            res_model: "res.partner",
            view_mode: "list,form",
            domain: [["is_wfm_client", "=", true]],
        });
    }

    openPartners() {
        this.action.doAction({
            name: "Partners",
            type: "ir.actions.act_window",
            res_model: "res.partner",
            view_mode: "list,form",
            domain: [["is_wfm_partner", "=", true]],
        });
    }

    openVisit(visitId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "wfm.visit",
            res_id: visitId,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }
}

// Register the admin dashboard as a client action
registry.category("actions").add("wfm_fsm.admin_dashboard", WfmAdminDashboard);
