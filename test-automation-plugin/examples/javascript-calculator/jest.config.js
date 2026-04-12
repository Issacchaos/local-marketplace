/**
 * Jest configuration for javascript-calculator project
 *
 * This configuration is used by the Automated Testing Plugin to:
 * - Detect Jest as the testing framework
 * - Configure test execution settings
 * - Set up coverage reporting
 */

module.exports = {
  // Test environment
  testEnvironment: 'node',

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Coverage settings
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!src/**/*.spec.js'
  ],

  // Coverage thresholds (disabled for example project - plugin will generate tests incrementally)
  // Uncomment and adjust after initial test generation:
  // coverageThreshold: {
  //   global: {
  //     branches: 80,
  //     functions: 80,
  //     lines: 80,
  //     statements: 80
  //   }
  // },

  // Verbose output for better debugging
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Reset mock state between tests
  resetMocks: true,

  // Restore mock state between tests
  restoreMocks: true,
};
