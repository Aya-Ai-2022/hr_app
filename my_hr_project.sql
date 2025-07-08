CREATE OR REPLACE PACKAGE hr_analysis_pkg AS
    -- Utility Functions
    FUNCTION get_dept_name(p_dept_id IN NUMBER) RETURN VARCHAR2;
    FUNCTION calculate_tenure(p_employee_id IN NUMBER) RETURN NUMBER;

    -- Report Generation Procedures
    PROCEDURE generate_dept_report(p_dept_id IN NUMBER);
    PROCEDURE generate_employee_report(p_dept_id IN NUMBER);
    PROCEDURE export_to_csv(p_query IN VARCHAR2, p_file_name IN VARCHAR2); -- Kept for generic exports
    PROCEDURE generate_salary_rank_report;
    PROCEDURE generate_salary_quartiles;
    PROCEDURE generate_tenure_comparison;
    PROCEDURE generate_top_salaries;
    PROCEDURE generate_salary_growth;
    PROCEDURE generate_job_history_analysis;
    PROCEDURE generate_location_employee_report;
    PROCEDURE generate_job_salary_statistics;
    PROCEDURE generate_salary_distribution;
    PROCEDURE generate_department_salary_analysis;
    PROCEDURE generate_job_experience_salary;
    PROCEDURE generate_top_bottom_jobs;
    PROCEDURE generate_job_turnover_analysis;

    -- Main Procedure to Run All Reports
    PROCEDURE generate_all_reports;
END hr_analysis_pkg;
/



CREATE OR REPLACE PACKAGE BODY hr_analysis_pkg AS
    -- Utility Procedure for File Handling (Standardized Error Handling)
