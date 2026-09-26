/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class StockSenseProducts extends Component {
    static template = "stocksense.Products";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            products: [],
            categories: [],
            query: "",
            categoryId: "all",
            qty: {},
            counts: {},
            timeline: { productId: null, productName: "", entries: [] },
        });
        this._searchTimeout = null;

        onWillStart(async () => {
            const dashboardData = await this.orm.call("stocksense.dashboard", "get_filter_options", []);
            this.state.categories = dashboardData.categories;
            await this.loadProducts();
        });
    }

    async loadProducts() {
        const categoryId = this.state.categoryId === "all" ? null : parseInt(this.state.categoryId, 10);
        const products = await this.orm.call("stocksense.product_intel", "search_products", [], {
            query: this.state.query,
            category_id: categoryId,
        });
        this.state.products = products;
        for (const p of products) {
            if (!(p.id in this.state.qty)) {
                this.state.qty[p.id] = 1;
            }
        }
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value;
        clearTimeout(this._searchTimeout);
        this._searchTimeout = setTimeout(() => this.loadProducts(), 300);
    }

    onCategoryChange(ev) {
        this.state.categoryId = ev.target.value;
        this.loadProducts();
    }

    onQtyInput(productId, ev) {
        const v = parseFloat(ev.target.value);
        this.state.qty[productId] = isNaN(v) ? 0 : v;
    }

    async onQuickAdd(productId) {
        const delta = this.state.qty[productId] || 0;
        await this.orm.call("stocksense.product_intel", "quick_adjust", [productId, delta]);
        await this.loadProducts();
    }

    async onQuickRemove(productId) {
        const delta = -(this.state.qty[productId] || 0);
        await this.orm.call("stocksense.product_intel", "quick_adjust", [productId, delta]);
        await this.loadProducts();
    }

    async onReportDamage(productId) {
        const delta = -(this.state.qty[productId] || 0);
        await this.orm.call("stocksense.product_intel", "quick_adjust", [productId, delta]);
        await this.loadProducts();
    }

    onCountInput(productId, ev) {
        const v = parseFloat(ev.target.value);
        this.state.counts[productId] = isNaN(v) ? "" : v;
    }

    countDiff(product) {
        const counted = this.state.counts[product.id];
        if (counted === undefined || counted === "") {
            return null;
        }
        return counted - product.qty_available;
    }

    async onApplyCount(product) {
        const counted = this.state.counts[product.id];
        if (counted === undefined || counted === "") {
            return;
        }
        await this.orm.call("stocksense.product_intel", "apply_physical_count", [
            product.id,
            product.primary_location_id,
            counted,
        ]);
        this.state.counts[product.id] = "";
        await this.loadProducts();
    }

    async onViewHistory(product) {
        const entries = await this.orm.call("stocksense.product_intel", "get_product_timeline", [product.id]);
        this.state.timeline = { productId: product.id, productName: product.name, entries };
    }

    closeTimeline() {
        this.state.timeline = { productId: null, productName: "", entries: [] };
    }
}

registry.category("actions").add("stocksense.products", StockSenseProducts);
