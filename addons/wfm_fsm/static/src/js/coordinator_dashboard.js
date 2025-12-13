/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";

/**
 * WFM Coordinator Dashboard Component
 * Displays coordinator dashboard with visit status cards and live activity feed
 */
export class WfmCoordinatorDashboard extends Component {
    static template = "wfm_fsm.CoordinatorDashboard";
    static props = {
        action: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            // Visit status counts
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
                this.loadDashboardData(),
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

    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "wfm.visit",
                "get_dashboard_data",
                []
            );
            Object.assign(this.state, data, { loading: false });
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
            this.state.loading = false;
        }
    }

    async loadActivityFeed() {
        try {
            this.state.activitiesLoading = true;
            const activities = await this.orm.call(
                "wfm.visit",
                "get_activity_feed",
                [20]
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
            this.loadDashboardData(),
            this.loadActivityFeed(),
        ]);
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

    openGreen() {
        this.openVisits("green");
    }

    openYellow() {
        this.openVisits("yellow");
    }

    openOrange() {
        this.openVisits("orange");
    }

    openRed() {
        this.openVisits("red");
    }

    openToday() {
        this.openVisits("today");
    }

    openUnassigned() {
        this.openVisits("unassigned");
    }

    openPipeline() {
        this.action.doAction({
            name: "Coordinator Pipeline",
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

    openCalendar() {
        this.action.doAction({
            name: "Visit Calendar",
            type: "ir.actions.act_window",
            res_model: "wfm.visit",
            view_mode: "calendar,kanban,list,form",
            views: [
                [false, "calendar"],
                [false, "kanban"],
                [false, "list"],
                [false, "form"],
            ],
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

// Register the coordinator dashboard as a client action
registry.category("actions").add("wfm_fsm.coordinator_dashboard", WfmCoordinatorDashboard);
