document.addEventListener("submit", (event) => {
    const button = event.target.querySelector("button[type='submit']");
    if (!button || button.disabled) {
        return;
    }
    button.dataset.originalText = button.textContent;
    button.textContent = "Готовим...";
    button.disabled = true;
});
