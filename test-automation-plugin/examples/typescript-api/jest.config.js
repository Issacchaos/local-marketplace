/**
 * Jest configuration for typescript-api project
 *
 * This configuration is used by the Automated Testing Plugin to:
 * - Detect Jest as the testing framework
 * - Configure TypeScript support via ts-jest
 * - Set up coverage reporting
 * - Configure test execution settings
 *
 * Key features:
 * - TypeScript transformation using ts-jest preset
 * - Strict type checking during tests
 * - Coverage collection from TypeScript source files
 */

module.exports = {
  // Use ts-jest preset for TypeScript support
  preset: 'ts-jest',

  // Test environment
  testEnvironment: 'node',

  // Root directory for tests
  roots: ['<rootDir>/src'],

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.ts',
    '**/?(*.)+(spec|test).ts'
  ],

  // Transform TypeScript files with ts-jest
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      // ts-jest configuration
      tsconfig: {
        // Use strict mode for test type checking
        strict: true,
        // Enable ES module interop
        esModuleInterop: true,
        // Skip lib check for faster compilation
        skipLibCheck: true,
      },
    }],
  },

  // Module file extensions
  moduleFileExtensions: ['ts', 'js', 'json', 'node'],

  // Coverage settings
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
    '!src/**/*.d.ts',
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

  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html'],

  // Coverage directory
  coverageDirectory: 'coverage',

  // Verbose output for better debugging
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Reset mock state between tests
  resetMocks: true,

  // Restore mock state between tests
  restoreMocks: true,

  // Maximum number of concurrent workers
  maxWorkers: '50%',

  // Test timeout (5 seconds)
  testTimeout: 5000,
};
