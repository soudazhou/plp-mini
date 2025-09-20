/**
 * Production Environment Configuration
 *
 * Production-optimized settings with security considerations
 * and performance optimizations.
 */

export const environment = {
  production: true,
  development: false,

  // API Configuration - Production URLs
  apiUrl: 'https://api.legalanalytics.com/api/v1',
  apiTimeout: 10000, // Shorter timeout for production

  // Authentication
  tokenKey: 'la_token',
  tokenExpirationKey: 'la_token_exp',

  // Feature Flags - More conservative in production
  features: {
    enableAdvancedSearch: true,
    enableFileUpload: true,
    enableDashboardCharts: true,
    enableRealTimeUpdates: true, // WebSocket features enabled in prod
    enableAuditLogging: true,
  },

  // UI Configuration - Optimized for performance
  ui: {
    defaultPageSize: 20,
    maxPageSize: 50, // Smaller to reduce bandwidth
    debounceTime: 500, // Longer debounce to reduce API calls
    toastDuration: 3000, // Shorter toast duration
    autoRefreshInterval: 60000, // 1 minute for dashboard
  },

  // File Upload Configuration - More restrictive
  upload: {
    maxFileSize: 5 * 1024 * 1024, // 5MB max in production
    allowedFileTypes: ['.csv'], // Only CSV for security
    chunkSize: 512 * 1024, // 512KB chunks
  },

  // Chart Configuration
  charts: {
    defaultColors: [
      '#1f77b4',
      '#ff7f0e',
      '#2ca02c',
      '#d62728',
      '#9467bd',
      '#8c564b',
    ],
    animationDuration: 500, // Faster animations
    responsive: true,
  },

  // Logging Configuration - Minimal logging in production
  logging: {
    level: 'error', // Only log errors in production
    enableConsoleLogging: false,
    enableRemoteLogging: true,
  },

  // Production Settings
  mock: {
    enableMockData: false,
    apiDelay: 0,
  },
};