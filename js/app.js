// Main application logic

let currentBatchData = null;
let includeModelUncertainty = true;
let selectedModelsWeights = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Initializing EQ-Scalculator...');
    
    const loaded = await loadAllModels();
    
    if (!loaded) {
        const errorMsg = `
            <div style="padding: 40px; text-align: center;">
                <div class="error">
                    <h2>⚠️ Error Loading Models</h2>
                    <p>Could not load scaling model files. Please check:</p>
                    <ul style="text-align: left; margin: 20px auto; max-width: 500px;">
                        <li>JSON files are in correct locations</li>
                        <li>Browser console for specific errors (F12)</li>
                        <li>Files are valid JSON format</li>
                    </ul>
                    <p>Try refreshing the page.</p>
                </div>
            </div>
        `;
        document.querySelector('.container').innerHTML = errorMsg;
        return;
    }
    
    if (Object.keys(allModels).length === 0) {
        const warningMsg = `
            <div style="padding: 40px; text-align: center;">
                <div class="warning">
                    <h2>⚠️ No Models Loaded</h2>
                    <p>No scaling models were found. Please ensure JSON files exist in the scaling_models directory.</p>
                </div>
            </div>
        `;
        document.querySelector('.container').innerHTML = warningMsg;
        return;
    }
    
    console.log(`Successfully loaded ${Object.keys(allModels).length} model(s)`);
    initializeUI();
});

function initializeUI() {
    const params = getAllParameters();
    
    console.log('Available parameters:', params);
    
    if (params.length === 0) {
        showError('detResults', 'No parameters found in loaded models. Check JSON files.');
        return;
    }
    
    // Populate all parameter dropdowns
    populateSelect('inputParam', params);
    populateSelect('outputParam', params);
    populateSelect('mcInputParam', params);
    populateSelect('mcOutputParam', params);
    populateSelect('plotXParam', params);
    populateSelect('plotYParam', params);
    
    // Set default values - ensure they exist in params
    const defaultInput = params.includes('Mw') ? 'Mw' : params[0];
    const defaultOutput = params.includes('A') ? 'A' : (params[1] || params[0]);
    
    document.getElementById('inputParam').value = defaultInput;
    document.getElementById('outputParam').value = defaultOutput;
    document.getElementById('mcInputParam').value = defaultInput;
    document.getElementById('mcOutputParam').value = defaultOutput;
    document.getElementById('plotXParam').value = defaultInput;
    document.getElementById('plotYParam').value = defaultOutput;
    
    // Initialize configurations
    updateDeterministicConfig();
    updateMonteCarloConfig();
    
    console.log('UI initialized successfully');
}

function populateSelect(elementId, options, selectedValue = null) {
    const select = document.getElementById(elementId);
    select.innerHTML = '';
    
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option;
        select.appendChild(opt);
    });
    
    if (selectedValue) {
        select.value = selectedValue;
    }
}

// Tab switching
function switchTab(index) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
    });
    
    contents.forEach((content, i) => {
        content.classList.toggle('active', i === index);
    });
    
    if (index === 2) {
        setTimeout(() => updatePlot(), 100);
    }
}

// Toggle calculation mode
function toggleCalcMode() {
    const mode = document.querySelector('input[name="calcMode"]:checked').value;
    document.getElementById('singleInputSection').classList.toggle('hidden', mode === 'batch');
    document.getElementById('batchInputSection').classList.toggle('hidden', mode === 'single');
}

// Update deterministic calculation configuration
function updateDeterministicConfig() {
    const inputParam = document.getElementById('inputParam').value;
    const outputParam = document.getElementById('outputParam').value;
    
    // Update available models
    const models = findAvailableModels(inputParam, outputParam);
    const modelSelect = document.getElementById('selectedModel');
    
    populateSelect('selectedModel', Object.keys(models));
    
    if (Object.keys(models).length === 0) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'No models available';
        modelSelect.appendChild(opt);
    }
    
    // Update units
    const inputUnits = getUnitsForParam(inputParam);
    const outputUnits = getUnitsForParam(outputParam);
    
    populateSelect('inputUnit', inputUnits, inputUnits[0]);
    populateSelect('outputUnit', outputUnits, outputUnits[0]);
}

