(() => {
  if (!window.PrintSheet) {
    return;
  }

  const form = document.getElementById("live-form");
  if (!form) {
    return;
  }

  const {
    normalizeData,
    computeResults,
    loadState,
    saveState,
    STORAGE_KEY,
  } = window.PrintSheet;

  const fields = Array.from(form.querySelectorAll("[data-field]"));
  const channel =
    "BroadcastChannel" in window ? new BroadcastChannel("print-sheet") : null;

  let state = loadState();
  let isApplying = false;

  function readField(element) {
    if (element.type === "checkbox") {
      return element.checked;
    }
    return element.value;
  }

  function writeField(element, value) {
    if (element.type === "checkbox") {
      element.checked = Boolean(value);
      return;
    }
    element.value = value == null ? "" : value;
  }

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

  function formatPercent(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue)
      ? `${(numberValue * 100).toFixed(0)}%`
      : "0%";
  }

  function updateResults(results) {
    if (!results) {
      return;
    }
    setText("result_subtotal", formatMoney(results.subtotal));
    setText("result_discount_rate", formatPercent(results.discount_rate));
    setText("result_discount_amount", formatMoney(results.discount_amount));
    setText("result_delivery_fee", formatMoney(results.delivery_fee));
    setText("result_urgent_fee", formatMoney(results.urgent_fee));
    setText("result_tax_rate", formatPercent(results.tax_rate));
    setText("result_tax_amount", formatMoney(results.tax_amount));
    setText("result_total", formatMoney(results.total));
    setText("result_status", results.status || "-");
  }

  function broadcast(payload) {
    if (channel) {
      channel.postMessage(payload);
    }
  }

  function applyState(payload) {
    const incoming = payload && payload.data ? payload.data : payload;
    if (!incoming) {
      return;
    }

    isApplying = true;
    state = normalizeData(incoming);

    fields.forEach((field) => {
      const name = field.dataset.field;
      writeField(field, state[name]);
    });

    const results = payload && payload.results ? payload.results : computeResults(state);
    updateResults(results);
    saveState(state);
    isApplying = false;
  }

  function handleChange(field) {
    if (isApplying) {
      return;
    }
    const name = field.dataset.field;
    state = normalizeData({ ...state, [name]: readField(field) });
    const results = computeResults(state);
    updateResults(results);
    saveState(state);
    broadcast({ data: state, results, source: "form" });
  }

  fields.forEach((field) => {
    field.addEventListener("input", () => handleChange(field));
    field.addEventListener("change", () => handleChange(field));
  });

  if (channel) {
    channel.addEventListener("message", (event) => {
      const payload = event.data;
      if (!payload || payload.source === "form") {
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
