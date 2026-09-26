/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onWillUnmount } from "@odoo/owl";
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
            showSummary: false,
            summary: { date: "", total_received_today: 0, total_delivered_today: 0, products: [] },
            transferSuggestions: [],
            showLayout: false,
            layout: [],
            optimization: [],
            showScanner: false,
            scannerSupported: "BarcodeDetector" in window,
            scanStatus: "",
            manualBarcode: "",
            showAddProduct: false,
            uomOptions: [],
            addError: "",
            newProduct: {
                name: "",
                sku: "",
                barcode: "",
                category_id: "",
                uom_id: "",
                list_price: "",
                track_expiry: false,
                expiration_days: 30,
            },
            confirmRemoveId: null,
            removeStatus: "",
        });
        this._searchTimeout = null;
        this.videoRef = useRef("scannerVideo");
        this._scanLoopHandle = null;
        this._mediaStream = null;

        onWillStart(async () => {
            const dashboardData = await this.orm.call("stocksense.dashboard", "get_filter_options", []);
            this.state.categories = dashboardData.categories;
            await this.loadProducts();
        });

        onWillUnmount(() => this.stopScanner());
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

    async toggleSummary() {
        this.state.showSummary = !this.state.showSummary;
        if (this.state.showSummary) {
            this.state.summary = await this.orm.call("stocksense.product_intel", "get_daily_summary", []);
            this.state.transferSuggestions = await this.orm.call(
                "stocksense.product_intel", "get_transfer_suggestions", []
            );
        }
    }

    async toggleLayout() {
        this.state.showLayout = !this.state.showLayout;
        if (this.state.showLayout) {
            this.state.layout = await this.orm.call("stocksense.product_intel", "get_warehouse_layout", []);
            this.state.optimization = await this.orm.call(
                "stocksense.product_intel", "get_optimization_suggestions", []
            );
        }
    }

    async openScanner() {
        this.state.showScanner = true;
        this.state.scanStatus = "";
        if (!this.state.scannerSupported) {
            return;
        }
        try {
            this._mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        } catch (e) {
            this.state.scanStatus = "Camera access denied or unavailable — use manual entry below.";
            this.state.scannerSupported = false;
            return;
        }
        // Video element only exists after the next render since it's behind showScanner.
        setTimeout(() => {
            if (this.videoRef.el) {
                this.videoRef.el.srcObject = this._mediaStream;
                this.videoRef.el.play();
                this._runScanLoop();
            }
        }, 0);
    }

    _runScanLoop() {
        const detector = new window.BarcodeDetector();
        const scan = async () => {
            if (!this.state.showScanner || !this.videoRef.el) {
                return;
            }
            try {
                const barcodes = await detector.detect(this.videoRef.el);
                if (barcodes.length) {
                    await this.handleScannedCode(barcodes[0].rawValue);
                    return;
                }
            } catch (e) {
                // keep trying — a frame with nothing decodable is normal, not an error
            }
            this._scanLoopHandle = requestAnimationFrame(scan);
        };
        this._scanLoopHandle = requestAnimationFrame(scan);
    }

    async handleScannedCode(code) {
        this.state.scanStatus = `Scanned: ${code} — looking up...`;
        const product = await this.orm.call("stocksense.product_intel", "lookup_by_barcode", [code]);
        if (product) {
            this.state.scanStatus = `Found: ${product.name}`;
            this.state.query = product.name;
            await this.loadProducts();
            setTimeout(() => this.closeScanner(), 800);
        } else {
            this.state.scanStatus = `No product found for barcode ${code}.`;
        }
    }

    onManualBarcodeInput(ev) {
        this.state.manualBarcode = ev.target.value;
    }

    async onManualBarcodeSubmit() {
        if (this.state.manualBarcode) {
            await this.handleScannedCode(this.state.manualBarcode);
        }
    }

    stopScanner() {
        if (this._scanLoopHandle) {
            cancelAnimationFrame(this._scanLoopHandle);
            this._scanLoopHandle = null;
        }
        if (this._mediaStream) {
            this._mediaStream.getTracks().forEach((t) => t.stop());
            this._mediaStream = null;
        }
    }

    closeScanner() {
        this.stopScanner();
        this.state.showScanner = false;
        this.state.manualBarcode = "";
    }

    async openAddProduct() {
        this.state.addError = "";
        if (!this.state.uomOptions.length) {
            this.state.uomOptions = await this.orm.call("stocksense.product_intel", "get_uom_options", []);
        }
        this.state.newProduct = {
            name: "",
            sku: "",
            barcode: "",
            category_id: "",
            uom_id: "",
            list_price: "",
            track_expiry: false,
            expiration_days: 30,
        };
        this.state.showAddProduct = true;
    }

    closeAddProduct() {
        this.state.showAddProduct = false;
    }

    onNewProductField(field, ev) {
        const value = field === "track_expiry" ? ev.target.checked : ev.target.value;
        this.state.newProduct[field] = value;
    }

    async submitNewProduct() {
        const p = this.state.newProduct;
        if (!p.name || !p.name.trim()) {
            this.state.addError = "Product name is required.";
            return;
        }
        try {
            await this.orm.call("stocksense.product_intel", "create_product", [{
                name: p.name,
                sku: p.sku || null,
                barcode: p.barcode || null,
                category_id: p.category_id ? parseInt(p.category_id, 10) : null,
                uom_id: p.uom_id ? parseInt(p.uom_id, 10) : null,
                list_price: p.list_price ? parseFloat(p.list_price) : 0,
                track_expiry: p.track_expiry,
                expiration_days: p.expiration_days ? parseInt(p.expiration_days, 10) : 30,
            }]);
            this.state.showAddProduct = false;
            await this.loadProducts();
        } catch (e) {
            this.state.addError = "Could not create product — check the details and try again.";
        }
    }

    askRemoveProduct(productId) {
        this.state.confirmRemoveId = productId;
        this.state.removeStatus = "";
    }

    cancelRemoveProduct() {
        this.state.confirmRemoveId = null;
    }

    async confirmRemoveProduct(productId) {
        const result = await this.orm.call("stocksense.product_intel", "remove_product", [productId]);
        this.state.confirmRemoveId = null;
        if (result.method === "deleted") {
            this.state.removeStatus = `"${result.name}" was permanently deleted (no stock history existed).`;
        } else if (result.method === "archived") {
            this.state.removeStatus = `"${result.name}" was archived (it has stock history, so it's hidden rather than deleted).`;
        }
        await this.loadProducts();
    }
}

registry.category("actions").add("stocksense.products", StockSenseProducts);