--    PROCEDURE safe_file_operation(p_file IN OUT UTL_FILE.file_type, p_action IN VARCHAR2, p_file_name IN VARCHAR2) IS
--    BEGIN
--        IF p_action = 'OPEN' THEN
--            p_file := UTL_FILE.fopen('HR_ALL', p_file_name => p_file_name, open_mode => 'w');
--        ELSIF p_action = 'CLOSE' AND UTL_FILE.is_open(p_file) THEN
--            UTL_FILE.fclose(p_file);
--        END IF;
--    EXCEPTION
--        WHEN OTHERS THEN
--            IF UTL_FILE.is_open(p_file) THEN UTL_FILE.fclose(p_file); END IF;
--            RAISE_APPLICATION_ERROR(-20000, 'File error in ' || p_action || ': ' || SQLERRM);
--    END safe_file_operation;
PROCEDURE safe_file_operation(p_file IN OUT UTL_FILE.file_type, p_action IN VARCHAR2, p_file_name IN VARCHAR2) IS
    BEGIN
        IF p_action = 'OPEN' THEN
            p_file := UTL_FILE.fopen('HR_ALL', p_file_name, 'w');
        ELSIF p_action = 'CLOSE' AND UTL_FILE.is_open(p_file) THEN
            UTL_FILE.fclose(p_file);
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            IF UTL_FILE.is_open(p_file) THEN UTL_FILE.fclose(p_file); END IF;
            RAISE_APPLICATION_ERROR(-20000, 'File error in ' || p_action || ': ' || SQLERRM);
    END safe_file_operation;
    -- Function: Get Department Name
    FUNCTION get_dept_name(p_dept_id IN NUMBER) RETURN VARCHAR2 IS
        v_dept_name departments.department_name%TYPE;
    BEGIN
        SELECT department_name INTO v_dept_name FROM departments WHERE department_id = p_dept_id;
        RETURN NVL(v_dept_name, 'Department not found');
    EXCEPTION
        WHEN NO_DATA_FOUND THEN RETURN 'Department not found';
    END get_dept_name;

    -- Function: Calculate Tenure
    FUNCTION calculate_tenure(p_employee_id IN NUMBER) RETURN NUMBER IS
        v_hire_date employees.hire_date%TYPE;
    BEGIN
        SELECT hire_date INTO v_hire_date FROM employees WHERE employee_id = p_employee_id;
        RETURN TRUNC(MONTHS_BETWEEN(SYSDATE, v_hire_date) / 12);
    EXCEPTION
        WHEN NO_DATA_FOUND THEN RETURN NULL;
        WHEN OTHERS THEN RETURN NULL;
    END calculate_tenure;

    -- Procedure: Department Report
    PROCEDURE generate_dept_report(p_dept_id IN NUMBER) IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'dept_' || p_dept_id || '.csv');
        UTL_FILE.put_line(v_file, 'Employee ID,Name,Salary,Hire Date,Department');
        FOR rec IN (
            SELECT employee_id, first_name || ' ' || last_name AS emp_name, salary, hire_date
            FROM employees WHERE department_id = p_dept_id
        ) LOOP
            UTL_FILE.put_line(v_file, rec.employee_id || ',' || rec.emp_name || ',' || rec.salary || ',' || 
                             TO_CHAR(rec.hire_date, 'YYYY-MM-DD') || ',' || get_dept_name(p_dept_id));
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'dept_' || p_dept_id || '.csv');
    END generate_dept_report;

    -- Procedure: Employee Report
    PROCEDURE generate_employee_report(p_dept_id IN NUMBER) IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'employees_dept_' || p_dept_id || '.csv');
        UTL_FILE.put_line(v_file, 'Employee ID,Name,Email,Phone,Hire Date,Job Title,Salary,Manager,Department');
        FOR rec IN (
            SELECT e.employee_id, e.first_name || ' ' || e.last_name AS ename, e.email, NVL(e.phone_number, 'N/A') AS phone,
                   e.hire_date, j.job_title, e.salary, NVL(m.first_name || ' ' || m.last_name, 'No Manager') AS manager_name,
                   d.department_name
            FROM employees e
            JOIN jobs j ON e.job_id = j.job_id
            LEFT JOIN employees m ON e.manager_id = m.employee_id
            JOIN departments d ON e.department_id = d.department_id
            WHERE e.department_id = p_dept_id
        ) LOOP
            UTL_FILE.put_line(v_file, rec.employee_id || ',' || rec.ename || ',' || rec.email || ',' || rec.phone || ',' || 
                             TO_CHAR(rec.hire_date, 'YYYY-MM-DD') || ',' || rec.job_title || ',' || rec.salary || ',' || 
                             rec.manager_name || ',' || rec.department_name);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'employees_dept_' || p_dept_id || '.csv');
    END generate_employee_report;

    -- Procedure: Export to CSV (Dynamic, Kept for Flexibility)
    PROCEDURE export_to_csv(p_query IN VARCHAR2, p_file_name IN VARCHAR2) IS
        v_file UTL_FILE.file_type;
        v_stmt INTEGER;
        v_desc DBMS_SQL.desc_tab;
        v_col_cnt NUMBER;
        v_row VARCHAR2(4000);
        v_value VARCHAR2(4000);
        v_rows_fetched NUMBER;
    BEGIN
        safe_file_operation(v_file, 'OPEN', p_file_name);
        v_stmt := DBMS_SQL.open_cursor;
        DBMS_SQL.parse(v_stmt, p_query, DBMS_SQL.native);
        v_rows_fetched := DBMS_SQL.execute(v_stmt);
        DBMS_SQL.describe_columns(v_stmt, v_col_cnt, v_desc);
        v_row := '';
        FOR i IN 1 .. v_col_cnt LOOP
            v_row := v_row || v_desc(i).col_name || ',';
            DBMS_SQL.define_column(v_stmt, i, v_value, 4000);
        END LOOP;
        UTL_FILE.put_line(v_file, RTRIM(v_row, ','));
        LOOP
            v_rows_fetched := DBMS_SQL.fetch_rows(v_stmt);
            EXIT WHEN v_rows_fetched = 0;
            v_row := '';
            FOR i IN 1 .. v_col_cnt LOOP
                DBMS_SQL.column_value(v_stmt, i, v_value);
                v_row := v_row || NVL(v_value, 'NULL') || ',';
            END LOOP;
            UTL_FILE.put_line(v_file, RTRIM(v_row, ','));
        END LOOP;
        DBMS_SQL.close_cursor(v_stmt);
        safe_file_operation(v_file, 'CLOSE', p_file_name);
    END export_to_csv;

    -- Procedure: Salary Rank Report
    PROCEDURE generate_salary_rank_report IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'salary_rank.csv');
        UTL_FILE.put_line(v_file, 'Department,Employee ID,Name,Salary,Rank,Dense Rank');
        FOR rec IN (
            SELECT d.department_name, e.employee_id, e.first_name || ' ' || e.last_name AS emp_name, e.salary,
                   RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS salary_rank,
                   DENSE_RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS dense_salary_rank
            FROM employees e JOIN departments d ON e.department_id = d.department_id
        ) LOOP
            UTL_FILE.put_line(v_file, rec.department_name || ',' || rec.employee_id || ',' || rec.emp_name || ',' || 
                             rec.salary || ',' || rec.salary_rank || ',' || rec.dense_salary_rank);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'salary_rank.csv');
    END generate_salary_rank_report;

    -- Procedure: Salary Quartiles
    PROCEDURE generate_salary_quartiles IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'salary_quartiles.csv');
        UTL_FILE.put_line(v_file, 'Department,Employee ID,Name,Salary,Quartile');
        FOR rec IN (
            SELECT d.department_name, e.employee_id, e.first_name || ' ' || e.last_name AS emp_name, e.salary,
                   NTILE(4) OVER (PARTITION BY e.department_id ORDER BY e.salary) AS quartile
            FROM employees e JOIN departments d ON e.department_id = d.department_id
        ) LOOP
            UTL_FILE.put_line(v_file, rec.department_name || ',' || rec.employee_id || ',' || rec.emp_name || ',' || 
                             rec.salary || ',' || rec.quartile);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'salary_quartiles.csv');
    END generate_salary_quartiles;

    -- Procedure: Tenure Comparison
    PROCEDURE generate_tenure_comparison IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'tenure_comparison.csv');
        UTL_FILE.put_line(v_file, 'Department,Employee ID,Name,Hire Date,Tenure,Prev Tenure,Next Tenure');
        FOR rec IN (
            SELECT d.department_name, e.employee_id, e.first_name || ' ' || e.last_name AS emp_name, e.hire_date,
                   NVL(calculate_tenure(e.employee_id), 0) AS tenure,
                   NVL(LAG(calculate_tenure(e.employee_id)) OVER (PARTITION BY e.department_id ORDER BY e.hire_date), 0) AS prev_tenure,
                   NVL(LEAD(calculate_tenure(e.employee_id)) OVER (PARTITION BY e.department_id ORDER BY e.hire_date), 0) AS next_tenure
            FROM employees e JOIN departments d ON e.department_id = d.department_id
        ) LOOP
            UTL_FILE.put_line(v_file, rec.department_name || ',' || rec.employee_id || ',' || rec.emp_name || ',' || 
                             TO_CHAR(rec.hire_date, 'YYYY-MM-DD') || ',' || rec.tenure || ',' || rec.prev_tenure || ',' || rec.next_tenure);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'tenure_comparison.csv');
    END generate_tenure_comparison;

    -- Procedure: Top Salaries
    PROCEDURE generate_top_salaries IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'top_salaries.csv');
        UTL_FILE.put_line(v_file, 'Department,Employee ID,Name,Salary,Rank');
        FOR rec IN (
            WITH RankedSalaries AS (
                SELECT d.department_name, e.employee_id, e.first_name || ' ' || e.last_name AS emp_name, e.salary,
                       RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS salary_rank
                FROM employees e JOIN departments d ON e.department_id = d.department_id
            ) SELECT * FROM RankedSalaries WHERE salary_rank <= 3
        ) LOOP
            UTL_FILE.put_line(v_file, rec.department_name || ',' || rec.employee_id || ',' || rec.emp_name || ',' || 
                             rec.salary || ',' || rec.salary_rank);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'top_salaries.csv');
    END generate_top_salaries;

    -- Procedure: Salary Growth
    PROCEDURE generate_salary_growth IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'salary_growth.csv');
        UTL_FILE.put_line(v_file, 'Department,Employee ID,Name,Hire Date,Salary,First Salary,Growth %');
        FOR rec IN (
            SELECT d.department_name, e.employee_id, e.first_name || ' ' || e.last_name AS emp_name, e.hire_date, e.salary,
                   FIRST_VALUE(e.salary) OVER (PARTITION BY e.department_id ORDER BY e.hire_date) AS first_salary,
                   NVL(ROUND(((e.salary - FIRST_VALUE(e.salary) OVER (PARTITION BY e.department_id ORDER BY e.hire_date)) /
                             FIRST_VALUE(e.salary) OVER (PARTITION BY e.department_id ORDER BY e.hire_date)) * 100, 2), 0) AS growth_pct
            FROM employees e JOIN departments d ON e.department_id = d.department_id
        ) LOOP
            UTL_FILE.put_line(v_file, rec.department_name || ',' || rec.employee_id || ',' || rec.emp_name || ',' || 
                             TO_CHAR(rec.hire_date, 'YYYY-MM-DD') || ',' || rec.salary || ',' || rec.first_salary || ',' || rec.growth_pct);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'salary_growth.csv');
    END generate_salary_growth;

    -- Procedure: Job History Analysis
    PROCEDURE generate_job_history_analysis IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'job_history_analysis.csv');
        UTL_FILE.put_line(v_file, 'Employee ID,Name,Job Title,Start Date,End Date,Tenure (Months),Job Switch Count');
        FOR rec IN (
            SELECT e.employee_id, e.first_name || ' ' || e.last_name AS emp_name, j.job_title, jh.start_date, jh.end_date,
                   ROUND(MONTHS_BETWEEN(NVL(jh.end_date, SYSDATE), jh.start_date), 1) AS tenure_months,
                   COUNT(*) OVER (PARTITION BY e.employee_id) AS job_switch_count
            FROM employees e JOIN job_history jh ON e.employee_id = jh.employee_id JOIN jobs j ON jh.job_id = j.job_id
            ORDER BY e.employee_id, jh.start_date
        ) LOOP
            UTL_FILE.put_line(v_file, rec.employee_id || ',' || rec.emp_name || ',' || rec.job_title || ',' || 
                             TO_CHAR(rec.start_date, 'YYYY-MM-DD') || ',' || TO_CHAR(rec.end_date, 'YYYY-MM-DD') || ',' || 
                             rec.tenure_months || ',' || rec.job_switch_count);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'job_history_analysis.csv');
    END generate_job_history_analysis;

    -- Procedure: Location Employee Report
    PROCEDURE generate_location_employee_report IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'location_employee_report.csv');
        UTL_FILE.put_line(v_file, 'Region,Country,City,Department,Employee Count,Average Salary');
        FOR rec IN (
            SELECT r.region_name, c.country_name, l.city, d.department_name,
                   NVL(COUNT(e.employee_id), 0) AS emp_count, NVL(ROUND(AVG(e.salary), 2), 0) AS avg_salary
            FROM regions r JOIN countries c ON r.region_id = c.region_id
            JOIN locations l ON c.country_id = l.country_id JOIN departments d ON l.location_id = d.location_id
            LEFT JOIN employees e ON d.department_id = e.department_id
            GROUP BY r.region_name, c.country_name, l.city, d.department_name
        ) LOOP
            UTL_FILE.put_line(v_file, rec.region_name || ',' || rec.country_name || ',' || rec.city || ',' || 
                             rec.department_name || ',' || rec.emp_count || ',' || rec.avg_salary);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'location_employee_report.csv');
    END generate_location_employee_report;

    -- Procedure: Job Salary Statistics
    PROCEDURE generate_job_salary_statistics IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'job_salary_statistics.csv');
        UTL_FILE.put_line(v_file, 'Job ID,Job Title,Department,Total Employees,Avg Salary,Median Salary,Min Salary,Max Salary');
        FOR rec IN (
            SELECT j.job_id, j.job_title, COALESCE(d.department_name, 'N/A') AS department_name,
                   COUNT(e.employee_id) AS total_employees, ROUND(AVG(e.salary), 2) AS avg_salary,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) AS median_salary,
                   MIN(e.salary) AS min_salary, MAX(e.salary) AS max_salary
            FROM employees e JOIN jobs j ON e.job_id = j.job_id LEFT JOIN departments d ON e.department_id = d.department_id
            GROUP BY j.job_id, j.job_title, d.department_name
            ORDER BY avg_salary DESC
        ) LOOP
            UTL_FILE.put_line(v_file, rec.job_id || ',' || rec.job_title || ',' || rec.department_name || ',' || 
                             rec.total_employees || ',' || rec.avg_salary || ',' || rec.median_salary || ',' || 
                             rec.min_salary || ',' || rec.max_salary);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'job_salary_statistics.csv');
    END generate_job_salary_statistics;

    -- Procedure: Salary Distribution
    PROCEDURE generate_salary_distribution IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'salary_distribution.csv');
        UTL_FILE.put_line(v_file, 'Salary Range,Employee Count');
        FOR rec IN (
            SELECT CASE 
                       WHEN salary < 3000 THEN 'Low ( < $3,000 )'
                       WHEN salary BETWEEN 3000 AND 7000 THEN 'Mid ( $3,000 - $7,000 )'
                       ELSE 'High ( > $7,000 )'
                   END AS salary_range, COUNT(*) AS employee_count
            FROM employees
            GROUP BY CASE 
                       WHEN salary < 3000 THEN 'Low ( < $3,000 )'
                       WHEN salary BETWEEN 3000 AND 7000 THEN 'Mid ( $3,000 - $7,000 )'
                       ELSE 'High ( > $7,000 )'
                   END
        ) LOOP
            UTL_FILE.put_line(v_file, rec.salary_range || ',' || rec.employee_count);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'salary_distribution.csv');
    END generate_salary_distribution;

    -- Procedure: Department Salary Analysis
    PROCEDURE generate_department_salary_analysis IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'department_salary_analysis.csv');
        UTL_FILE.put_line(v_file, 'Department,Employee Count,Avg Salary,Min Salary,Max Salary');
        FOR rec IN (
            SELECT d.department_name, COUNT(e.employee_id) AS total_employees, ROUND(AVG(e.salary), 2) AS avg_salary,
                   MIN(e.salary) AS min_salary, MAX(e.salary) AS max_salary
            FROM employees e JOIN departments d ON e.department_id = d.department_id
            GROUP BY d.department_name
        ) LOOP
            UTL_FILE.put_line(v_file, rec.department_name || ',' || rec.total_employees || ',' || rec.avg_salary || ',' || 
                             rec.min_salary || ',' || rec.max_salary);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'department_salary_analysis.csv');
    END generate_department_salary_analysis;

    -- Procedure: Job Experience vs Salary
    PROCEDURE generate_job_experience_salary IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'job_experience_salary.csv');
        UTL_FILE.put_line(v_file, 'Job Title,Avg Salary,Avg Experience (Years)');
        FOR rec IN (
            SELECT j.job_title, ROUND(AVG(e.salary), 2) AS avg_salary,
                   ROUND(AVG(MONTHS_BETWEEN(SYSDATE, e.hire_date) / 12), 1) AS avg_experience_years
            FROM employees e JOIN jobs j ON e.job_id = j.job_id
            GROUP BY j.job_title
        ) LOOP
            UTL_FILE.put_line(v_file, rec.job_title || ',' || rec.avg_salary || ',' || rec.avg_experience_years);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'job_experience_salary.csv');
    END generate_job_experience_salary;

    -- Procedure: Top and Bottom Jobs
    PROCEDURE generate_top_bottom_jobs IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'top_bottom_jobs.csv');
        UTL_FILE.put_line(v_file, 'Job Title,Avg Salary');
        FOR rec IN (
            (SELECT j.job_title, ROUND(AVG(e.salary), 2) AS avg_salary 
             FROM employees e JOIN jobs j ON e.job_id = j.job_id
             GROUP BY j.job_title ORDER BY avg_salary DESC FETCH FIRST 5 ROWS ONLY)
            UNION ALL
            (SELECT j.job_title, ROUND(AVG(e.salary), 2) AS avg_salary 
             FROM employees e JOIN jobs j ON e.job_id = j.job_id
             GROUP BY j.job_title ORDER BY avg_salary ASC FETCH FIRST 5 ROWS ONLY)
        ) LOOP
            UTL_FILE.put_line(v_file, rec.job_title || ',' || rec.avg_salary);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'top_bottom_jobs.csv');
    END generate_top_bottom_jobs;

    -- Procedure: Job Turnover Analysis
    PROCEDURE generate_job_turnover_analysis IS
        v_file UTL_FILE.file_type;
    BEGIN
        safe_file_operation(v_file, 'OPEN', 'job_turnover_analysis.csv');
        UTL_FILE.put_line(v_file, 'Job Title,Current Employees,Past Employees,Turnover Rate (%)');
        FOR rec IN (
            SELECT j.job_title, COUNT(DISTINCT e.employee_id) AS current_employees,
                   COUNT(DISTINCT h.employee_id) AS past_employees,
                   NVL((COUNT(DISTINCT h.employee_id) * 100 / 
                        NULLIF(COUNT(DISTINCT e.employee_id) + COUNT(DISTINCT h.employee_id), 0)), 0) AS turnover_rate
            FROM jobs j LEFT JOIN employees e ON j.job_id = e.job_id LEFT JOIN job_history h ON j.job_id = h.job_id
            GROUP BY j.job_title
        ) LOOP
            UTL_FILE.put_line(v_file, rec.job_title || ',' || rec.current_employees || ',' || rec.past_employees || ',' || 
                             rec.turnover_rate);
        END LOOP;
        safe_file_operation(v_file, 'CLOSE', 'job_turnover_analysis.csv');
    END generate_job_turnover_analysis;

    -- Procedure: Generate All Reports
    PROCEDURE generate_all_reports IS
    BEGIN
        FOR dept IN (SELECT department_id FROM departments) LOOP
            generate_dept_report(dept.department_id);
        END LOOP;
        export_to_csv('SELECT * FROM employees', 'all_employees.csv');
        export_to_csv('SELECT * FROM departments', 'all_departments.csv');
        generate_salary_rank_report;
        generate_salary_quartiles;
        generate_tenure_comparison;
        generate_top_salaries;
        generate_salary_growth;
        generate_job_history_analysis;
        generate_location_employee_report;
        generate_job_salary_statistics;
        generate_salary_distribution;
        generate_department_salary_analysis;
        generate_job_experience_salary;
        generate_top_bottom_jobs;
        generate_job_turnover_analysis;
    END generate_all_reports;
END hr_analysis_pkg;
/



BEGIN
    hr_analysis_pkg.generate_all_reports;
END;