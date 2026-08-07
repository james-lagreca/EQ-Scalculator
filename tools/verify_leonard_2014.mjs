#!/usr/bin/env node
// Self-consistency checks for scaling_models/leonard_2014/leonard_2014.json,
// including spot calculations routed through the real js/solver.js + js/units.js.
//
//   node tools/verify_leonard_2014.mjs [path/to/alternate.json]
//
// Background and derivations: scaling_models/leonard_2014/REVIEW.md
// Framework: M0 = mu*A*D_Av, W = C1*L^(2/3), D_Av = C2*sqrt(A), mu = 3.3e10 Pa,
// Mw = (2/3)*log10(M0[N*m]) - 6.07 (the constant Leonard's Table 4 was built with).

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const jsonPath = process.argv[2] || join(root, 'scaling_models/leonard_2014/leonard_2014.json');
const faultTypes = JSON.parse(readFileSync(jsonPath, 'utf8'))['Leonard 2014'].fault_types;

const LOG_MU = Math.log10(3.3e10); // 10.5185
const HK = (logM0) => (2 / 3) * logM0 - 6.07;

let failures = 0;
let checks = 0;
function check(cond, msg) {
    checks++;
    if (!cond) { failures++; console.log('FAIL  ' + msg); }
}
const near = (x, y, tol) => Number.isFinite(x) && Number.isFinite(y) && Math.abs(x - y) <= tol;
const a0 = (ft, key) => faultTypes[ft][key][0].coefficients.a;

// Both equation forms reduce to "a + b*log10(x)" (log10(Y) for Table 3, Mw for Table 4),
// which is the right space for continuity/consistency comparisons.
const evalLog = (seg, x) => seg.coefficients.a + seg.coefficients.b * Math.log10(x);

// ---- 1. Structure, segment contiguity and continuity at breakpoints ----
for (const [ft, rels] of Object.entries(faultTypes)) {
    for (const [key, segs] of Object.entries(rels)) {
        for (const seg of segs) {
            check(typeof seg.coefficients?.a === 'number' && typeof seg.coefficients?.b === 'number',
                `${ft} ${key}: numeric coefficients`);
            check(seg.equation_form === 'log10(Y) = a + b * log10(X)' || seg.equation_form === 'Y = a + b * log10(X)',
                `${ft} ${key}: recognised equation_form`);
        }
        for (let i = 0; i + 1 < segs.length; i++) {
            const brk = segs[i].range_x[1];
            check(brk === segs[i + 1].range_x[0], `${ft} ${key}: segments ${i}/${i + 1} contiguous`);
            check(near(evalLog(segs[i], brk), evalLog(segs[i + 1], brk), 0.05),
                `${ft} ${key}: continuous at breakpoint ${brk} (${evalLog(segs[i], brk).toFixed(3)} vs ${evalLog(segs[i + 1], brk).toFixed(3)})`);
        }
    }
}

// ---- 2. Framework identities within each fault type ----
for (const ft of Object.keys(faultTypes)) {
    const dA = a0(ft, 'D_from_A');
    check(near(a0(ft, 'M0_from_A'), LOG_MU + dA, 0.02), `${ft}: a(M0_from_A) = log10(mu) + a(D_from_A)`);
    check(near(a0(ft, 'M0_from_D'), LOG_MU - 2 * dA, 0.02),
        `${ft}: a(M0_from_D) = log10(mu) + 2*|a(D_from_A)| (got ${a0(ft, 'M0_from_D')}, want ${(LOG_MU - 2 * dA).toFixed(2)})`);
    check(near(a0(ft, 'Mw_from_A'), HK(a0(ft, 'M0_from_A') + 9), 0.02), `${ft}: Mw_from_A consistent with M0_from_A`);
    check(near(a0(ft, 'Mw_from_D'), HK(a0(ft, 'M0_from_D')), 0.02),
        `${ft}: Mw_from_D consistent with M0_from_D (got ${a0(ft, 'Mw_from_D')}, want ${HK(a0(ft, 'M0_from_D')).toFixed(2)})`);
    // Mw_from_L segments against the M0_from_L segment with matching slope (b_M0 = 1.5*b_Mw).
    for (const mwSeg of faultTypes[ft].Mw_from_L) {
        const m0Seg = faultTypes[ft].M0_from_L.find(s => Math.abs(s.coefficients.b - 1.5 * mwSeg.coefficients.b) < 0.01);
        check(!!m0Seg && near(mwSeg.coefficients.a, HK(m0Seg.coefficients.a + 3 * m0Seg.coefficients.b), 0.05),
            `${ft}: Mw_from_L (b=${mwSeg.coefficients.b}) consistent with M0_from_L`);
    }
}

// ---- 3. Pins on the corrected entries (regression guard) ----
check(a0('Interplate Dip-Slip', 'M0_from_D') === 19.36, 'pin: Interplate DS M0_from_D a = 19.36');
check(a0('Interplate Strike-Slip', 'M0_from_D') === 19.38, 'pin: Interplate SS M0_from_D a = 19.38');
check(a0('SCR Dip-Slip', 'M0_from_D') === 18.79, 'pin: SCR DS M0_from_D a = 18.79');
check(a0('SCR Strike-Slip', 'M0_from_D') === 18.82, 'pin: SCR SS M0_from_D a = 18.82');
check(a0('SCR Strike-Slip', 'Mw_from_D') === 6.47, 'pin: SCR SS Mw_from_D a = 6.47');
check(faultTypes['SCR Strike-Slip'].Mw_from_D[0].range_x[0] === 0, 'pin: SCR SS Mw_from_D range starts at 0');

