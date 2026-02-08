(() => {
  const DEFAULT_DATA = {
    customer_name: "",
    order_number: "",
    product: "",
    quantity: 0,
    price: 0,
    region: "local",
    delivery: "standard",
    urgent: false,
    notes: "",
  };

  const REGION_SET = new Set(["local", "national", "international"]);
  const DELIVERY_SET = new Set(["standard", "express"]);
  const DELIVERY_FEES = {
    "local|standard": 5,
    "local|express": 15,
    "national|standard": 12,
    "national|express": 25,
    "international|standard": 30,
    "international|express": 60,
  };

  const STORAGE_KEY = "print_sheet_state_v1";

  function parseFloatSafe(value, fallback = 0) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue : fallback;
  }

  function parseBool(value) {
    if (typeof value === "boolean") {
      return value;
    }
    if (typeof value === "number") {
      return value !== 0;
    }
    if (typeof value === "string") {
      return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
    }
    return false;
  }

  function roundMoney(value) {
    return Math.round((value + 1e-9) * 100) / 100;
  }

  function normalizeData(input) {
    const data = { ...DEFAULT_DATA, ...(input || {}) };

    data.customer_name = String(data.customer_name || "").trim();
    data.order_number = String(data.order_number || "").trim();
    data.product = String(data.product || "").trim();
    data.notes = String(data.notes || "").trim();

    data.quantity = Math.max(0, parseFloatSafe(data.quantity, 0));
    data.price = Math.max(0, parseFloatSafe(data.price, 0));
    data.urgent = parseBool(data.urgent);

    const region = String(data.region || "").trim().toLowerCase();
    const delivery = String(data.delivery || "").trim().toLowerCase();
    data.region = REGION_SET.has(region) ? region : DEFAULT_DATA.region;
    data.delivery = DELIVERY_SET.has(delivery) ? delivery : DEFAULT_DATA.delivery;

    return data;
  }

  function computeResults(data) {
    const quantity = Math.max(0, parseFloatSafe(data.quantity, 0));
    const price = Math.max(0, parseFloatSafe(data.price, 0));
    const subtotal = quantity * price;

    let discount_rate = 0;
    if (quantity >= 100) {
      discount_rate = 0.15;
    } else if (quantity >= 50) {
      discount_rate = 0.1;
    } else if (quantity >= 10) {
      discount_rate = 0.05;
    }

    const discount_amount = subtotal * discount_rate;
    const feeKey = `${data.region}|${data.delivery}`;
    const delivery_fee = DELIVERY_FEES[feeKey] || 0;
    const urgent_fee = parseBool(data.urgent) ? 10 : 0;

    const tax_rate = data.region !== "international" ? 0.2 : 0;
    const taxable =
      Math.max(0, subtotal - discount_amount) + delivery_fee + urgent_fee;
    const tax_amount = taxable * tax_rate;
    const total = taxable + tax_amount;

    let status = "ok";
    if (quantity <= 0 || price <= 0) {
      status = "missing_values";
    }

    return {
      subtotal: roundMoney(subtotal),
      discount_rate,
      discount_amount: roundMoney(discount_amount),
      delivery_fee: roundMoney(delivery_fee),
      urgent_fee: roundMoney(urgent_fee),
      tax_rate,
      tax_amount: roundMoney(tax_amount),
      total: roundMoney(total),
      status,
    };
  }

  function loadState() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return normalizeData({});
      }
      return normalizeData(JSON.parse(raw));
    } catch (error) {
      return normalizeData({});
    }
  }

  function saveState(data) {
    try {
      const normalized = normalizeData(data);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
    } catch (error) {
      // Ignore storage errors.
    }
  }

  window.PrintSheet = {
    DEFAULT_DATA,
    STORAGE_KEY,
    normalizeData,
    computeResults,
    loadState,
    saveState,
  };
})();
