/**
 * Simple calculator module for demonstrating automated testing plugin.
 *
 * This module provides basic arithmetic operations and is designed to be used
 * as a test subject for the Automated Testing Plugin for Claude Code.
 */

/**
 * Add two numbers together.
 *
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum of a and b
 *
 * @example
 * add(2, 3)
 * // returns 5
 *
 * @example
 * add(-1, 1)
 * // returns 0
 *
 * @example
 * add(2.5, 3.7)
 * // returns 6.2
 */
function add(a, b) {
  return a + b;
}

/**
 * Subtract second number from first number.
 *
 * @param {number} a - Number to subtract from
 * @param {number} b - Number to subtract
 * @returns {number} The difference between a and b (a - b)
 *
 * @example
 * subtract(5, 3)
 * // returns 2
 *
 * @example
 * subtract(10, 15)
 * // returns -5
 *
 * @example
 * subtract(7.5, 2.5)
 * // returns 5.0
 */
function subtract(a, b) {
  return a - b;
}

/**
 * Multiply two numbers together.
 *
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The product of a and b
 *
 * @example
 * multiply(3, 4)
 * // returns 12
 *
 * @example
 * multiply(-2, 5)
 * // returns -10
 *
 * @example
 * multiply(2.5, 4)
 * // returns 10.0
 */
function multiply(a, b) {
  return a * b;
}

/**
 * Divide first number by second number.
 *
 * @param {number} a - Numerator
 * @param {number} b - Denominator (must not be zero)
 * @returns {number} The quotient of a divided by b
 * @throws {Error} If b is zero
 *
 * @example
 * divide(10, 2)
 * // returns 5.0
 *
 * @example
 * divide(7, 2)
 * // returns 3.5
 *
 * @example
 * divide(-10, 2)
 * // returns -5.0
 *
 * @example
 * divide(5, 0)
 * // throws Error: Cannot divide by zero
 */
function divide(a, b) {
  if (b === 0) {
    throw new Error("Cannot divide by zero");
  }
  return a / b;
}

module.exports = {
  add,
  subtract,
  multiply,
  divide,
};
