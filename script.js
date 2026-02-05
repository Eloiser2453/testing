const rollButton = document.querySelector("#roll-d20");
const result = document.querySelector("#dice-result");

if (rollButton && result) {
  rollButton.addEventListener("click", () => {
    const value = Math.floor(Math.random() * 20) + 1;
    result.textContent = `Выпало: ${value} (d20)`;
  });
}

const tableOverlay = document.querySelector("#table-overlay");
const tableOpenButtons = document.querySelectorAll("[data-open-table]");
const tableCloseButton = document.querySelector("[data-close-table]");

const setTableOpen = (isOpen) => {
  if (!tableOverlay) {
    return;
  }

  tableOverlay.classList.toggle("is-open", isOpen);
  tableOverlay.setAttribute("aria-hidden", String(!isOpen));
  document.body.classList.toggle("table-open", isOpen);
};

if (tableOverlay) {
  tableOverlay.addEventListener("click", (event) => {
    if (event.target === tableOverlay) {
      setTableOpen(false);
    }
  });
}

tableOpenButtons.forEach((button) => {
  button.addEventListener("click", () => setTableOpen(true));
});

if (tableCloseButton) {
  tableCloseButton.addEventListener("click", () => setTableOpen(false));
}

document.addEventListener("keydown", (event) => {
  if (!tableOverlay || event.defaultPrevented) {
    return;
  }

  if (event.metaKey || event.ctrlKey || event.altKey) {
    return;
  }

  const target = event.target;
  const isInput =
    target instanceof HTMLElement &&
    (target.isContentEditable ||
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA");

  if (isInput) {
    return;
  }

  const key = event.key.toLowerCase();
  const isGameKey = event.code === "KeyG" || key === "g" || key === "п";
  const isEscape = event.key === "Escape";

  if (isGameKey) {
    event.preventDefault();
    setTableOpen(!tableOverlay.classList.contains("is-open"));
  } else if (isEscape && tableOverlay.classList.contains("is-open")) {
    event.preventDefault();
    setTableOpen(false);
  }
});
