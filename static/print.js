(() => {
  let socket = null;
  let reconnectTimer = null;

  const regionLabels = {
    local: "Local",
    national: "National",
    international: "International",
  };
  const deliveryLabels = {
    standard: "Standard",
    express: "Express",
  };

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

  function scheduleReconnect() {
    if (reconnectTimer) {
      return;
    }
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, 1000);
  }

  function connect() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${protocol}://${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);

    socket.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data);
        updateData(payload.data);
        updateResults(payload.results);
      } catch (error) {
        // Ignore malformed messages.
      }
    });

    socket.addEventListener("close", scheduleReconnect);
    socket.addEventListener("error", () => {
      socket.close();
    });
  }

  connect();
})();
