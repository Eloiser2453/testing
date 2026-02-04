const rollButton = document.querySelector("#roll-d20");
const result = document.querySelector("#dice-result");

if (rollButton && result) {
  rollButton.addEventListener("click", () => {
    const value = Math.floor(Math.random() * 20) + 1;
    result.textContent = `Выпало: ${value} (d20)`;
  });
}
