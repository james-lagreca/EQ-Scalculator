// Core solver logic
// Based on logic.py (generic_solver.py) from the original Python code

/**
 * Calculate deterministic result for an equation
 * @param {string} form - Equation form
 * @param {number} x - Input value
 * @param {number} a - Coefficient a
 * @param {number} b - Coefficient b
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {number|null} Calculated result
 */
function _calcEquation(form, x, a, b, direction) {
    try {
        if (x === null || x === undefined || isNaN(x)) {
            return null;
        }

        x = parseFloat(x);
        a = parseFloat(a);
        b = parseFloat(b);
        
        if (form === "log10(Y) = a + b * log10(X)") {
            if (direction === 'forward') {
                if (x <= 0) return null;
                const result = Math.pow(10, a + b * Math.log10(x));
                    return result;
            } else { // inverse
                if (x <= 0 || b === 0) return null;
                const result = Math.pow(10, (Math.log10(x) - a) / b);
                return result;
            }
        } else if (form === "Y = a + b * log10(X)") {
            if (direction === 'forward') {
                if (x <= 0) return null;
                const result = a + b * Math.log10(x);
                return result;
            } else { // inverse
                if (b === 0) return null;
                const result = Math.pow(10, (x - a) / b);
                return result;
            }
        } else if (form === "log10(Y) = a + b * X") {
            if (direction === 'forward') {
                const result = Math.pow(10, a + b * x);
                return result;
            } else { // inverse
                if (x <= 0 || b === 0) return null;
                const result = (Math.log10(x) - a) / b;
                return result;
            }
        }
    } catch (e) {
        return null;
    }
    return null;
}

/**
 * Validity range of one segment, expressed in the INPUT variable's space.
 *
 * `range_x` is always stated in terms of X. When solving forward that IS the
 * input, so it is returned unchanged. When solving inversely the input is Y,
 * so the bounds are pushed through the forward equation — otherwise a length
 * range gets reported as though it were a displacement range.
 *
 * @param {Object} segment - A model segment
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {Object} {min, max} in input units; null on either side means unbounded
 */
function getSegmentDomain(segment, direction) {
    const rangeX = segment.range_x || [null, null];
    const minX = rangeX[0];
    const maxX = rangeX[1];

    if (direction === 'forward') {
        return { min: minX, max: maxX };
    }

    const { a, b } = segment.coefficients;
    const yAt = (x) => {
        if (x === null) return null;
        // _calcEquation refuses x <= 0 for the log-X forms, but a lower bound
        // of exactly 0 is a real bound, not an absent one: for
        // log10(Y) = a + b*log10(X) with b > 0, Y tends to 0 as X tends to 0.
        // Without this the domain reads "no lower bound" when it is [0, ...).
        if (x === 0 && segment.equation_form === 'log10(Y) = a + b * log10(X)') {
            return b > 0 ? 0 : null;
        }
        return _calcEquation(segment.equation_form, x, a, b, 'forward');
    };

    const yAtMinX = yAt(minX);
    const yAtMaxX = yAt(maxX);

    // A saturated segment (b = 0) maps every X to one Y, so it has no
    // invertible domain. _calcEquation already refuses to invert it.
    if (b === 0) return { min: null, max: null, degenerate: true };

    // b < 0 flips the mapping, so sort rather than assume ordering.
    if (yAtMinX === null || yAtMaxX === null || yAtMinX < yAtMaxX) {
        return { min: yAtMinX, max: yAtMaxX };
    }
    return { min: yAtMaxX, max: yAtMinX };
}

/**
 * Validity range of a whole relation in the input variable's space: the union
 * across its segments, which are contiguous by construction.
 *
 * @param {Array} modelParams - Array of model segments
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {Object|null} {min, max, unit, degenerate} — null bounds mean the
 *                        publication states no bound on that side
 */
