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
function calculateDeterministic(form, x, a, b, direction) {
    try {
        if (x === null || x === undefined || isNaN(x)) {
            console.warn('Invalid input to calculateDeterministic:', x);
            return null;
        }
        
        x = parseFloat(x);
        a = parseFloat(a);
        b = parseFloat(b);
        
        console.log('calculateDeterministic:', { form, x, a, b, direction });
        
        if (form === "log10(Y) = a + b * log10(X)") {
            if (direction === 'forward') {
                if (x <= 0) return null;
                const result = Math.pow(10, a + b * Math.log10(x));
                console.log('Forward log-log result:', result);
                return result;
            } else { // inverse
                if (x <= 0) return null;
                const result = Math.pow(10, (Math.log10(x) - a) / b);
                console.log('Inverse log-log result:', result);
                return result;
            }
        } else if (form === "Y = a + b * log10(X)") {
            if (direction === 'forward') {
                if (x <= 0) return null;
                const result = a + b * Math.log10(x);
                console.log('Forward linear-log result:', result);
                return result;
            } else { // inverse
                const result = Math.pow(10, (x - a) / b);
                console.log('Inverse linear-log result:', result);
                return result;
            }
        } else if (form === "log10(Y) = a + b * X") {
            if (direction === 'forward') {
                const result = Math.pow(10, a + b * x);
                console.log('Forward log-linear result:', result);
                return result;
            } else { // inverse
                if (x <= 0) return null;
                const result = (Math.log10(x) - a) / b;
                console.log('Inverse log-linear result:', result);
                return result;
            }
        } else {
            console.error('Unknown equation form:', form);
        }
    } catch (e) {
        console.error('Error in calculateDeterministic:', e);
        return null;
    }
    return null;
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
        let isInRange = false;
        
        if (direction === 'forward') {
            const rangeX = segment.range_x || [null, null];
            const minX = rangeX[0];
            const maxX = rangeX[1];
            
            if ((minX === null || convertedInput >= minX) && 
                (maxX === null || convertedInput < maxX)) {
                isInRange = true;
            }
        } else { // 'inverse' direction
            const rangeX = segment.range_x || [null, null];
            const minX = rangeX[0];
            const maxX = rangeX[1];
            
            const yAtMinX = minX !== null ? 
                calculateDeterministic(segment.equation_form, minX, 
                    segment.coefficients.a, segment.coefficients.b, 'forward') : null;
            const yAtMaxX = maxX !== null ? 
                calculateDeterministic(segment.equation_form, maxX, 
                    segment.coefficients.a, segment.coefficients.b, 'forward') : null;
            
            let minY, maxY;
            if (yAtMinX === null || yAtMaxX === null || yAtMinX < yAtMaxX) {
                minY = yAtMinX;
                maxY = yAtMaxX;
            } else {
                minY = yAtMaxX;
                maxY = yAtMinX;
            }
            
            if ((minY === null || convertedInput >= minY) && 
                (maxY === null || convertedInput < maxY)) {
                isInRange = true;
            }
        }
        
        if (isInRange) {
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
        
        const result = calculateDeterministic(
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
            if (direction === 'forward') {
                const rangeX = segment.range_x || [null, null];
                const minX = rangeX[0];
                const maxX = rangeX[1];
                
                if ((minX === null || convertedInput >= minX) && 
                    (maxX === null || convertedInput < maxX)) {
                    isWithinAnyRange = true;
                    break;
                }
            } else { // 'inverse'
                const rangeX = segment.range_x || [null, null];
                const minX = rangeX[0];
                const maxX = rangeX[1];
                
                const yAtMinX = minX !== null ? 
                    calculateDeterministic(segment.equation_form, minX, 
                        segment.coefficients.a, segment.coefficients.b, 'forward') : null;
                const yAtMaxX = maxX !== null ? 
                    calculateDeterministic(segment.equation_form, maxX, 
                        segment.coefficients.a, segment.coefficients.b, 'forward') : null;
                
                let minY, maxY;
                if (yAtMinX === null || yAtMaxX === null || yAtMinX < yAtMaxX) {
                    minY = yAtMinX;
                    maxY = yAtMaxX;
                } else {
                    minY = yAtMaxX;
                    maxY = yAtMinX;
                }
                
                if ((minY === null || convertedInput >= minY) && 
                    (maxY === null || convertedInput < maxY)) {
                    isWithinAnyRange = true;
                    break;
                }
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
        
        // Apply model uncertainty if requested
        if (includeModelUncertainty && targetSegment.std_dev_a) {
            try {
                const stdDevA = parseFloat(targetSegment.std_dev_a);
                a = randomNormal(a, stdDevA);
            } catch (e) {
                // If std_dev_a is a range string, skip uncertainty
            }
        }
        
        const result = calculateDeterministic(
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