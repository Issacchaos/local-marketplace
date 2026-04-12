/**
 * Simple API Client for demonstrating TypeScript testing with automated testing plugin.
 *
 * This module provides a REST API client with TypeScript types and modern async/await patterns.
 * It is designed to be used as a test subject for the Automated Testing Plugin for Claude Code.
 *
 * Features demonstrated:
 * - TypeScript interfaces and types
 * - Generics for flexible API responses
 * - Async/await for asynchronous operations
 * - Error handling with custom error types
 * - No external HTTP dependencies (uses simulated responses)
 */

/**
 * HTTP methods supported by the API client
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

/**
 * Configuration options for the API client
 */
export interface ApiConfig {
  /** Base URL for all API requests */
  baseUrl: string;
  /** Optional timeout in milliseconds */
  timeout?: number;
  /** Optional headers to include in all requests */
  headers?: Record<string, string>;
}

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T> {
  /** Response data of generic type T */
  data: T;
  /** HTTP status code */
  status: number;
  /** Status text (e.g., "OK", "Created") */
  statusText: string;
  /** Response headers */
  headers: Record<string, string>;
}

/**
 * User data model
 */
export interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

/**
 * API request options
 */
export interface RequestOptions {
  /** Optional query parameters */
  params?: Record<string, string | number>;
  /** Optional request body */
  body?: unknown;
  /** Optional request-specific headers */
  headers?: Record<string, string>;
}

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly response?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * API Client class with TypeScript types and async/await patterns
 *
 * @example
 * const client = new ApiClient({ baseUrl: 'https://api.example.com' });
 * const users = await client.get<User[]>('/users');
 * console.log(users.data);
 */
export class ApiClient {
  private config: Required<ApiConfig>;

  /**
   * Create a new API client instance
   *
   * @param config - Configuration options for the client
   *
   * @example
   * const client = new ApiClient({
   *   baseUrl: 'https://api.example.com',
   *   timeout: 5000,
   *   headers: { 'Authorization': 'Bearer token' }
   * });
   */
  constructor(config: ApiConfig) {
    this.config = {
      baseUrl: config.baseUrl,
      timeout: config.timeout ?? 5000,
      headers: config.headers ?? {},
    };
  }

