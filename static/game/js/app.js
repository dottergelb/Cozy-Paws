document.addEventListener("submit", (event) => {
    const button = event.target.querySelector("button[type='submit']");
    if (!button || button.disabled) {
        return;
    }
    button.dataset.originalText = button.textContent;
    button.textContent = "Готовим...";
    button.disabled = true;
});

document.addEventListener("DOMContentLoaded", () => {
    const hideToast = (toast) => {
        toast.classList.add("is-hiding");
        window.setTimeout(() => toast.remove(), 180);
    };

    document.querySelectorAll(".toast").forEach((toast) => {
        const close = toast.querySelector("[data-toast-close]");
        close?.addEventListener("click", () => hideToast(toast));
        window.setTimeout(() => {
            if (toast.isConnected) {
                hideToast(toast);
            }
        }, 5200);
    });
});