// Update Monte Carlo configuration
function updateMonteCarloConfig() {
    const inputParam = document.getElementById('mcInputParam').value;
    const outputParam = document.getElementById('mcOutputParam').value;
    
    // Update units
    const inputUnits = getUnitsForParam(inputParam);
    const outputUnits = getUnitsForParam(outputParam);
    
    populateSelect('mcInputUnit', inputUnits, inputUnits[0]);
    populateSelect('mcOutputUnit', outputUnits, outputUnits[0]);
    
    // Update model selection
    updateMCModelList();
}

function updateMCModelList() {
    const inputParam = document.getElementById('mcInputParam').value;
    const outputParam = document.getElementById('mcOutputParam').value;
    const models = findAvailableModels(inputParam, outputParam);
    
    const container = document.getElementById('mcModelList');
    container.innerHTML = '';
    
    selectedModelsWeights = {};
    
    const modelKeys = Object.keys(models);
    const defaultWeight = modelKeys.length > 0 ? Math.floor(100 / modelKeys.length) : 0;
    
    modelKeys.forEach((modelId, index) => {
        const item = document.createElement('div');
        item.className = 'model-weight-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `model_${index}`;
        checkbox.checked = true;
        checkbox.onchange = updateTotalWeight;
        
        const label = document.createElement('label');
        label.htmlFor = `model_${index}`;
        label.textContent = modelId;
        
        const weightInput = document.createElement('input');
        weightInput.type = 'number';
        weightInput.min = 0;
        weightInput.max = 100;
        weightInput.value = defaultWeight;
        weightInput.dataset.modelId = modelId;
        weightInput.oninput = updateTotalWeight;
        
        const weightLabel = document.createElement('span');
        weightLabel.textContent = '%';
        weightLabel.style.marginLeft = '5px';
        
        item.appendChild(checkbox);
        item.appendChild(label);
        item.appendChild(weightInput);
        item.appendChild(weightLabel);
        
        container.appendChild(item);
        
        selectedModelsWeights[modelId] = defaultWeight;
    });
    
    updateTotalWeight();
}

function updateTotalWeight() {
    let total = 0;
    const inputs = document.querySelectorAll('#mcModelList input[type="number"]');
    
    selectedModelsWeights = {};
    
    inputs.forEach(input => {
        const checkbox = input.parentElement.querySelector('input[type="checkbox"]');
        if (checkbox.checked) {
            const weight = parseFloat(input.value) || 0;
            total += weight;
            selectedModelsWeights[input.dataset.modelId] = weight;
        }
    });
    
    const totalElem = document.getElementById('totalWeight');
    totalElem.textContent = `${total}%`;
    totalElem.style.color = total === 100 ? 'white' : '#fbbf24';
    
    const runBtn = document.getElementById('mcRunBtn');
    runBtn.disabled = total !== 100 || Object.keys(selectedModelsWeights).length === 0;
}

function toggleModelUncertainty(element) {
    element.classList.toggle('active');
    includeModelUncertainty = element.classList.contains('active');
}

// Deterministic calculation
async function calculateDeterministic() {
    const inputParam = document.getElementById('inputParam').value;
    const outputParam = document.getElementById('outputParam').value;
    const selectedModelId = document.getElementById('selectedModel').value;
    const mode = document.querySelector('input[name="calcMode"]:checked').value;
    
    console.log('Calculate clicked:', { inputParam, outputParam, selectedModelId, mode });
    
    if (!selectedModelId) {
        showError('detResults', 'Please select a model.');
        return;
    }
    
    // Show loading state
    const resultsDiv = document.getElementById('detResults');
    resultsDiv.innerHTML = '<div class="spinner"></div>';
    
    // Use setTimeout to prevent blocking
    setTimeout(() => {
        try {
            if (mode === 'single') {
                calculateSingle();
            } else {
                calculateBatch();
            }
        } catch (error) {
            console.error('Calculation error:', error);
            showError('detResults', `Calculation failed: ${error.message}`);
        }
    }, 100);
}

