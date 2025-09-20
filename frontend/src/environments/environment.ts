/**
 * Development Environment Configuration
 *
 * Educational comparison between Angular environment configuration
 * and Spring Boot profiles/configuration management.
 *
 * Angular approach:
 * - Compile-time environment switching
 * - TypeScript interfaces for type safety
 * - Build-time replacement via angular.json
 *
 * Spring Boot equivalent:
 * application-dev.yml with profile-specific configuration
 * @Profile("development") annotations
 * @ConfigurationProperties for type-safe config
 */

export const environment = {
  production: false,
  development: true,

  // API Configuration
  apiUrl: 'http://localhost:8000/api/v1',
  apiTimeout: 30000, // 30 seconds

  // Authentication
  tokenKey: 'legalanalytics_token',
  tokenExpirationKey: 'legalanalytics_token_exp',

  // Feature Flags
  features: {
    enableAdvancedSearch: true,
    enableFileUpload: true,
    enableDashboardCharts: true,
    enableRealTimeUpdates: false, // WebSocket features
    enableAuditLogging: true,
  },

  // UI Configuration
  ui: {
    defaultPageSize: 20,
    maxPageSize: 100,
    debounceTime: 300, // milliseconds for search input
    toastDuration: 5000, // milliseconds
    autoRefreshInterval: 30000, // 30 seconds for dashboard
  },

  // File Upload Configuration
  upload: {
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedFileTypes: ['.csv', '.xlsx'],
    chunkSize: 1024 * 1024, // 1MB chunks for large files
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
    animationDuration: 750,
    responsive: true,
  },

  // Logging Configuration
  logging: {
    level: 'debug', // 'error' | 'warn' | 'info' | 'debug'
    enableConsoleLogging: true,
    enableRemoteLogging: false,
  },

  // Local Development Settings
  mock: {
    enableMockData: false,
    apiDelay: 500, // milliseconds to simulate network delay
  },
};

/*
Educational Notes: Angular vs Spring Boot Configuration

1. Environment Switching:
   Angular: Build-time replacement via angular.json
   ```json
   "fileReplacements": [
     {
       "replace": "src/environments/environment.ts",
       "with": "src/environments/environment.prod.ts"
     }
   ]
   ```

   Spring Boot: Runtime profile activation
   ```bash
   java -jar app.jar --spring.profiles.active=production
   ```

2. Type Safety:
   Angular: TypeScript interfaces and compile-time checking
   ```typescript
   interface Environment {
     production: boolean;
     apiUrl: string;
   }
   ```

   Spring Boot: @ConfigurationProperties with validation
   ```java
   @ConfigurationProperties(prefix = "app")
   @Validated
   public class AppConfig {
     @NotNull
     private String apiUrl;
   }
   ```

3. Feature Flags:
   Angular: Simple boolean flags in environment
   Spring Boot: @ConditionalOnProperty or feature flag libraries

4. Build Integration:
   Angular: Angular CLI handles environment switching automatically
   Spring Boot: Maven/Gradle profiles for different configurations
*/