function getInputDomain(modelParams, direction) {
    if (!modelParams || !modelParams.length) return null;

    const unitKey = direction === 'forward' ? 'x' : 'y';
    const unit = modelParams[0].units ? modelParams[0].units[unitKey] : null;

    let min = Infinity;
    let max = -Infinity;
    let sawUnboundedLow = false;
    let sawUnboundedHigh = false;
    let degenerate = true;

    for (const segment of modelParams) {
        const domain = getSegmentDomain(segment, direction);
        if (domain.degenerate) continue;
        degenerate = false;

        if (domain.min === null) sawUnboundedLow = true;
        else min = Math.min(min, domain.min);

        if (domain.max === null) sawUnboundedHigh = true;
        else max = Math.max(max, domain.max);
    }

    if (degenerate) return { min: null, max: null, unit, degenerate: true };

    return {
        min: sawUnboundedLow || min === Infinity ? null : min,
        max: sawUnboundedHigh || max === -Infinity ? null : max,
        unit,
        degenerate: false
    };
}

/**
 * Get the appropriate model segment for a given input value
 * @param {Array} modelParams - Array of model parameter objects
 * @param {number} convertedInput - Input value in model's native units
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {Object|null} The matching segment or null
 */
function getTargetSegment(modelParams, convertedInput, direction) {
    if (convertedInput === null) return null;

    for (const segment of modelParams) {
        const domain = getSegmentDomain(segment, direction);

        // A saturated segment has no invertible domain, so it can never be
        // matched on input value; it is only reachable via the fallback below.
        if (domain.degenerate) continue;

        if ((domain.min === null || convertedInput >= domain.min) &&
            (domain.max === null || convertedInput < domain.max)) {
            return segment;
        }
    }

    // If no segment found, return first or last based on input value
    if (!modelParams.length) return null;

    const firstRangeX = (modelParams[0].range_x || [0])[0];
    return convertedInput < firstRangeX ? modelParams[0] : modelParams[modelParams.length - 1];
}

/**
 * Solve a scaling relationship
 * @param {Array} modelParams - Array of model segments
 * @param {number} inputVal - Input value
 * @param {string} inputUnit - Input unit
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {Object} {result: number|null, unit: string|null, error: string|null}
 */
function solveRelationship(modelParams, inputVal, inputUnit, direction = 'forward') {
    const xKey = direction === 'forward' ? 'x' : 'y';
    const yKey = direction === 'forward' ? 'y' : 'x';
    
    try {
        const modelInputUnit = modelParams[0].units[xKey];
        let convertedInput;
        
        if (modelInputUnit) {
            convertedInput = convertUnits(inputVal, inputUnit, modelInputUnit);
        } else {
            convertedInput = inputVal;
        }
        
        const targetSegment = getTargetSegment(modelParams, convertedInput, direction);
        
        if (!targetSegment) {
            return { result: null, unit: null, error: "Could not identify a model segment." };
        }
        
        const result = _calcEquation(
            targetSegment.equation_form,
            convertedInput,
            targetSegment.coefficients.a,
            targetSegment.coefficients.b,
            direction
        );

        if (result === null) {
            return { result: null, unit: null, error: "Mathematical error during calculation." };
        }
        
        return { result: result, unit: targetSegment.units[yKey], error: null };
    } catch (e) {
        return { result: null, unit: null, error: e.message };
    }
}

/**
 * Check if input is outside the model's validity range
 * @param {Array} modelParams - Array of model segments
 * @param {number} inputVal - Input value
 * @param {string} inputUnit - Input unit
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {string|null} Warning message or null
 */
function checkIfExtrapolating(modelParams, inputVal, inputUnit, direction = 'forward') {
    const xKey = direction === 'forward' ? 'x' : 'y';
    
    try {
        const modelInputUnit = modelParams[0].units[xKey];
        const convertedInput = modelInputUnit ? 
            convertUnits(inputVal, inputUnit, modelInputUnit) : inputVal;
        
        let isWithinAnyRange = false;

        for (const segment of modelParams) {
            const domain = getSegmentDomain(segment, direction);
            if (domain.degenerate) continue;

            if ((domain.min === null || convertedInput >= domain.min) &&
                (domain.max === null || convertedInput < domain.max)) {
                isWithinAnyRange = true;
                break;
            }
        }

        if (!isWithinAnyRange) {
            return "Warning: Input is outside the model's recommended validity range. Result is an extrapolation.";
        }
        
        return null;
    } catch (e) {
        return null;
    }
}

/**
 * Parse a std_dev_a field into a standard deviation.
 * Numeric values are used as-is (e.g. Yang et al. 2020). Leonard (2014)
 * stores the one-standard-deviation RANGE of the intercept as a string
 * (e.g. "-4.30 to -3.40" or "6.29-6.69"), so sigma is half the range
 * width, regardless of the order the bounds are written in.
 * @param {number|string|null} value - std_dev_a value from a model segment
 * @returns {number|null} Standard deviation, or null if not usable
 */
