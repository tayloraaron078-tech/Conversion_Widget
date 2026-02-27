const MM_PER_INCH = 25.4;

const mmInput = document.getElementById('mm-input');
const inchInput = document.getElementById('inch-input');
const inchDisplay = document.getElementById('inch-display');
const statusLine = document.getElementById('status');
const calcInput = document.getElementById('calc-input');
const calcResult = document.getElementById('calc-result');
const copyMmButton = document.getElementById('copy-mm');
const copyInchButton = document.getElementById('copy-inch');
const copyResultButton = document.getElementById('copy-result');
const desiredHeightInput = document.getElementById('desired-height');
const layerHeightInput = document.getElementById('layer-height');
const calcLayerButton = document.getElementById('calc-layer');
const layerOutput = document.getElementById('layer-output');
const targetWallInput = document.getElementById('target-wall');
const lineWidthInput = document.getElementById('line-width');
const calcWallButton = document.getElementById('calc-wall');
const wallOutput = document.getElementById('wall-output');
const dimLengthInput = document.getElementById('dim-length');
const dimWidthInput = document.getElementById('dim-width');
const dimHeightInput = document.getElementById('dim-height');
const nozzleSizeInput = document.getElementById('nozzle-size');
const snapLayerHeightInput = document.getElementById('snap-layer-height');
const snapLineWidthInput = document.getElementById('snap-line-width');
const calcSnapButton = document.getElementById('calc-snap');
const snapOutput = document.getElementById('snap-output');

function gcd(a, b) {
  let x = Math.abs(a);
  let y = Math.abs(b);

  while (y) {
    [x, y] = [y, x % y];
  }

  return x || 1;
}

function toMixedFraction(value, maxDenominator = 64) {
  if (!Number.isFinite(value)) {
    return '—';
  }

  const sign = value < 0 ? '-' : '';
  const absValue = Math.abs(value);
  const whole = Math.floor(absValue);
  const fractional = absValue - whole;

  if (fractional < 1e-12) {
    return `${sign}${whole}`;
  }

  let bestNumerator = 0;
  let bestDenominator = 1;
  let minError = Number.POSITIVE_INFINITY;

  for (let denominator = 1; denominator <= maxDenominator; denominator += 1) {
    const numerator = Math.round(fractional * denominator);
    const approximation = numerator / denominator;
    const error = Math.abs(approximation - fractional);

    if (error < minError) {
      minError = error;
      bestNumerator = numerator;
      bestDenominator = denominator;
    }
  }

  if (bestNumerator === 0) {
    return `${sign}${whole}`;
  }

  const divisor = gcd(bestNumerator, bestDenominator);
  const reducedNumerator = bestNumerator / divisor;
  const reducedDenominator = bestDenominator / divisor;

  if (whole === 0) {
    return `${sign}${reducedNumerator}/${reducedDenominator}`;
  }

  return `${sign}${whole} ${reducedNumerator}/${reducedDenominator}`;
}

function parseInchValue(value) {
  const normalized = value.trim();

  if (!normalized) {
    return null;
  }

  const mixedMatch = normalized.match(/^(-?\d+)\s+(\d+)\s*\/\s*(\d+)$/);
  if (mixedMatch) {
    const whole = Number.parseInt(mixedMatch[1], 10);
    const numerator = Number.parseInt(mixedMatch[2], 10);
    const denominator = Number.parseInt(mixedMatch[3], 10);

    if (denominator === 0) {
      return Number.NaN;
    }

    const absWhole = Math.abs(whole);
    const sign = whole < 0 ? -1 : 1;
    return sign * (absWhole + numerator / denominator);
  }

  const fractionMatch = normalized.match(/^(-?\d+)\s*\/\s*(\d+)$/);
  if (fractionMatch) {
    const numerator = Number.parseInt(fractionMatch[1], 10);
    const denominator = Number.parseInt(fractionMatch[2], 10);

    if (denominator === 0) {
      return Number.NaN;
    }

    return numerator / denominator;
  }

  return Number.parseFloat(normalized);
}

function formatDecimal(value, precision = 6) {
  return value.toFixed(precision).replace(/\.?0+$/, '');
}

function parsePositiveNumber(value) {
  const parsed = Number.parseFloat(value.trim());
  return Number.isFinite(parsed) && parsed > 0 ? parsed : Number.NaN;
}