function calculateSingle() {
    console.log('Starting single calculation...');
    
    const inputParam = document.getElementById('inputParam').value;
    const outputParam = document.getElementById('outputParam').value;
    const inputValue = parseFloat(document.getElementById('inputValue').value);
    const inputUnit = document.getElementById('inputUnit').value;
    const outputUnit = document.getElementById('outputUnit').value;
    const selectedModelId = document.getElementById('selectedModel').value;
    
    console.log('Inputs:', { inputParam, outputParam, inputValue, inputUnit, outputUnit, selectedModelId });
    
    // Validation
    if (isNaN(inputValue)) {
        showError('detResults', 'Please enter a valid numeric input value.');
        return;
    }
    
    if (!selectedModelId) {
        showError('detResults', 'Please select a model.');
        return;
    }
    
    const models = findAvailableModels(inputParam, outputParam);
    console.log('Available models:', models);
    
    const modelInfo = models[selectedModelId];
    console.log('Selected model info:', modelInfo);
    
    if (!modelInfo) {
        showError('detResults', 'Selected model not found. Please choose another model.');
        return;
    }
    
    let result, resultUnit, warning = null;
    
    try {
        // Handle Hanks & Kanamori conversion
        if (selectedModelId === 'Hanks & Kanamori (1979) Definition') {
            console.log('Using Hanks & Kanamori conversion');
            if (inputParam === 'M0') {
                result = m0ToMw(inputValue, inputUnit);
                resultUnit = null;
            } else {
                result = mwToM0(inputValue, inputUnit === 'N/A' ? 'Nm' : inputUnit);
                resultUnit = 'Nm';
            }
        } else {
            console.log('Loading relationship params...');
            const params = getRelationshipParams(modelInfo.paper, modelInfo.fault, modelInfo.key);
            console.log('Params:', params);
            
            if (!params) {
                showError('detResults', 'Could not load model parameters. Please try another model.');
                return;
            }
            
            console.log('Solving relationship...');
            const solved = solveRelationship(params, inputValue, inputUnit, modelInfo.direction);
            console.log('Solved:', solved);
            
            if (solved.error) {
                showError('detResults', 'Calculation error: ' + solved.error);
                return;
            }
            
            result = solved.result;
            resultUnit = solved.unit;
            
            if (result !== null) {
                warning = checkIfExtrapolating(params, inputValue, inputUnit, modelInfo.direction);
            }
        }
        
        console.log('Final result:', { result, resultUnit, warning });
        displayResult(result, resultUnit, outputParam, outputUnit, warning);
        
    } catch (error) {
        console.error('Error in calculateSingle:', error);
        showError('detResults', `Error: ${error.message}`);
    }
}

function displayResult(result, resultUnit, outputParam, outputUnit, warning) {
    const resultsDiv = document.getElementById('detResults');
    
    if (result === null) {
        showError('detResults', 'Calculation failed. Please check your inputs.');
        return;
    }
    
    let finalResult = result;
    let finalUnit = resultUnit;
    
    // Convert to target output unit if needed
    if (outputUnit !== 'N/A' && resultUnit) {
        try {
            finalResult = convertUnits(result, resultUnit, outputUnit);
            finalUnit = outputUnit;
        } catch (e) {
            // Keep original units if conversion fails
        }
    }
    
    // Convert M0 to Mw if output is magnitude
    if (outputParam === 'Mw' && resultUnit) {
        finalResult = m0ToMw(result, resultUnit);
        finalUnit = 'Mw';
    }
    
    const unitDisplay = finalUnit && finalUnit !== 'N/A' ? ` (${finalUnit})` : '';
    
    let html = `
        <div class="result-box">
            <h3>Result</h3>
            <div class="metric">
                <div class="metric-label">${outputParam}${unitDisplay}</div>
                <div class="metric-value">${finalResult.toFixed(4)}</div>
            </div>
    `;
    
    if (warning) {
        html += `<div class="warning">${warning}</div>`;
    }
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        complete: function(results) {
            currentBatchData = results.data;
            displayBatchPreview(results.meta.fields);
        },
        error: function(error) {
            showError('detResults', 'Error reading file: ' + error.message);
        }
    });
}

function displayBatchPreview(columns) {
    const preview = document.getElementById('batchPreview');
    const columnSelection = document.getElementById('columnSelection');
    
    preview.classList.remove('hidden');
    
    columnSelection.innerHTML = `
        <div class="form-group">
            <label for="batchInputColumn">Select Input Column</label>
            <select id="batchInputColumn">
                ${columns.map(col => `<option value="${col}">${col}</option>`).join('')}
            </select>
        </div>
    `;
}