// ---- 4. Spot calculations through the real app code ----
const ctx = vm.createContext({ Math, parseFloat, isNaN, String, Number, Error, console });
vm.runInContext(readFileSync(join(root, 'js/units.js'), 'utf8'), ctx);
vm.runInContext(readFileSync(join(root, 'js/solver.js'), 'utf8'), ctx);
const ss = faultTypes['Interplate Strike-Slip'];
const solve = (params, val, unit, dir) => vm.runInContext('solveRelationship', ctx)(params, val, unit, dir);

const adFromMw = solve(ss.Mw_from_D, 7, null, 'inverse');        // Mw 7 -> AD
check(near(adFromMw.result, 1.188, 0.03), `solver: IP SS Mw 7 -> AD = ${adFromMw.result?.toFixed(3)} m (want ~1.19)`);
const adFromM0 = solve(ss.M0_from_D, Math.pow(10, 19.605), 'Nm', 'inverse'); // same event via M0
check(near(adFromM0.result, 1.188, 0.04), `solver: IP SS M0(Mw7) -> AD = ${adFromM0.result?.toFixed(3)} m (want ~1.19; was ~35.6 pre-fix)`);

const lDirect = solve(ss.D_from_L, 6, 'm', 'inverse');            // AD 6 m -> L, direct
check(near(lDirect.result / 1e3, 1501, 30), `solver: IP SS AD 6 m -> L = ${(lDirect.result / 1e3).toFixed(0)} km (want ~1501)`);
const m0From6 = solve(ss.M0_from_D, 6, 'm', 'forward');
const lChained = solve(ss.M0_from_L, m0From6.result, 'Nm', 'inverse'); // AD 6 m -> M0 -> L
check(near(lChained.result / lDirect.result, 1.0, 0.05),
    `solver: chained AD->M0->L = ${(lChained.result / 1e3).toFixed(0)} km agrees with direct (was 5.9 km pre-fix)`);

const wSat = solve(ss.W_from_L, 20, 'km', 'inverse');             // saturated width -> L
check(wSat.result === null, 'solver: inverse of saturated (b=0) W_from_L returns null, not Infinity');

const parse = vm.runInContext('parseStdDevA', ctx);
check(near(parse('-4.30 to -3.40'), 0.45, 1e-9), 'parseStdDevA("-4.30 to -3.40") = 0.45');
check(near(parse('-5.02 to -5.60'), 0.29, 1e-9), 'parseStdDevA order-insensitive ("-5.02 to -5.60") = 0.29');
check(near(parse('3.73-4.33'), 0.30, 1e-9), 'parseStdDevA("3.73-4.33") = 0.30');
check(near(parse(0.12), 0.12, 1e-9), 'parseStdDevA(0.12) = 0.12 (numeric passthrough)');
check(parse(null) === null, 'parseStdDevA(null) = null');

// Monte Carlo scatter sanity: sigma of log10(AD) should be ~0.455 (=|−1.86−(−2.77)|/2), not ~4.3.
const mcRun = vm.runInContext('solveOneSimulationRun', ctx);
const logs = [];
for (let i = 0; i < 3000; i++) {
    const r = mcRun(ss.D_from_L, 100, 'km', 'forward', true);
    if (r.result > 0) logs.push(Math.log10(r.result));
}
const mean = logs.reduce((s, v) => s + v, 0) / logs.length;
const sd = Math.sqrt(logs.reduce((s, v) => s + (v - mean) ** 2, 0) / (logs.length - 1));
check(logs.length === 3000 && near(mean, 0.19, 0.05) && sd > 0.3 && sd < 0.6,
    `solver MC: IP SS L 100 km -> AD, log10 mean ${mean.toFixed(3)} (want ~0.19), sd ${sd.toFixed(3)} (want ~0.455)`);

// ---- 5. Documented paper quirks (informational, non-failing) ----
for (const ft of Object.keys(faultTypes)) {
    const derived = HK(a0(ft, 'M0_from_W') + 3 * 3.75);
    const delta = a0(ft, 'Mw_from_W') - derived;
    console.log(`QUIRK ${ft}: Mw_from_W printed ${a0(ft, 'Mw_from_W')} vs Table-3-derived ${derived.toFixed(2)} (delta ${delta >= 0 ? '+' : ''}${delta.toFixed(2)}; kept as printed - see REVIEW.md)`);
}
console.log('QUIRK Interplate SS: Table 3 breaks at L=40 km, Table 4 Mw_from_L at 45 km (both as printed).');
console.log('QUIRK SCR SS: Table 3 A/W relations break at L=70 km, D/M0/Mw relations at 60 km (as printed).');

console.log(failures === 0
    ? `\nPASS  all ${checks} checks passed`
    : `\nFAIL  ${failures} of ${checks} checks failed`);
process.exit(failures === 0 ? 0 : 1);