function renderLayerHelper() {
  const desiredHeight = parsePositiveNumber(desiredHeightInput.value);
  const layerHeight = parsePositiveNumber(layerHeightInput.value);

  if (!Number.isFinite(desiredHeight) || !Number.isFinite(layerHeight)) {
    layerOutput.textContent = 'Please enter valid positive numbers for desired height and layer height.';
    return;
  }

  const exactLayers = desiredHeight / layerHeight;
  const lowerLayers = Math.floor(exactLayers);
  const upperLayers = Math.ceil(exactLayers);
  const nearestLayers = Math.round(exactLayers);

  const lowerHeight = lowerLayers * layerHeight;
  const upperHeight = upperLayers * layerHeight;
  const nearestHeight = nearestLayers * layerHeight;

  layerOutput.innerHTML = [
    `Exact layer count: <strong>${formatDecimal(exactLayers, 4)}</strong>`,
    `Nearest clean multiple: <strong>${formatDecimal(nearestHeight, 4)} mm</strong> (${nearestLayers} layers)`,
    `Lower option: ${lowerLayers} layers = ${formatDecimal(lowerHeight, 4)} mm`,
    `Snap up option: ${upperLayers} layers = ${formatDecimal(upperHeight, 4)} mm`,
  ].join('<br>');
}

function renderWallHelper() {
  const targetWall = parsePositiveNumber(targetWallInput.value);
  const lineWidth = parsePositiveNumber(lineWidthInput.value);

  if (!Number.isFinite(targetWall) || !Number.isFinite(lineWidth)) {
    wallOutput.textContent = 'Please enter valid positive numbers for target wall thickness and line width.';
    return;
  }

  const exactWallCount = targetWall / lineWidth;
  const lowerCount = Math.max(1, Math.floor(exactWallCount));
  const upperCount = Math.max(1, Math.ceil(exactWallCount));
  const nearestCount = Math.max(1, Math.round(exactWallCount));

  wallOutput.innerHTML = [
    `Exact wall count: <strong>${formatDecimal(exactWallCount, 4)}</strong>`,
    `Nearest printable count: <strong>${nearestCount} perimeters</strong> = ${formatDecimal(
      nearestCount * lineWidth,
      4,
    )} mm`,
    `Lower option: ${lowerCount} perimeters = ${formatDecimal(lowerCount * lineWidth, 4)} mm`,
    `Snap up option: ${upperCount} perimeters = ${formatDecimal(upperCount * lineWidth, 4)} mm`,
  ].join('<br>');
}

function snapDimension(value, increment) {
  const count = Math.max(1, Math.round(value / increment));
  const snapped = count * increment;
  const delta = snapped - value;

  return {
    count,
    snapped,
    delta,
  };
}

function renderSnapHelper() {
  const length = parsePositiveNumber(dimLengthInput.value);
  const width = parsePositiveNumber(dimWidthInput.value);
  const height = parsePositiveNumber(dimHeightInput.value);
  const nozzle = parsePositiveNumber(nozzleSizeInput.value);
  const layerHeight = parsePositiveNumber(snapLayerHeightInput.value);
  const lineWidth = parsePositiveNumber(snapLineWidthInput.value);

  if (
    !Number.isFinite(length)
    || !Number.isFinite(width)
    || !Number.isFinite(height)
    || !Number.isFinite(nozzle)
    || !Number.isFinite(layerHeight)
    || !Number.isFinite(lineWidth)
  ) {
    snapOutput.textContent = 'Please fill all fields with valid positive numbers.';
    return;
  }

  const lengthSnap = snapDimension(length, lineWidth);
  const widthSnap = snapDimension(width, lineWidth);
  const heightSnap = snapDimension(height, layerHeight);

  snapOutput.innerHTML = [
    `Nozzle: <strong>${formatDecimal(nozzle, 4)} mm</strong> | line width: <strong>${formatDecimal(
      lineWidth,
      4,
    )} mm</strong> | layer: <strong>${formatDecimal(layerHeight, 4)} mm</strong>`,
    `Length → ${lengthSnap.count} lines = ${formatDecimal(lengthSnap.snapped, 4)} mm (${formatDecimal(
      lengthSnap.delta,
      4,
    )} mm adjustment)`,
    `Width → ${widthSnap.count} lines = ${formatDecimal(widthSnap.snapped, 4)} mm (${formatDecimal(
      widthSnap.delta,
      4,
    )} mm adjustment)`,
    `Height → ${heightSnap.count} layers = ${formatDecimal(heightSnap.snapped, 4)} mm (${formatDecimal(
      heightSnap.delta,
      4,
    )} mm adjustment)`,
  ].join('<br>');
}

