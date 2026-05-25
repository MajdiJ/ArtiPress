document.querySelectorAll('.lqip-full').forEach(function(img) {
    if (img.complete) {
        img.style.transition = 'none';
        img.classList.add('loaded');
        return;
    }
    img.addEventListener('load', function() {
        var src = img.currentSrc || img.src;
        var entries = performance.getEntriesByName(src, 'resource');
        var fromCache = entries.length > 0 && entries[entries.length - 1].transferSize === 0;
        if (fromCache) img.style.transition = 'none';
        img.classList.add('loaded');
    });
});
