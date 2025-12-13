/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

/**
 * WFM Dashboard Component
 * Displays coordinator dashboard with 4 color-coded status cards
 */
export class WfmDashboard extends Component {
    static template = "wfm_fsm.Dashboard";
    static props = {
        action: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            green: 0,
            yellow: 0,
            orange: 0,
            red: 0,
            total: 0,
            today: 0,
            unassigned: 0,
            this_week: 0,
            loading: true,
        });

        onWillStart(async () => {
            await this.loadDashboardData();
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

    async refreshData() {
        this.state.loading = true;
        await this.loadDashboardData();
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
}

// Register the dashboard as a client action
registry.category("actions").add("wfm_fsm.dashboard", WfmDashboard);
