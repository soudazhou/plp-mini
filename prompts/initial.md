1.

/constitution Create governing principles for LegalAnalytics Mini project:

**PROJECT PURPOSE**
This is a learning-focused project designed to master Pirical's technology stack through building a 
People Analytics platform for law firms. The primary goal is educational - transitioning from 
Java/Golang expertise to Python/TypeScript proficiency.

**DEVELOPMENT PRINCIPLES**

1. **Learning-First Approach**
   - Every implementation decision must include educational commentary
   - Code must contain extensive comments comparing Java/Go patterns to Python/TypeScript
   - Document "why" choices were made, not just "what" was implemented
   - Create reusable learning materials for future reference

2. **Specification-Driven Development**
   - Business requirements come before technical implementation
   - Clear separation between "what/why" (specification) and "how" (implementation)
   - All features must have acceptance criteria before coding begins
   - Use iterative refinement rather than one-shot development

3. **Technology Stack Adherence**
   - Must use Pirical's exact technology choices: Python/FastAPI, TypeScript/Angular, PostgreSQL, 
Elasticsearch, AWS services
   - Document architectural decisions and tradeoffs
   - Compare performance and development experience to Java/Go equivalents
   - No shortcuts or familiar technology substitutions

4. **Documentation Standards**
   - All code files require learning-focused header comments
   - Complex functions need inline comments explaining differences from Java/Go
   - Create weekly learning journals tracking progress and insights
   - Maintain comparative analysis documents for major concepts

5. **Quality and Best Practices**
   - Follow idiomatic patterns for each language/framework
   - Implement proper error handling and logging
   - Include unit tests with educational comments
   - Use type hints in Python and strong typing in TypeScript

6. **Realistic Constraints**
   - Simulate real-world law firm requirements and data sensitivity
   - Implement proper security patterns (OAuth2, data protection)
   - Consider scalability and performance implications
   - Design for maintainability and team collaboration

**LEARNING SUCCESS CRITERIA**
- Comprehensive documentation comparing Java/Go to Python/TypeScript patterns
- Working implementation demonstrating all major Pirical technologies
- Ability to explain architectural decisions and technology tradeoffs
- Portfolio of learning materials suitable for interview preparation
- Deep understanding of when and why to use each technology approach

**CONSTRAINTS AND BOUNDARIES**
- No deviation from specified technology stack
- All learning materials must be interview-ready professional quality
- Implementation must demonstrate production-level thinking
- Focus on depth over breadth - master core concepts thoroughly
- Maintain clean git history with educational commit messages

These principles will guide all development decisions and ensure the project serves its educational 
purpose while demonstrating professional software development practices.

2.

/specify Build LegalAnalytics Mini - MVP Version: A minimal People Analytics dashboard for law firms that demonstrates all core technologies in Pirical's stack.

**LEARNING PROJECT CONTEXT**
This is an educational "Hello World" project for a Java/Golang developer transitioning to Pirical's Python/TypeScript technology stack. Focus on demonstrating each technology rather than complex business logic. All implementation must include extensive comparative documentation.

**MINIMAL VIABLE PRODUCT SCOPE**
Create the simplest possible People Analytics platform that touches every part of Pirical's tech stack:

**CORE FEATURES (Minimal)**

1. **Employee Management (CRUD)**
   - Add a new employee (name, email, department, hire date)
   - View list of employees in a simple table
   - Edit employee basic information
   - Delete an employee
   - Search employees by name or department

2. **Time Tracking (Basic)**
   - Log billable hours for an employee (date, hours, matter description)
   - View time entries in a simple list
   - Calculate total hours per employee per month
   - Mark entries as billable/non-billable

3. **Simple Dashboard**
   - Show total number of employees
   - Display total billable hours this month
   - Show average utilization rate across all employees
   - Basic bar chart showing hours by department

4. **Data Upload**
   - Upload employee CSV file (5-10 sample records)
   - Upload time tracking CSV file (20-30 sample entries)
   - Show upload progress and success/error messages

**USER PERSONAS (Simplified)**
1. **HR Admin** - Can add/edit employees and upload data
2. **Lawyer** - Can log time entries and view personal dashboard
3. **Partner** - Can view firm-wide dashboard and reports

**SAMPLE DATA (Minimal)**
- 10 employees total (2 partners, 3 senior associates, 5 associates)
- 2 departments (Corporate Law, Litigation)
- 1 month of time tracking data (50-100 entries)
- No complex hierarchies or relationships

**TECHNOLOGY STACK DEMONSTRATION**
Each component must be implemented to show learning:

1. **Python/FastAPI Backend**
   - Basic CRUD API endpoints for employees and time entries
   - File upload endpoint for CSV processing with Pandas
   - Simple OAuth2 authentication (just login/logout)
   - Database operations using SQLAlchemy

2. **TypeScript/Angular Frontend**
   - Employee list/add/edit components
   - Time tracking form component
   - Simple dashboard with charts (using Chart.js or similar)
   - Basic routing between views
   - HTTP services for API calls

3. **PostgreSQL Database**
   - Two main tables: employees and time_entries
   - Basic relationships (foreign keys)
   - Simple queries and aggregations

4. **Elasticsearch**
   - Index employee data for search functionality
   - Basic search queries by name and department
   - Simple aggregations for dashboard metrics

5. **AWS Services (Basic)**
   - S3: Store uploaded CSV files
   - SQS: Queue CSV processing jobs
   - SNS: Send notification when processing completes
   - Secrets Manager: Store database credentials
   - EC2: Deploy the application

**ACCEPTANCE CRITERIA (Minimal)**
1. User can add an employee and see them in the list immediately
2. User can log time entries and see total hours calculated
3. Dashboard shows current month metrics (employee count, total hours)
4. CSV upload processes successfully and displays confirmation
5. Search finds employees by partial name match
6. Application deploys to AWS and is accessible via URL
7. All sensitive data uses proper authentication

**EDUCATIONAL LEARNING OBJECTIVES**
Demonstrate understanding of:
- Python FastAPI vs Java Spring Boot (basic CRUD patterns)
- SQLAlchemy vs JPA/Hibernate (simple entity relationships)
- TypeScript vs Java (type safety, async patterns)
- Angular vs server-side MVC (component architecture, HTTP services)
- Pandas vs Java Collections (CSV processing)
- OAuth2 implementation differences
- AWS service integration patterns
- Container deployment vs JAR deployment

**OUT OF SCOPE (Future Versions)**
- Complex analytics and reporting
- Advanced dashboard visualizations  
- Multiple user roles and permissions
- Integration with external systems
- Advanced search and filtering
- Performance optimization
- Comprehensive error handling
- Mobile responsiveness
- Real-time notifications

This MVP focuses on demonstrating technical competency with each tool rather than solving complex business problems. Perfect for learning and interview preparation!