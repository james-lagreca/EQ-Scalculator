# CLAUDE.md

## Project Overview

EQ-Scalculator is a client-side web application for calculating, comparing, and exploring empirical earthquake fault-scaling relationships. It is deployed as a static site on GitHub Pages.

## Tech Stack

- Vanilla JavaScript (ES6+), HTML5, CSS3
- Plotly.js 2.26.0 (charting, loaded via CDN)
- PapaParse 5.4.1 (CSV parsing, loaded via CDN)
- No build tools, bundlers, or package manager — all static files served directly

## Project Structure

```
index.html          — Single-page application entry point
styles.css          — All styling (responsive, CSS Grid + Flexbox)
js/
  app.js            — Main UI logic, tab management, form handling (~1500 lines)
  solver.js         — Core math solver for scaling equations
  models.js         — Model loading and management via fetch()
  units.js          — Unit conversion utilities
scaling_models/     — JSON data files for 6 empirical scaling model sets
```

## Running Locally

Open `index.html` directly in a browser. No server or build step required.

## Code Conventions

- **JS functions/variables**: camelCase (`calculateDeterministic`, `currentBatchData`)
- **Constants**: UPPERCASE (`CONVERSIONS_TO_METER`, `UNIT_OPTIONS`)
- **CSS classes**: kebab-case (`tab-content`, `form-group`, `btn-primary`)
- **HTML IDs**: camelCase (`inputValue`, `selectedModel`)
- JSDoc-style comments on functions with `@param` and `@returns`

## Architecture Notes

- All computation is client-side — no backend
- Scaling model data is lazy-loaded from JSON files in `scaling_models/`
- Three equation forms: `log10(Y) = a + b*log10(X)`, `Y = a + b*log10(X)`, `log10(Y) = a + b*X`
- Monte Carlo simulation uses Box-Muller transform for normal distribution sampling
- Parameters: Mw, M0, L, W, A, SRL, AD, MD with unit conversions (km/m, km²/m², Nm/dyne.cm)

## Testing

No automated test suite. Test manually by opening `index.html` in a browser and exercising the five tabs: Deterministic Calculation, Monte Carlo Simulation, Explore Relationships, Model Comparison, and Chain Calculations.
