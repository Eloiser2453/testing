(() => {
  if (!window.PrintSheet) {
    return;
  }

  const {
    normalizeData,
    computeResults,
    loadState,
    saveState,
    STORAGE_KEY,
  } = window.PrintSheet;

  const channel =
    "BroadcastChannel" in window ? new BroadcastChannel("print-sheet") : null;

  const regionLabels = {
    local: "Local",
    national: "National",
    international: "International",
  };
  const deliveryLabels = {
    standard: "Standard",
    express: "Express",
  };

  let state = loadState();

  function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  function formatMoney(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue.toFixed(2) : "0.00";
  }

  function formatQuantity(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue.toFixed(0) : "0";
  }

  function formatText(value) {
    const text = String(value || "").trim();
    return text.length ? text : "-";
  }

  function formatLabel(value, labels) {
    const key = String(value || "").toLowerCase();
    return labels[key] || formatText(value);
  }

  function updateData(data) {
    if (!data) {
      return;
    }
    setText("print_customer_name", formatText(data.customer_name));
    setText("print_order_number", formatText(data.order_number));
    setText("print_product", formatText(data.product));
    setText("print_quantity", formatQuantity(data.quantity));
    setText("print_price", formatMoney(data.price));
    setText("print_region", formatLabel(data.region, regionLabels));
    setText("print_delivery", formatLabel(data.delivery, deliveryLabels));
    setText("print_urgent", data.urgent ? "yes" : "no");
    setText("print_notes", formatText(data.notes));
  }

  function updateResults(results) {
    if (!results) {
      return;
    }
    setText("print_subtotal", formatMoney(results.subtotal));
    setText("print_discount_amount", formatMoney(results.discount_amount));
    setText("print_delivery_fee", formatMoney(results.delivery_fee));
    setText("print_urgent_fee", formatMoney(results.urgent_fee));
    setText("print_tax_amount", formatMoney(results.tax_amount));
    setText("print_total", formatMoney(results.total));
  }

  function applyState(payload) {
    const incoming = payload && payload.data ? payload.data : payload;
    if (!incoming) {
      return;
    }
    state = normalizeData(incoming);
    const results = payload && payload.results ? payload.results : computeResults(state);
    updateData(state);
    updateResults(results);
    saveState(state);
  }

  if (channel) {
    channel.addEventListener("message", (event) => {
      const payload = event.data;
      if (!payload) {
        return;
      }
      applyState(payload);
    });
  }

  window.addEventListener("storage", (event) => {
    if (event.key !== STORAGE_KEY || !event.newValue) {
      return;
    }
    try {
      applyState({ data: JSON.parse(event.newValue) });
    } catch (error) {
      // Ignore malformed data.
    }
  });

  applyState({ data: state });
})();