function calculateBatch() {
    if (!currentBatchData) {
        showError('detResults', 'Please upload a file first.');
        return;
    }
    
    const inputColumn = document.getElementById('batchInputColumn')?.value;
    if (!inputColumn) {
        showError('detResults', 'Please select an input column.');
        return;
    }
    
    const inputParam = document.getElementById('inputParam').value;
    const outputParam = document.getElementById('outputParam').value;
    const inputUnit = document.getElementById('inputUnit').value;
    const outputUnit = document.getElementById('outputUnit').value;
    const selectedModelId = document.getElementById('selectedModel').value;
    
    const models = findAvailableModels(inputParam, outputParam);
    const modelInfo = models[selectedModelId];
    
    const outputColumnName = `${outputParam}_${outputUnit}`;
    
    const results = currentBatchData.map(row => {
        const inputValue = parseFloat(row[inputColumn]);
        if (isNaN(inputValue)) {
            return { ...row, [outputColumnName]: null };
        }
        
        let result, resultUnit;
        
        if (selectedModelId === 'Hanks & Kanamori (1979) Definition') {
            if (inputParam === 'M0') {
                result = m0ToMw(inputValue, inputUnit);
                resultUnit = null;
            } else {
                result = mwToM0(inputValue, 'Nm');
                resultUnit = 'Nm';
            }
        } else {
            const params = getRelationshipParams(modelInfo.paper, modelInfo.fault, modelInfo.key);
            const solved = solveRelationship(params, inputValue, inputUnit, modelInfo.direction);
            result = solved.result;
            resultUnit = solved.unit;
        }
        
        if (result !== null && outputUnit !== 'N/A' && resultUnit) {
            try {
                result = convertUnits(result, resultUnit, outputUnit);
            } catch (e) {}
        }
        
        return { ...row, [outputColumnName]: result };
    });
    
    displayBatchResults(results);
}

