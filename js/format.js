// Presentation helpers: how numbers and plots are rendered.
// Kept separate from units.js (which converts) and solver.js (which computes).

/** Design tokens mirrored from styles.css, for canvas-drawn plots. */
const THEME = {
    ink: '#16181D',
    inkMute: '#5A5F6B',
    rule: '#DDD9D2',
    surface: '#FFFFFF',
    accent: '#8A3324',
    warn: '#A8631C',
    fontUi: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    fontMono: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
};

/**
 * Okabe-Ito, a colourblind-safe qualitative palette. Replaces Plotly's
 * default category-10, which is neither colourblind-safe nor tied to the
 * page's own palette.
 */
const PLOT_COLORWAY = [
    '#0072B2', '#D55E00', '#009E73', '#CC79A7',
    '#56B4E9', '#E69F00', '#7A4E8C', '#4C6E5A'
];

/**
 * Format a computed quantity for display.
 *
 * Replaces a blanket .toFixed(4), which rendered M0 as
 * "12589254117941.6719" and small displacements as "0.0012".
 * Magnitudes get 2 decimals; everything else uses significant figures,
 * switching to scientific notation outside 1e-3 .. 1e5.
 *
 * @param {number|null} value - The value to format
 * @param {string} [param] - Parameter symbol (e.g. 'Mw', 'M0'), for special cases
 * @param {number} [sigFigs=4] - Significant figures to keep
 * @returns {string} Formatted value, or an em dash if not finite
 */
function formatQuantity(value, param, sigFigs = 4) {
    if (value === null || value === undefined || !isFinite(value)) return '—';
    if (param === 'Mw') return value.toFixed(2);
    if (value === 0) return '0';

    const magnitude = Math.abs(value);
    if (magnitude >= 1e5 || magnitude < 1e-3) {
        // Scientific notation with a true multiplication sign and superscripts
        const exponent = Math.floor(Math.log10(magnitude));
        const mantissa = value / Math.pow(10, exponent);
        return `${mantissa.toFixed(sigFigs - 1)} × 10${toSuperscript(exponent)}`;
    }

    // Significant figures, then trim trailing zeros ("1258.925", "1.188")
    const decimals = Math.max(0, sigFigs - 1 - Math.floor(Math.log10(magnitude)));
    return parseFloat(value.toFixed(decimals)).toString();
}

/**
 * Plain-text variant for CSV export and clipboard, where the Unicode
 * superscripts of formatQuantity would be unhelpful.
 * @param {number|null} value
 * @returns {string}
 */
function formatQuantityPlain(value) {
    if (value === null || value === undefined || !isFinite(value)) return '';
    const magnitude = Math.abs(value);
    if (magnitude !== 0 && (magnitude >= 1e5 || magnitude < 1e-3)) {
        return value.toExponential(4);
    }
    return parseFloat(value.toPrecision(6)).toString();
}

/**
 * Render a unit for display: "km^2" -> "km²", "dyne.cm" -> "dyne·cm".
 * Returns '' for dimensionless or absent units.
 * @param {string|null} unit
 * @returns {string}
 */
function formatUnit(unit) {
    if (!unit || unit === 'N/A' || unit === 'Mw') return '';
    return unit.replace(/\^2/g, '²').replace(/\^3/g, '³').replace(/\./g, '·');
}

/**
 * Render an integer as Unicode superscript digits.
 * @param {number} n
 * @returns {string}
 */
function toSuperscript(n) {
    const glyphs = { '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                     '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻' };
    return String(n).split('').map(c => glyphs[c] || c).join('');
}

/**
 * Build a Plotly layout carrying the page's typography and palette.
 * Every plot in the app goes through this so the charts and the page
 * read as one document.
 *
 * @param {Object} [overrides={}] - Layout keys to merge over the base
 * @returns {Object} Plotly layout object
 */
function plotLayout(overrides = {}) {
    const axis = {
        gridcolor: THEME.rule,
        zerolinecolor: THEME.rule,
        linecolor: THEME.rule,
        tickfont: { family: THEME.fontMono, size: 11, color: THEME.inkMute },
        titlefont: { family: THEME.fontUi, size: 12, color: THEME.inkMute },
        automargin: true
    };

    const base = {
        colorway: PLOT_COLORWAY,
        font: { family: THEME.fontUi, size: 12, color: THEME.ink },
        paper_bgcolor: THEME.surface,
        plot_bgcolor: THEME.surface,
        margin: { l: 64, r: 24, t: 32, b: 56 },
        hoverlabel: { font: { family: THEME.fontMono, size: 12 } },
        legend: { font: { size: 11 }, bgcolor: 'rgba(0,0,0,0)' },
        xaxis: { ...axis, ...(overrides.xaxis || {}) },
        yaxis: { ...axis, ...(overrides.yaxis || {}) }
    };

    // Titles live in the surrounding HTML, not inside the plot.
    const merged = { ...base, ...overrides };
    merged.xaxis = base.xaxis;
    merged.yaxis = base.yaxis;
    delete merged.title;
    return merged;
}

/** Shared Plotly config: responsive, no vendor logo. */
const PLOT_CONFIG = { responsive: true, displaylogo: false };
