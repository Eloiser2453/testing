(() => {
  const form = document.getElementById("live-form");
  if (!form) {
    return;
  }

  const fields = Array.from(form.querySelectorAll("[data-field]"));
  const state = {};
  let socket = null;
  let reconnectTimer = null;
  let hasPending = false;

  function readField(element) {
    if (element.type === "checkbox") {
      return element.checked;
    }
    return element.value;
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

  function sendState() {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ data: state }));
      hasPending = false;
    } else {
      hasPending = true;
    }
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

    socket.addEventListener("open", () => {
      if (hasPending) {
        sendState();
      }
    });

    socket.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data);
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

  fields.forEach((field) => {
    const name = field.dataset.field;
    state[name] = readField(field);

    const handler = () => {
      state[name] = readField(field);
      sendState();
    };

    field.addEventListener("input", handler);
    field.addEventListener("change", handler);
  });

  connect();
})();