function displayBatchResults(results) {
    const resultsDiv = document.getElementById('detResults');
    
    const headers = Object.keys(results[0]);
    const tableRows = results.slice(0, 10).map(row => {
        return '<tr>' + headers.map(h => `<td>${row[h] !== null ? row[h] : 'N/A'}</td>`).join('') + '</tr>';
    }).join('');
    
    const html = `
        <div class="result-box">
            <div class="success">Batch calculation complete! Processed ${results.length} rows.</div>
            <h4>Preview (first 10 rows)</h4>
            <table class="stat-table">
                <thead>
                    <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
                </thead>
                <tbody>${tableRows}</tbody>
            </table>
            <button class="btn-primary download-btn" onclick="downloadBatchResults()">Download Full Results (CSV)</button>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    window.batchResults = results;
}

function downloadBatchResults() {
    if (!window.batchResults) return;
    
    const csv = Papa.unparse(window.batchResults);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'eq_scalculator_results.csv';
    a.click();
    URL.revokeObjectURL(url);
}

// Monte Carlo simulation
function runMonteCarlo() {
    const inputParam = document.getElementById('mcInputParam').value;
    const outputParam = document.getElementById('mcOutputParam').value;
    const inputValue = parseFloat(document.getElementById('mcInputValue').value);
    const inputUnit = document.getElementById('mcInputUnit').value;
    const outputUnit = document.getElementById('mcOutputUnit').value;
    const numSims = parseInt(document.getElementById('mcSimulations').value);
    
    const uncType = document.querySelector('input[name="uncType"]:checked').value;
    const uncValue = parseFloat(document.getElementById('mcUncertainty').value);
    
    const resultsDiv = document.getElementById('mcResults');
    resultsDiv.innerHTML = '<div class="spinner"></div>';
    
    setTimeout(() => {
        const results = [];
        const models = findAvailableModels(inputParam, outputParam);
        const modelIds = Object.keys(selectedModelsWeights);
        const weights = modelIds.map(id => selectedModelsWeights[id] / 100);
        
        for (let i = 0; i < numSims; i++) {
            // Apply input uncertainty
            let currentInput = inputValue;
            if (uncType === 'absolute' && uncValue > 0) {
                currentInput = randomNormal(inputValue, uncValue);
            } else if (uncType === 'percentage' && uncValue > 0) {
                currentInput = randomNormal(inputValue, inputValue * uncValue / 100);
            }
            
            // Randomly select model based on weights
            const rand = Math.random();
            let cumWeight = 0;
            let selectedModelId = modelIds[0];
            
            for (let j = 0; j < modelIds.length; j++) {
                cumWeight += weights[j];
                if (rand <= cumWeight) {
                    selectedModelId = modelIds[j];
                    break;
                }
            }
            
            const modelInfo = models[selectedModelId];
            let result, resultUnit;
            
            if (selectedModelId === 'Hanks & Kanamori (1979) Definition') {
                if (inputParam === 'M0') {
                    result = m0ToMw(currentInput, inputUnit);
                    resultUnit = null;
                } else {
                    result = mwToM0(currentInput, 'Nm');
                    resultUnit = 'Nm';
                }
            } else {
                const params = getRelationshipParams(modelInfo.paper, modelInfo.fault, modelInfo.key);
                const solved = solveOneSimulationRun(params, currentInput, inputUnit, 
                    modelInfo.direction, includeModelUncertainty);
                result = solved.result;
                resultUnit = solved.unit;
            }
            
            if (result !== null) {
                if (outputUnit !== 'N/A' && resultUnit) {
                    try {
                        result = convertUnits(result, resultUnit, outputUnit);
                    } catch (e) {}
                }
                if (outputParam === 'Mw' && resultUnit) {
                    result = m0ToMw(result, resultUnit);
                }
                results.push(result);
            }
        }
        
        displayMonteCarloResults(results, outputParam, outputUnit);
    }, 100);
}

function displayMonteCarloResults(results, outputParam, outputUnit) {
    if (results.length === 0) {
        showError('mcResults', 'Simulation failed for all runs.');
        return;
    }
    
    const mean = results.reduce((a, b) => a + b, 0) / results.length;
    const std = Math.sqrt(results.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / results.length);
    const sortedResults = [...results].sort((a, b) => a - b);
    const p16 = sortedResults[Math.floor(results.length * 0.16)];
    const p50 = sortedResults[Math.floor(results.length * 0.50)];
    const p84 = sortedResults[Math.floor(results.length * 0.84)];
    
    const trace = {
        x: results,
        type: 'histogram',
        marker: {
            color: 'rgba(102, 126, 234, 0.7)',
            line: {
                color: 'rgba(102, 126, 234, 1)',
                width: 1
            }
        },
        nbinsx: 50
    };
    
    const layout = {
        title: `Distribution of ${outputParam}`,
        xaxis: { title: `${outputParam} (${outputUnit || ''})` },
        yaxis: { title: 'Frequency' },
        bargap: 0.05
    };
    
    const unitDisplay = outputUnit && outputUnit !== 'N/A' ? ` (${outputUnit})` : '';
    
    const html = `
        <div class="result-box">
            <h3>Simulation Results</h3>
            <div id="mcPlot" style="width: 100%; height: 400px;"></div>
            <h3 style="margin-top: 30px;">Summary Statistics for ${outputParam}${unitDisplay}</h3>
            <table class="stat-table">
                <thead>
                    <tr>
                        <th>Statistic</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Count</td><td>${results.length}</td></tr>
                    <tr><td>Mean</td><td>${mean.toFixed(4)}</td></tr>
                    <tr><td>Std Dev</td><td>${std.toFixed(4)}</td></tr>
                    <tr><td>Min</td><td>${Math.min(...results).toFixed(4)}</td></tr>
                    <tr><td>16th Percentile</td><td>${p16.toFixed(4)}</td></tr>
                    <tr><td>50th Percentile (Median)</td><td>${p50.toFixed(4)}</td></tr>
                    <tr><td>84th Percentile</td><td>${p84.toFixed(4)}</td></tr>
                    <tr><td>Max</td><td>${Math.max(...results).toFixed(4)}</td></tr>
                </tbody>
            </table>
        </div>
    `;
    
    document.getElementById('mcResults').innerHTML = html;
    Plotly.newPlot('mcPlot', [trace], layout, { responsive: true });
}

// Plotting
function updatePlot() {
    const xParam = document.getElementById('plotXParam').value;
    const yParam = document.getElementById('plotYParam').value;
    const xScale = document.getElementById('plotXScale').value;
    const yScale = document.getElementById('plotYScale').value;
    
    const plotDiv = document.getElementById('plotDiv');
    
    if (!xParam || !yParam) {
        plotDiv.innerHTML = '<div class="warning">Please select both X and Y parameters.</div>';
        return;
    }
    
    const models = findAvailableModels(xParam, yParam);
    
    if (Object.keys(models).length === 0) {
        plotDiv.innerHTML = '<div class="warning">No models found for this parameter combination. Try different parameters.</div>';
        return;
    }
    
    try {
        const traces = [];
        const xUnit = getStandardUnit(xParam);
        const yUnit = getStandardUnit(yParam);
        
        // Generate x values
        let xValues;
        if (xParam === 'Mw') {
            xValues = [];
            for (let i = 4.5; i <= 9.0; i += 0.05) {
                xValues.push(i);
            }
        } else if (xParam === 'M0') {
            xValues = [];
            for (let i = 15; i <= 22; i += 0.1) {
                xValues.push(Math.pow(10, i));
            }
        } else {
            xValues = [];
            for (let i = -1; i <= 4; i += 0.05) {
                xValues.push(Math.pow(10, i));
            }
        }
        
        let validTraces = 0;
        
        for (const modelId in models) {
            const modelInfo = models[modelId];
            
            if (modelInfo.paper === 'virtual') {
                // Handle Hanks & Kanamori separately
                if (xParam === 'Mw' && yParam === 'M0') {
                    const yValues = xValues.map(mw => mwToM0(mw, yUnit || 'Nm'));
                    traces.push({
                        x: xValues,
                        y: yValues,
                        mode: 'lines',
                        name: modelId,
                        line: { width: 3, dash: 'dot' }
                    });
                    validTraces++;
                } else if (xParam === 'M0' && yParam === 'Mw') {
                    const yValues = xValues.map(m0 => m0ToMw(m0, xUnit || 'Nm'));
                    traces.push({
                        x: xValues,
                        y: yValues,
                        mode: 'lines',
                        name: modelId,
                        line: { width: 3, dash: 'dot' }
                    });
                    validTraces++;
                }
                continue;
            }
            
            const params = getRelationshipParams(modelInfo.paper, modelInfo.fault, modelInfo.key);
            
            if (!params || !params.length) {
                console.warn(`No parameters found for ${modelId}`);
                continue;
            }
            
            const { yValues, outputUnit } = calculateCurve(params, xValues, xUnit, modelInfo.direction);
            
            // Convert units if needed
            const convertedY = yValues.map(y => {
                if (y === null) return null;
                if (yUnit && outputUnit && yUnit !== outputUnit) {
                    try {
                        return convertUnits(y, outputUnit, yUnit);
                    } catch (e) {
                        return y;
                    }
                }
                return y;
            });
            
            // Filter out null values for plotting
            const validPoints = xValues.map((x, i) => ({x, y: convertedY[i]}))
                                       .filter(p => p.y !== null && !isNaN(p.y) && isFinite(p.y));
            
            if (validPoints.length > 0) {
                traces.push({
                    x: validPoints.map(p => p.x),
                    y: validPoints.map(p => p.y),
                    mode: 'lines',
                    name: modelId,
                    line: { width: 3 }
                });
                validTraces++;
            }
        }
        
        if (validTraces === 0) {
            plotDiv.innerHTML = '<div class="warning">Could not generate plot data for the selected models. The models may not support this parameter range.</div>';
            return;
        }
        
        const layout = {
            title: `${yParam} vs ${xParam}`,
            xaxis: {
                title: `${xParam} ${xUnit ? `(${xUnit})` : ''}`,
                type: xScale
            },
            yaxis: {
                title: `${yParam} ${yUnit ? `(${yUnit})` : ''}`,
                type: yScale
            },
            hovermode: 'closest',
            showlegend: true,
            legend: {
                orientation: 'v',
                x: 1.02,
                y: 1,
                xanchor: 'left'
            },
            margin: {
                l: 60,
                r: 200,
                t: 60,
                b: 60
            }
        };
        
        Plotly.newPlot('plotDiv', traces, layout, { responsive: true });
    } catch (error) {
        console.error('Plot error:', error);
        plotDiv.innerHTML = `<div class="error">Error generating plot: ${error.message}</div>`;
    }
}

// Utility functions
function showError(elementId, message) {
    document.getElementById(elementId).innerHTML = `<div class="error">${message}</div>`;
}