  /**
   * Build full URL with query parameters
   *
   * @param endpoint - API endpoint path
   * @param params - Optional query parameters
   * @returns Full URL with query string
   *
   * @example
   * buildUrl('/users', { page: 1, limit: 10 })
   * // returns 'https://api.example.com/users?page=1&limit=10'
   */
  private buildUrl(endpoint: string, params?: Record<string, string | number>): string {
    const url = new URL(endpoint, this.config.baseUrl);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, String(value));
      });
    }

    return url.toString();
  }

  /**
   * Simulate HTTP request (no external dependencies)
   * In a real implementation, this would use fetch() or an HTTP library
   *
   * @param method - HTTP method
   * @param url - Full URL
   * @param options - Request options
   * @returns Simulated API response
   */
  private async simulateRequest<T>(
    method: HttpMethod,
    url: string,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 100));

    // Simulate 404 for invalid endpoints
    if (url.includes('/invalid') || url.includes('/not-found')) {
      throw new ApiError('Not Found', 404, { error: 'Resource not found' });
    }

    // Simulate 500 for error endpoints
    if (url.includes('/error')) {
      throw new ApiError('Internal Server Error', 500, { error: 'Server error' });
    }

    // Simulate successful response
    const mockData = this.getMockData<T>(url, method);

    return {
      data: mockData,
      status: method === 'POST' ? 201 : 200,
      statusText: method === 'POST' ? 'Created' : 'OK',
      headers: {
        'content-type': 'application/json',
        ...this.config.headers,
      },
    };
  }

  /**
   * Generate mock data based on endpoint
   * This is for demonstration purposes only
   */
  private getMockData<T>(url: string, method: HttpMethod): T {
    if (url.includes('/users') && method === 'GET') {
      return [
        {
          id: 1,
          name: 'Alice',
          email: 'alice@example.com',
          createdAt: new Date('2024-01-01'),
        },
        {
          id: 2,
          name: 'Bob',
          email: 'bob@example.com',
          createdAt: new Date('2024-01-02'),
        },
      ] as T;
    }

    if (url.includes('/users') && method === 'POST') {
      return {
        id: 3,
        name: 'Charlie',
        email: 'charlie@example.com',
        createdAt: new Date(),
      } as T;
    }

    return {} as T;
  }

  /**
   * Perform a GET request
   *
   * @param endpoint - API endpoint path
   * @param options - Optional request options
   * @returns Promise resolving to API response with data of type T
   *
   * @example
   * const response = await client.get<User[]>('/users');
   * console.log(response.data); // Array of users
   *
   * @example
   * const response = await client.get<User[]>('/users', {
   *   params: { page: 1, limit: 10 }
   * });
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, options?.params);
    return this.simulateRequest<T>('GET', url, options);
  }

  /**
   * Perform a POST request
   *
   * @param endpoint - API endpoint path
   * @param options - Optional request options including body
   * @returns Promise resolving to API response with data of type T
   *
   * @example
   * const response = await client.post<User>('/users', {
   *   body: { name: 'Alice', email: 'alice@example.com' }
   * });
   * console.log(response.data); // Created user
   */
  async post<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, options?.params);
    return this.simulateRequest<T>('POST', url, options);
  }

  /**
   * Perform a PUT request
   *
   * @param endpoint - API endpoint path
   * @param options - Optional request options including body
   * @returns Promise resolving to API response with data of type T
   *
   * @example
   * const response = await client.put<User>('/users/1', {
   *   body: { name: 'Alice Updated' }
   * });
   */
  async put<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, options?.params);
    return this.simulateRequest<T>('PUT', url, options);
  }

  /**
   * Perform a DELETE request
   *
   * @param endpoint - API endpoint path
   * @param options - Optional request options
   * @returns Promise resolving to API response with data of type T
   *
   * @example
   * const response = await client.delete<void>('/users/1');
   * console.log(response.status); // 200
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    const url = this.buildUrl(endpoint, options?.params);
    return this.simulateRequest<T>('DELETE', url, options);
  }

  /**
   * Get the base URL of the API client
   *
   * @returns The configured base URL
   *
   * @example
   * client.getBaseUrl()
   * // returns 'https://api.example.com'
   */
  getBaseUrl(): string {
    return this.config.baseUrl;
  }

  /**
   * Get the timeout configuration
   *
   * @returns The configured timeout in milliseconds
   *
   * @example
   * client.getTimeout()
   * // returns 5000
   */
  getTimeout(): number {
    return this.config.timeout;
  }

  /**
   * Update client configuration headers
   *
   * @param headers - Headers to merge with existing headers
   *
   * @example
   * client.setHeaders({ 'Authorization': 'Bearer new-token' });
   */
  setHeaders(headers: Record<string, string>): void {
    this.config.headers = { ...this.config.headers, ...headers };
  }
}

/**
 * Utility function to create a configured API client
 *
 * @param baseUrl - Base URL for the API
 * @param options - Optional configuration options
 * @returns Configured API client instance
 *
 * @example
 * const client = createApiClient('https://api.example.com', {
 *   timeout: 10000,
 *   headers: { 'X-API-Key': 'abc123' }
 * });
 */
export function createApiClient(
  baseUrl: string,
  options?: Omit<ApiConfig, 'baseUrl'>
): ApiClient {
  return new ApiClient({ baseUrl, ...options });
}

/**
 * Type guard to check if an error is an ApiError
 *
 * @param error - Error to check
 * @returns True if error is an ApiError instance
 *
 * @example
 * try {
 *   await client.get('/invalid');
 * } catch (error) {
 *   if (isApiError(error)) {
 *     console.log(error.statusCode); // 404
 *   }
 * }
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