function parseStdDevA(value) {
    if (value === null || value === undefined) return null;
    if (typeof value === 'number') return isNaN(value) ? null : value;
    const range = String(value).match(/(-?\d+(?:\.\d+)?)\s*(?:to|–|-)\s*(-?\d+(?:\.\d+)?)/);
    if (range) {
        return Math.abs(parseFloat(range[2]) - parseFloat(range[1])) / 2;
    }
    const single = parseFloat(value);
    return isNaN(single) ? null : single;
}

/**
 * Solve one simulation run with optional uncertainty
 * @param {Array} modelParams - Array of model segments
 * @param {number} inputVal - Input value
 * @param {string} inputUnit - Input unit
 * @param {string} direction - 'forward' or 'inverse'
 * @param {boolean} includeModelUncertainty - Whether to include model uncertainty
 * @returns {Object} {result: number|null, unit: string|null}
 */
function solveOneSimulationRun(modelParams, inputVal, inputUnit, direction = 'forward', includeModelUncertainty = true) {
    const xKey = direction === 'forward' ? 'x' : 'y';
    const yKey = direction === 'forward' ? 'y' : 'x';
    
    try {
        const modelInputUnit = modelParams[0].units[xKey];
        const convertedInput = modelInputUnit ? 
            convertUnits(inputVal, inputUnit, modelInputUnit) : inputVal;
        
        const targetSegment = getTargetSegment(modelParams, convertedInput, direction);
        
        if (!targetSegment) {
            return { result: null, unit: null };
        }
        
        let a = targetSegment.coefficients.a;
        let b = targetSegment.coefficients.b;
        
        // Apply model uncertainty if requested (mirrors Python solve_one_simulation_run)
        if (includeModelUncertainty) {
            // Apply std_dev_a noise to intercept coefficient (e.g. Leonard 2014)
            const stdDevA = parseStdDevA(targetSegment.std_dev_a);
            if (stdDevA !== null && stdDevA > 0) {
                a = randomNormal(a, stdDevA);
            }

            // Apply log10_y_std_dev scatter directly to result (e.g. Wells & Coppersmith 1994)
            if (targetSegment.log10_y_std_dev !== null &&
                targetSegment.log10_y_std_dev !== undefined &&
                direction === 'forward') {
                const stdDev = targetSegment.log10_y_std_dev;
                const deterministicResult = _calcEquation(
                    targetSegment.equation_form, convertedInput, a, b, direction
                );
                if (deterministicResult !== null && deterministicResult > 0) {
                    const log10Y = Math.log10(deterministicResult);
                    return { result: Math.pow(10, randomNormal(log10Y, stdDev)), unit: targetSegment.units[yKey] };
                } else {
                    return { result: null, unit: null };
                }
            }
        }

        const result = _calcEquation(
            targetSegment.equation_form,
            convertedInput,
            a,
            b,
            direction
        );

        return { result: result, unit: targetSegment.units[yKey] };
    } catch (e) {
        return { result: null, unit: null };
    }
}

/**
 * Calculate curve data for plotting
 * @param {Array} modelParams - Array of model segments
 * @param {Array} xValues - Array of x values
 * @param {string} inputUnit - Input unit
 * @param {string} direction - 'forward' or 'inverse'
 * @returns {Object} {yValues: Array, outputUnit: string}
 */
function calculateCurve(modelParams, xValues, inputUnit, direction = 'forward') {
    const yValues = [];
    let outputUnit = "";
    
    for (const x of xValues) {
        const {result, unit} = solveRelationship(modelParams, x, inputUnit, direction);
        yValues.push(result);
        
        if (result !== null && !outputUnit && unit) {
            outputUnit = unit;
        }
    }
    
    return { yValues, outputUnit };
}

/**
 * Generate random number from normal distribution
 * @param {number} mean - Mean of distribution
 * @param {number} stdDev - Standard deviation
 * @returns {number} Random value
 */
function randomNormal(mean, stdDev) {
    // Box-Muller transform
    const u1 = Math.random();
    const u2 = Math.random();
    const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    return z0 * stdDev + mean;
}