# Tasks: LegalAnalytics Mini - MVP Version

**Input**: Design documents from `/Users/wenxuan.zhou/PLP/plpmin/plp-mini/specs/001-build-legalanalytics-mini/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Project Overview
Full-stack web application with FastAPI backend, Angular frontend, PostgreSQL database, Elasticsearch search, and local AWS service alternatives. Educational focus on learning Python/TypeScript technologies with comprehensive Java/Go comparison documentation.

## Path Structure (Web Application)
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Infrastructure**: `infrastructure/docker-compose.yml`

## Phase 3.1: Setup & Infrastructure
- [x] T001 Create project directory structure (backend/, frontend/, infrastructure/)
- [x] T002 [P] Initialize Python backend with FastAPI, SQLAlchemy, pytest dependencies
- [x] T003 [P] Initialize Angular frontend with TypeScript, Angular CLI, Jest dependencies
- [x] T004 [P] Setup Docker Compose with PostgreSQL, Elasticsearch, Redis, MailHog services
- [x] T005 [P] Configure backend linting (black, flake8, mypy) and formatting
- [x] T006 [P] Configure frontend linting (ESLint, Prettier) and formatting
- [x] T007 Setup database migrations with Alembic in backend/alembic/
- [x] T008 [P] Create backend environment configuration (.env.example, settings.py)
- [x] T009 [P] Create frontend environment configuration (environment.ts files)

## Phase 3.2: Data Models & Database (TDD Prerequisites)
- [x] T010 [P] Department model in backend/src/models/department.py
- [x] T011 [P] User model in backend/src/models/user.py
- [x] T012 [P] Employee model in backend/src/models/employee.py
- [x] T013 [P] TimeEntry model in backend/src/models/time_entry.py
- [x] T014 Create database migration scripts for all models in backend/alembic/versions/
- [x] T015 [P] Database seeding script with sample data in backend/scripts/seed_data.py

## Phase 3.3: Contract Tests (MUST FAIL before implementation)
**CRITICAL: These tests MUST be written and MUST FAIL before ANY API implementation**

### Employee API Contract Tests
- [x] T016 [P] Contract test POST /api/v1/employees in backend/tests/contract/test_employee_post.py
- [x] T017 [P] Contract test GET /api/v1/employees in backend/tests/contract/test_employee_list.py
- [x] T018 [P] Contract test GET /api/v1/employees/{id} in backend/tests/contract/test_employee_get.py
- [ ] T019 [P] Contract test PUT /api/v1/employees/{id} in backend/tests/contract/test_employee_put.py
- [ ] T020 [P] Contract test DELETE /api/v1/employees/{id} in backend/tests/contract/test_employee_delete.py
- [ ] T021 [P] Contract test GET /api/v1/employees/search in backend/tests/contract/test_employee_search.py

### Time Entry API Contract Tests
- [x] T022 [P] Contract test POST /api/v1/time-entries in backend/tests/contract/test_timeentry_post.py
- [ ] T023 [P] Contract test GET /api/v1/time-entries in backend/tests/contract/test_timeentry_list.py
- [ ] T024 [P] Contract test GET /api/v1/time-entries/{id} in backend/tests/contract/test_timeentry_get.py
- [ ] T025 [P] Contract test PUT /api/v1/time-entries/{id} in backend/tests/contract/test_timeentry_put.py
- [ ] T026 [P] Contract test DELETE /api/v1/time-entries/{id} in backend/tests/contract/test_timeentry_delete.py
- [ ] T027 [P] Contract test GET /api/v1/time-entries/summary in backend/tests/contract/test_timeentry_summary.py

### Dashboard API Contract Tests
- [ ] T028 [P] Contract test GET /api/v1/dashboard/overview in backend/tests/contract/test_dashboard_overview.py
- [ ] T029 [P] Contract test GET /api/v1/dashboard/utilization in backend/tests/contract/test_dashboard_utilization.py
- [ ] T030 [P] Contract test GET /api/v1/dashboard/department-hours in backend/tests/contract/test_dashboard_departments.py
- [ ] T031 [P] Contract test GET /api/v1/dashboard/trends in backend/tests/contract/test_dashboard_trends.py

### Upload API Contract Tests
- [ ] T032 [P] Contract test POST /api/v1/upload/employees in backend/tests/contract/test_upload_employees.py
- [ ] T033 [P] Contract test POST /api/v1/upload/time-entries in backend/tests/contract/test_upload_timeentries.py
- [ ] T034 [P] Contract test GET /api/v1/upload/status/{id} in backend/tests/contract/test_upload_status.py
- [ ] T035 [P] Contract test GET /api/v1/upload/history in backend/tests/contract/test_upload_history.py
- [ ] T036 [P] Contract test GET /api/v1/upload/templates/{type} in backend/tests/contract/test_upload_templates.py

## Phase 3.4: Integration Tests (User Stories Validation)
- [ ] T037 [P] Integration test employee management workflow in backend/tests/integration/test_employee_workflow.py
- [ ] T038 [P] Integration test time tracking workflow in backend/tests/integration/test_timetracking_workflow.py
- [ ] T039 [P] Integration test dashboard analytics workflow in backend/tests/integration/test_dashboard_workflow.py
- [ ] T040 [P] Integration test CSV upload workflow in backend/tests/integration/test_upload_workflow.py
- [ ] T041 [P] Integration test employee search workflow in backend/tests/integration/test_search_workflow.py

## Phase 3.5: Core Backend Services (ONLY after tests are failing)
### Repository Pattern Implementation
- [x] T042 [P] Department repository in backend/src/repositories/department_repository.py
- [x] T043 [P] User repository in backend/src/repositories/user_repository.py
- [x] T044 [P] Employee repository in backend/src/repositories/employee_repository.py
- [x] T045 [P] TimeEntry repository in backend/src/repositories/time_entry_repository.py

### Service Layer Implementation
- [x] T046 [P] Department service in backend/src/services/department_service.py
- [x] T047 [P] User service with authentication in backend/src/services/user_service.py
- [x] T048 Employee service in backend/src/services/employee_service.py (depends on T044)
- [x] T049 TimeEntry service in backend/src/services/time_entry_service.py (depends on T045, T048)
- [x] T050 [P] Dashboard analytics service in backend/src/services/dashboard_service.py
- [x] T051 [P] Search service with Elasticsearch in backend/src/services/search_service.py

### Local AWS Service Alternatives
- [x] T052 [P] Local file storage service (S3 alternative) in backend/src/services/local_storage_service.py
- [x] T053 [P] Celery job processing (SQS alternative) in backend/src/services/local_job_service.py
- [x] T054 [P] Local notification service (SNS alternative) in backend/src/services/local_notification_service.py

## Phase 3.6: API Endpoints Implementation
### Authentication & Base
- [ ] T055 Authentication endpoints (/api/v1/auth/*) in backend/src/api/auth.py
- [ ] T056 [P] Health check endpoint in backend/src/api/health.py

### Employee API Endpoints
- [x] T057 POST /api/v1/employees endpoint in backend/src/api/employees.py
- [x] T058 GET /api/v1/employees endpoint in backend/src/api/employees.py (extends T057)
- [x] T059 GET /api/v1/employees/{id} endpoint in backend/src/api/employees.py (extends T057)
- [x] T060 PUT /api/v1/employees/{id} endpoint in backend/src/api/employees.py (extends T057)
- [x] T061 DELETE /api/v1/employees/{id} endpoint in backend/src/api/employees.py (extends T057)
- [x] T062 GET /api/v1/employees/search endpoint in backend/src/api/employees.py (extends T057)

### Time Entry API Endpoints
- [x] T063 POST /api/v1/time-entries endpoint in backend/src/api/time_entries.py
- [x] T064 GET /api/v1/time-entries endpoint in backend/src/api/time_entries.py (extends T063)
- [x] T065 GET /api/v1/time-entries/{id} endpoint in backend/src/api/time_entries.py (extends T063)
- [x] T066 PUT /api/v1/time-entries/{id} endpoint in backend/src/api/time_entries.py (extends T063)
- [x] T067 DELETE /api/v1/time-entries/{id} endpoint in backend/src/api/time_entries.py (extends T063)
- [x] T068 GET /api/v1/time-entries/summary endpoint in backend/src/api/time_entries.py (extends T063)

### Dashboard API Endpoints
- [x] T069 GET /api/v1/dashboard/overview endpoint in backend/src/api/dashboard.py
- [x] T070 GET /api/v1/dashboard/utilization endpoint in backend/src/api/dashboard.py (extends T069)
- [x] T071 GET /api/v1/dashboard/department-hours endpoint in backend/src/api/dashboard.py (extends T069)
- [x] T072 GET /api/v1/dashboard/trends endpoint in backend/src/api/dashboard.py (extends T069)

### Upload API Endpoints
- [x] T073 POST /api/v1/upload/employees endpoint in backend/src/api/upload.py
- [x] T074 POST /api/v1/upload/time-entries endpoint in backend/src/api/upload.py (extends T073)
- [x] T075 GET /api/v1/upload/status/{id} endpoint in backend/src/api/upload.py (extends T073)
- [x] T076 GET /api/v1/upload/history endpoint in backend/src/api/upload.py (extends T073)
- [x] T077 GET /api/v1/upload/templates/{type} endpoint in backend/src/api/upload.py (extends T073)
- [x] T078 GET /api/v1/files/{bucket}/{filename} endpoint in backend/src/api/upload.py (extends T073)

## Phase 3.7: Frontend Core Components
### Angular Services (API Integration)
- [ ] T079 [P] Authentication service in frontend/src/app/services/auth.service.ts
- [ ] T080 [P] Employee service in frontend/src/app/services/employee.service.ts
- [ ] T081 [P] Time entry service in frontend/src/app/services/time-entry.service.ts
- [ ] T082 [P] Dashboard service in frontend/src/app/services/dashboard.service.ts
- [ ] T083 [P] Upload service in frontend/src/app/services/upload.service.ts
- [ ] T084 [P] HTTP interceptor for JWT tokens in frontend/src/app/interceptors/auth.interceptor.ts

### Angular Components & Pages
- [ ] T085 [P] Login component in frontend/src/app/components/auth/login/login.component.ts
- [ ] T086 [P] Employee list component in frontend/src/app/components/employees/employee-list/employee-list.component.ts
- [ ] T087 [P] Employee form component in frontend/src/app/components/employees/employee-form/employee-form.component.ts
- [ ] T088 [P] Employee search component in frontend/src/app/components/employees/employee-search/employee-search.component.ts
- [ ] T089 [P] Time entry list component in frontend/src/app/components/time-entries/time-entry-list/time-entry-list.component.ts
- [ ] T090 [P] Time entry form component in frontend/src/app/components/time-entries/time-entry-form/time-entry-form.component.ts
- [ ] T091 [P] Dashboard overview component in frontend/src/app/components/dashboard/dashboard-overview/dashboard-overview.component.ts
- [ ] T092 [P] Dashboard charts component in frontend/src/app/components/dashboard/dashboard-charts/dashboard-charts.component.ts
- [ ] T093 [P] File upload component in frontend/src/app/components/upload/file-upload/file-upload.component.ts
- [ ] T094 [P] Upload history component in frontend/src/app/components/upload/upload-history/upload-history.component.ts

### Angular Pages & Routing
- [ ] T095 [P] Employees page in frontend/src/app/pages/employees/employees.page.ts
- [ ] T096 [P] Time tracking page in frontend/src/app/pages/time-tracking/time-tracking.page.ts
- [ ] T097 [P] Dashboard page in frontend/src/app/pages/dashboard/dashboard.page.ts
- [ ] T098 [P] Data upload page in frontend/src/app/pages/upload/upload.page.ts
- [ ] T099 App routing configuration in frontend/src/app/app-routing.module.ts

## Phase 3.8: Integration & Middleware
- [ ] T100 Backend database connection and session management in backend/src/database.py
- [ ] T101 JWT authentication middleware in backend/src/middleware/auth_middleware.py
- [ ] T102 CORS configuration in backend/src/middleware/cors_middleware.py
- [ ] T103 Request/response logging middleware in backend/src/middleware/logging_middleware.py
- [ ] T104 Error handling middleware in backend/src/middleware/error_middleware.py
- [ ] T105 Elasticsearch client configuration in backend/src/elasticsearch_client.py
- [ ] T106 Celery worker configuration in backend/src/worker.py

## Phase 3.9: Async Processing & Jobs
- [ ] T107 [P] Employee CSV processing job in backend/src/jobs/employee_csv_processor.py
- [ ] T108 [P] Time entry CSV processing job in backend/src/jobs/time_entry_csv_processor.py
- [ ] T109 [P] Employee search indexing job in backend/src/jobs/search_indexing.py
- [ ] T110 [P] Upload notification job in backend/src/jobs/notification_job.py

## Phase 3.10: Frontend Tests
- [ ] T111 [P] Employee service unit tests in frontend/src/app/services/employee.service.spec.ts
- [ ] T112 [P] Time entry service unit tests in frontend/src/app/services/time-entry.service.spec.ts
- [ ] T113 [P] Dashboard service unit tests in frontend/src/app/services/dashboard.service.spec.ts
- [ ] T114 [P] Login component unit tests in frontend/src/app/components/auth/login/login.component.spec.ts
- [ ] T115 [P] Employee list component unit tests in frontend/src/app/components/employees/employee-list/employee-list.component.spec.ts
- [ ] T116 [P] Dashboard component unit tests in frontend/src/app/components/dashboard/dashboard-overview/dashboard-overview.component.spec.ts

## Phase 3.11: Backend Unit Tests & Validation
- [ ] T117 [P] Department model unit tests in backend/tests/unit/models/test_department.py
- [ ] T118 [P] Employee model unit tests in backend/tests/unit/models/test_employee.py
- [ ] T119 [P] TimeEntry model unit tests in backend/tests/unit/models/test_time_entry.py
- [ ] T120 [P] Employee service unit tests in backend/tests/unit/services/test_employee_service.py
- [ ] T121 [P] Dashboard service unit tests in backend/tests/unit/services/test_dashboard_service.py
- [ ] T122 [P] Local storage service unit tests in backend/tests/unit/services/test_local_storage.py
- [ ] T123 [P] Input validation unit tests in backend/tests/unit/test_validation.py

## Phase 3.12: Performance & Optimization
- [ ] T124 API response time optimization (<200ms target) across all endpoints
- [ ] T125 Database query optimization and indexing validation
- [ ] T126 Frontend bundle size optimization and lazy loading
- [ ] T127 Elasticsearch query performance optimization

## Phase 3.13: Documentation & Polish
- [ ] T128 [P] Backend API documentation generation (OpenAPI/Swagger) in backend/docs/
- [ ] T129 [P] Learning documentation with Java/Go comparisons in backend/README_LEARNING.md
- [ ] T130 [P] Frontend component documentation in frontend/docs/
- [ ] T131 [P] Local AWS alternatives documentation in infrastructure/README_LOCAL_AWS.md
- [ ] T132 Remove code duplication and refactor common patterns
- [ ] T133 Final security review and vulnerability check

## Phase 3.14: End-to-End Validation
- [ ] T134 Execute quickstart.md integration test scenarios
- [ ] T135 Performance validation with concurrent user simulation
- [ ] T136 Local AWS services validation (Redis jobs, file storage, notifications)
- [ ] T137 Cross-browser compatibility testing for frontend
- [ ] T138 API contract validation against OpenAPI specifications

## Dependencies

### Critical Path Dependencies
- **Setup** (T001-T009) → **Models** (T010-T015) → **Contract Tests** (T016-T036)
- **Contract Tests** → **Services** (T042-T054) → **API Endpoints** (T055-T078)
- **API Endpoints** → **Frontend Services** (T079-T084) → **Frontend Components** (T085-T099)

### Service Dependencies
- T048 (Employee service) depends on T044 (Employee repository)
- T049 (TimeEntry service) depends on T045 (TimeEntry repository) + T048 (Employee service)
- All API endpoints depend on their corresponding services
- Frontend components depend on frontend services (T079-T084)

### Integration Dependencies
- T100-T106 (Integration & Middleware) must complete before T134-T138 (End-to-End Validation)
- T107-T110 (Async Jobs) depend on T052-T054 (Local AWS services)
- T134-T138 require ALL previous phases to be complete

### File Modification Conflicts (No [P] marking)
- All employee API endpoints (T057-T062) modify same file: `backend/src/api/employees.py`
- All time entry API endpoints (T063-T068) modify same file: `backend/src/api/time_entries.py`
- All dashboard API endpoints (T069-T072) modify same file: `backend/src/api/dashboard.py`
- All upload API endpoints (T073-T078) modify same file: `backend/src/api/upload.py`

## Parallel Execution Examples

### Phase 3.2: Models (All Independent Files)
```bash
# Launch T010-T013 together:
Task: "Department model in backend/src/models/department.py"
Task: "User model in backend/src/models/user.py"
Task: "Employee model in backend/src/models/employee.py"
Task: "TimeEntry model in backend/src/models/time_entry.py"
```

### Phase 3.3: Contract Tests (All Independent Files)
```bash
# Launch T016-T021 together (Employee API):
Task: "Contract test POST /api/v1/employees in backend/tests/contract/test_employee_post.py"
Task: "Contract test GET /api/v1/employees in backend/tests/contract/test_employee_list.py"
Task: "Contract test GET /api/v1/employees/{id} in backend/tests/contract/test_employee_get.py"
Task: "Contract test PUT /api/v1/employees/{id} in backend/tests/contract/test_employee_put.py"
Task: "Contract test DELETE /api/v1/employees/{id} in backend/tests/contract/test_employee_delete.py"
Task: "Contract test GET /api/v1/employees/search in backend/tests/contract/test_employee_search.py"
```

### Phase 3.5: Repositories (All Independent Files)
```bash
# Launch T042-T045 together:
Task: "Department repository in backend/src/repositories/department_repository.py"
Task: "User repository in backend/src/repositories/user_repository.py"
Task: "Employee repository in backend/src/repositories/employee_repository.py"
Task: "TimeEntry repository in backend/src/repositories/time_entry_repository.py"
```

### Phase 3.7: Frontend Services (All Independent Files)
```bash
# Launch T079-T084 together:
Task: "Authentication service in frontend/src/app/services/auth.service.ts"
Task: "Employee service in frontend/src/app/services/employee.service.ts"
Task: "Time entry service in frontend/src/app/services/time-entry.service.ts"
Task: "Dashboard service in frontend/src/app/services/dashboard.service.ts"
Task: "Upload service in frontend/src/app/services/upload.service.ts"
Task: "HTTP interceptor for JWT tokens in frontend/src/app/interceptors/auth.interceptor.ts"
```

## Validation Checklist

**GATE: All must be ✓ before execution begins**

- [x] All contracts have corresponding tests (T016-T036 cover all 4 contract files)
- [x] All entities have model tasks (T010-T013 cover Department, User, Employee, TimeEntry)
- [x] All tests come before implementation (Phase 3.3 before Phase 3.5-3.6)
- [x] Parallel tasks truly independent (marked [P] only for different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Backend and frontend separated into appropriate directories
- [x] Local AWS alternatives included (T052-T054, T107-T110)
- [x] Educational documentation tasks included (T128-T131)
- [x] Performance and validation tasks included (T124-T138)

## Learning Objectives Addressed

1. **Python/FastAPI vs Java/Spring Boot**: Models, services, repositories, dependency injection
2. **TypeScript/Angular vs Java web frameworks**: Components, services, HTTP clients, routing
3. **SQLAlchemy vs JPA/Hibernate**: ORM patterns, migrations, relationships
4. **PostgreSQL vs traditional RDBMS**: Database design, indexing, performance
5. **Elasticsearch vs Lucene/Solr**: Search implementation, indexing, query patterns
6. **Local AWS vs Real AWS**: Service simulation, environment configuration, migration readiness
7. **Async Processing**: Celery vs Spring Boot async, job queues, notification patterns
8. **Full-Stack Integration**: API design, frontend-backend communication, authentication

## Estimated Total Tasks: 138
- **Setup & Infrastructure**: 9 tasks
- **Models & Database**: 6 tasks
- **Contract Tests**: 21 tasks
- **Integration Tests**: 5 tasks
- **Backend Services**: 10 tasks
- **API Endpoints**: 24 tasks
- **Frontend**: 21 tasks
- **Integration & Middleware**: 7 tasks
- **Async Processing**: 4 tasks
- **Testing & Validation**: 17 tasks
- **Performance & Polish**: 6 tasks
- **Documentation**: 4 tasks
- **End-to-End Validation**: 5 tasks

**Success Criteria**: All quickstart.md scenarios pass, API response times <200ms, local AWS alternatives working, comprehensive learning documentation complete.
