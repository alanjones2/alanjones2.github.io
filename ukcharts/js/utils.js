const partyColors = {
    'Conservative': '#0087DC',
    'Labour': '#DC241f',
    'Liberal Democrats': '#FAA91E',
    'Green': '#6AB023',
    'Reform': '#12E5C7',
    'SNP': '#FDF38E',
    'Plaid Cymru': '#00B140'
};

function parseDate(dateStr) {
    return new Date(dateStr);
}

function getMostRecentDate(data) {
    const dates = data.map(d => new Date(d.date));
    return new Date(Math.max(...dates));
}

function formatLatestDate(date) {
    return date.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

function downloadChart(chartId, filename) {
    const container = document.getElementById(chartId);
    const svgs = container.querySelectorAll('svg');
    let mainSvg = null;
    let maxSize = 0;

    svgs.forEach(svg => {
        const width = parseInt(svg.getAttribute('width') || '0');
        const height = parseInt(svg.getAttribute('height') || '0');
        const size = width * height;
        if (size > maxSize) {
            maxSize = size;
            mainSvg = svg;
        }
    });

    if (!mainSvg) return;

    const clone = mainSvg.cloneNode(true);
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    const originalElements = mainSvg.querySelectorAll('*');
    const clonedElements = clone.querySelectorAll('*');

    clonedElements.forEach((el, i) => {
        const original = originalElements[i];
        if (!original) return;
        const computed = window.getComputedStyle(original);
        ['fill', 'stroke', 'stroke-width', 'opacity', 'font-size', 'font-family', 'display'].forEach(prop => {
            const value = computed.getPropertyValue(prop);
            if (value) {
                el.style.setProperty(prop, value);
            }
        });
        Array.from(original.attributes).forEach(attr => {
            if (!el.hasAttribute(attr.name)) {
                el.setAttribute(attr.name, attr.value);
            }
        });
    });

    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clone);
    const blob = new Blob([svgString], {type: 'image/svg+xml'});
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
