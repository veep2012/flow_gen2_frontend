/**
 * Convert value to finite number
 * @param {*} value - Value to convert
 * @returns {number} - Finite number or 0
 */
export const toNumber = (value) => {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
};