function updateFromMm() {
  const mm = Number.parseFloat(mmInput.value.trim());

  if (!mmInput.value.trim()) {
    inchInput.value = '';
    inchDisplay.textContent = 'Inch display: decimal — | fraction —';
    statusLine.textContent = '';
    return;
  }

  if (!Number.isFinite(mm)) {
    statusLine.textContent = 'Enter a valid number in millimeters.';
    return;
  }

  statusLine.textContent = '';
  const inches = mm / MM_PER_INCH;
  inchInput.value = formatDecimal(inches);
  inchDisplay.textContent = `Inch display: decimal ${formatDecimal(inches)} | fraction ${toMixedFraction(
    inches,
  )}`;
}

function updateFromInches() {
  const raw = inchInput.value;
  const inches = parseInchValue(raw);

  if (!raw.trim()) {
    mmInput.value = '';
    inchDisplay.textContent = 'Inch display: decimal — | fraction —';
    statusLine.textContent = '';
    return;
  }

  if (!Number.isFinite(inches)) {
    statusLine.textContent = 'Use decimal or fraction format (example: 1.25, 1/4, 1 1/4).';
    return;
  }

  statusLine.textContent = '';
  mmInput.value = formatDecimal(inches * MM_PER_INCH);
  inchDisplay.textContent = `Inch display: decimal ${formatDecimal(inches)} | fraction ${toMixedFraction(
    inches,
  )}`;
}

function evaluateExpression(expression) {
  const trimmed = expression.trim();

  if (!trimmed) {
    return { result: null, error: null };
  }

  if (!/^[\d+\-*/().\s%]+$/.test(trimmed)) {
    return { result: null, error: 'Only arithmetic characters are allowed.' };
  }

  try {
    const value = Function(`"use strict"; return (${trimmed});`)();
    if (!Number.isFinite(value)) {
      return { result: null, error: 'Expression did not produce a finite number.' };
    }

    return { result: value, error: null };
  } catch {
    return { result: null, error: 'Invalid expression.' };
  }
}

async function copyTextToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.setAttribute('readonly', '');
  textArea.style.position = 'absolute';
  textArea.style.left = '-9999px';
  document.body.appendChild(textArea);
  textArea.select();
  const successful = document.execCommand('copy');
  document.body.removeChild(textArea);

  if (!successful) {
    throw new Error('Copy command failed.');
  }
}

function pulseButton(button, label = 'Copied!') {
  const originalText = button.textContent;
  button.textContent = label;
  button.disabled = true;

  window.setTimeout(() => {
    button.textContent = originalText;
    button.disabled = false;
  }, 1000);
}

async function copyFieldValue(getValue, button, emptyMessage) {
  const value = getValue().trim();
  if (!value || value === '—') {
    statusLine.textContent = emptyMessage;
    return;
  }

  try {
    await copyTextToClipboard(value);
    statusLine.textContent = '';
    pulseButton(button);
  } catch {
    statusLine.textContent = 'Unable to copy to clipboard in this browser context.';
  }
}

mmInput.addEventListener('input', updateFromMm);
inchInput.addEventListener('input', updateFromInches);

calcInput.addEventListener('input', () => {
  const { result, error } = evaluateExpression(calcInput.value);

  if (error) {
    calcResult.textContent = `Result: ${error}`;
    return;
  }

  if (result === null) {
    calcResult.textContent = 'Result: —';
    return;
  }

  calcResult.textContent = `Result: ${formatDecimal(result, 10)}`;
});

copyMmButton.addEventListener('click', () => {
  copyFieldValue(() => mmInput.value, copyMmButton, 'Millimeter field is empty.');
});

copyInchButton.addEventListener('click', () => {
  copyFieldValue(() => inchInput.value, copyInchButton, 'Inch field is empty.');
});

copyResultButton.addEventListener('click', () => {
  const { result, error } = evaluateExpression(calcInput.value);

  if (error || result === null) {
    statusLine.textContent = 'Enter a valid arithmetic expression to copy its result.';
    return;
  }

  copyFieldValue(() => formatDecimal(result, 10), copyResultButton, 'No result available to copy.');
});

calcLayerButton.addEventListener('click', renderLayerHelper);
calcWallButton.addEventListener('click', renderWallHelper);
calcSnapButton.addEventListener('click', renderSnapHelper);
