document.querySelectorAll("time.localised-date").forEach(el => {
    const raw = el.getAttribute("datetime");
    if (!raw) return;

    const date = new Date(raw);
    if (isNaN(date)) return;

    const datePart = date.toLocaleDateString(undefined, {
        day:   "numeric",
        month: "long",
        year:  "numeric",
    });

    const isMidnight = date.getUTCHours() === 0 && date.getUTCMinutes() === 0;

    if (isMidnight) {
        el.textContent = datePart;
    } else {
        const timePart = date.toLocaleTimeString(undefined, {
            hour:   "2-digit",
            minute: "2-digit",
        });
        el.textContent = `${datePart} at ${timePart}`;
    }
});