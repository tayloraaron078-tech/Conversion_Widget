const MM_PER_INCH = 25.4;

const mmInput = document.getElementById('mm-input');
const inchInput = document.getElementById('inch-input');
const inchDisplay = document.getElementById('inch-display');
const statusLine = document.getElementById('status');
const calcInput = document.getElementById('calc-input');
const calcResult = document.getElementById('calc-result');

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
