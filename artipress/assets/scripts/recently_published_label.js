(function () {
    function applyRecentlyPublishedLabels() {
        const containers = document.querySelectorAll('.artipress-articles-container[data-recently-published-hours]');

        containers.forEach((container) => {
            const thresholdHours = parseFloat(container.dataset.recentlyPublishedHours);
            if (!isFinite(thresholdHours) || thresholdHours <= 0) return;

            const thresholdMs = thresholdHours * 60 * 60 * 1000;
            const now = Date.now();

            container.querySelectorAll('.artipress-article-card[data-published]').forEach((card) => {
                const publishedRaw = card.dataset.published;
                if (!publishedRaw) return;

                const publishedMs = Date.parse(publishedRaw);
                if (!isFinite(publishedMs)) return;

                if (now - publishedMs > thresholdMs) return;

                const labelSpan = document.createElement('span');
                labelSpan.className = 'artipress-article-card-label recently-published-article-label';
                labelSpan.textContent = 'Recently Published';

                const existingLabels = card.querySelector('.artipress-article-card-labels');
                if (existingLabels) {
                    existingLabels.insertBefore(labelSpan, existingLabels.firstChild);
                    return;
                }

                const emptySpacer = card.querySelector('.artipress-article-card-labels-empty');
                const labelsParagraph = document.createElement('p');
                labelsParagraph.className = 'artipress-article-card-labels';
                labelsParagraph.appendChild(labelSpan);

                if (emptySpacer) {
                    emptySpacer.replaceWith(labelsParagraph);
                } else {
                    const textContent = card.querySelector('.text-content');
                    if (textContent) textContent.insertBefore(labelsParagraph, textContent.firstChild);
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyRecentlyPublishedLabels);
    } else {
        applyRecentlyPublishedLabels();
    }
})();
