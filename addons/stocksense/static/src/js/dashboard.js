/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class StockSenseDashboard extends Component {
    static template = "stocksense.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            kpis: {},
            documents: [],
            filterOptions: { warehouses: [], categories: [] },
            filters: { doc_type: "all", status: "all", warehouse_id: null, category_id: null },
        });
        onWillStart(async () => {
            this.state.filterOptions = await this.orm.call("stocksense.dashboard", "get_filter_options", []);
            await this.loadData();
        });
    }

    async loadData() {
        this.state.kpis = await this.orm.call("stocksense.dashboard", "get_kpis", []);
        this.state.documents = await this.orm.call("stocksense.dashboard", "get_documents", [this.state.filters]);
    }

    onDocTypeChange(ev) {
        this.state.filters.doc_type = ev.target.value;
        this.loadData();
    }

    onStatusChange(ev) {
        this.state.filters.status = ev.target.value;
        this.loadData();
    }

    onWarehouseChange(ev) {
        const v = ev.target.value;
        this.state.filters.warehouse_id = v === "all" ? null : parseInt(v, 10);
        this.loadData();
    }

    onCategoryChange(ev) {
        const v = ev.target.value;
        this.state.filters.category_id = v === "all" ? null : parseInt(v, 10);
        this.loadData();
    }
}

registry.category("actions").add("stocksense.dashboard", StockSenseDashboard);
