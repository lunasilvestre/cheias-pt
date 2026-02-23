/**
 * cheias.pt — Utility functions
 */

/**
 * Debounce a function call.
 * @param {Function} fn
 * @param {number} ms
 * @returns {Function}
 */
export function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/**
 * Format a number with Portuguese locale.
 * @param {number} n
 * @param {number} decimals
 * @returns {string}
 */
export function formatNumber(n, decimals = 0) {
  return new Intl.NumberFormat('pt-PT', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n);
}
