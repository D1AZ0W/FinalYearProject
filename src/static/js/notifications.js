document.addEventListener("DOMContentLoaded", () => {
    const evtSource = new EventSource("/stream_notifications");

    evtSource.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            showToast(`New Fine Recorded!`, `Case #${data.case_id} added to the Fine List.`);
        } catch (e) {
            console.error("Error parsing notification:", e);
        }
    };

    function showToast(title, message) {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.style.position = "fixed";
            container.style.bottom = "20px";
            container.style.left = "20px";
            container.style.display = "flex";
            container.style.flexDirection = "column";
            container.style.gap = "10px";
            container.style.zIndex = "9999";
            document.body.appendChild(container);

            if (!document.getElementById("toast-styles")) {
                const style = document.createElement("style");
                style.id = "toast-styles";
                style.textContent = `
                    @keyframes slideInLeft {
                        from { transform: translateX(-100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes fadeOut {
                        from { transform: translateX(0); opacity: 1; }
                        to { transform: translateX(-100%); opacity: 0; }
                    }
                    .custom-toast {
                        background-color: #fff;
                        border-left: 4px solid var(--accent-yellow, #ffc107);
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        padding: 12px 20px;
                        border-radius: 4px;
                        display: flex;
                        flex-direction: column;
                        min-width: 250px;
                        animation: slideInLeft 0.3s ease-out forwards;
                    }
                    .custom-toast.closing {
                        animation: fadeOut 0.3s ease-in forwards;
                    }
                    .custom-toast-title {
                        font-weight: 700;
                        font-size: 0.9rem;
                        color: var(--dark-blue, #003d80);
                        margin-bottom: 4px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .custom-toast-title::before {
                        content: "⚠️";
                        font-size: 1.1rem;
                    }
                    .custom-toast-msg {
                        font-size: 0.8rem;
                        color: var(--text-dark, #333);
                    }
                `;
                document.head.appendChild(style);
            }
        }

        const toast = document.createElement("div");
        toast.className = "custom-toast";

        const titleEl = document.createElement("div");
        titleEl.className = "custom-toast-title";
        titleEl.textContent = title;

        const msgEl = document.createElement("div");
        msgEl.className = "custom-toast-msg";
        msgEl.textContent = message;

        toast.appendChild(titleEl);
        toast.appendChild(msgEl);
        container.appendChild(toast);

        // Remove toast after 5 seconds
        setTimeout(() => {
            toast.classList.add("closing");
            toast.addEventListener("animationend", () => {
                toast.remove();
            });
        }, 5000);
    }
});
