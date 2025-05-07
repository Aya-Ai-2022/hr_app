import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# This COLORS dictionary should be defined globally in your script,

# as these functions will reference it.
COLORS = {
    'background': '#F5F6F5',
    'sidebar': '#D1C4E9',
    'text': '#343A40',
    'secondary_text': '#5C6BC0',
    'title_color': '#453299',
    'navy': '#343A40',
    'light_navy': '#5C6BC0',
    'purple': '#6F42C1',
    'light_purple': '#B39DDB',
    'indigo': '#4B0082',
    'light_indigo': '#7E57C2',
    'magenta': '#FF00FF',
    'soft_magenta': '#F06292',
    'card_bg': '#EDE7F6',
    'graph_bg': '#FAF9FE',
    'button_bg': '#6F42C1',
    'button_text': '#FFFFFF',
    'discrete_sequence': ['#343A40', '#6F42C1', '#4B0082', '#FF00FF', '#5C6BC0', '#B39DDB', '#7E57C2', '#F06292'],
    'continuous_scale': ['#B39DDB', '#6F42C1', '#4B0082'],
    'bar_colors': ['#6F42C1', '#7E57C2', '#343A40'],
    'pie_colors': ['#6F42C1', '#343A40', '#FF00FF', '#5C6BC0', '#B39DDB'],
}

# --- Visualization Functions ---
def plot_employee_demographics(dfs: dict):
    dept_salary_df = dfs.get('department_salary_analysis', pd.DataFrame())
    if dept_salary_df.empty:
        st.warning("Data for 'Department Salary Comparison' (department_salary_analysis.csv) not available.")
        return None

    required_cols = ['department', 'avg_salary', 'min_salary', 'max_salary']
    for col in required_cols:
        if col not in dept_salary_df.columns:
            st.error(f"Missing column '{col}' in department_salary_analysis.csv for demographics plot.")
            return None
    numeric_salary_cols = ['avg_salary', 'min_salary', 'max_salary']
    for col in numeric_salary_cols:
        if not pd.api.types.is_numeric_dtype(dept_salary_df[col]):
            # Attempt conversion if not numeric, show error if fails
            try:
                dept_salary_df[col] = pd.to_numeric(dept_salary_df[col])
            except ValueError:
                st.error(f"Column '{col}' in department_salary_analysis.csv must be numeric for demographics plot.")
                return None
        # Check for NaNs after potential conversion and fill with 0 or handle as appropriate
        # For plotting, it's often better to ensure they are numbers, filling NaNs if it makes sense.
        # Here we assume that if a value is NA after to_numeric, it should not be plotted or treated as zero.
        # Plotly handles NaNs by skipping them generally.

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dept_salary_df['department'], y=dept_salary_df['avg_salary'],
        name='Avg Salary', marker_color=COLORS['purple'],
        text=dept_salary_df['avg_salary'].round(0).astype(str), textposition='auto' # Ensure text is string
    ))
    fig.add_trace(go.Bar(
        x=dept_salary_df['department'], y=dept_salary_df['min_salary'],
        name='Min Salary', marker_color=COLORS['light_indigo'],
        text=dept_salary_df['min_salary'].round(0).astype(str), textposition='auto'
    ))
    fig.add_trace(go.Bar(
        x=dept_salary_df['department'], y=dept_salary_df['max_salary'],
        name='Max Salary', marker_color=COLORS['navy'],
        text=dept_salary_df['max_salary'].round(0).astype(str), textposition='auto'
    ))
    fig.update_layout(
        title_text="Department Salary Comparison", barmode='group',
        xaxis_title="Department", yaxis_title="Salary (Currency)",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig

def plot_salary_analysis(dfs: dict):
    exp_df = dfs.get('job_experience_salary', pd.DataFrame())
    if exp_df.empty:
        st.warning("Data for 'Experience vs. Salary' (job_experience_salary.csv) not available.")
        return None
    required_cols = ['avg_experience_(years)', 'avg_salary', 'job_title']
    if not all(col in exp_df.columns for col in required_cols):
        st.error(f"Missing required columns in job_experience_salary.csv. Need: {', '.join(required_cols)}")
        return None
    # Ensure numeric types for relevant columns
    for col in ['avg_experience_(years)', 'avg_salary']:
        if not pd.api.types.is_numeric_dtype(exp_df[col]):
            try:
                exp_df[col] = pd.to_numeric(exp_df[col])
            except ValueError:
                st.error(f"Column '{col}' in job_experience_salary.csv must be numeric.")
                return None

    fig = px.scatter(
        exp_df, x='avg_experience_(years)', y='avg_salary', text='job_title',
        trendline='ols', color='avg_salary', color_continuous_scale=COLORS['continuous_scale'],
        title="Experience vs. Salary",
        labels={
            'avg_experience_(years)': 'Average Experience (Years)',
            'avg_salary': 'Average Salary (Currency)',
            'job_title': 'Job Title'
        }
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig

def plot_hiring_trends(dfs: dict):
    emp_df = dfs.get('all_employees', pd.DataFrame())
    if emp_df.empty or 'hire_date' not in emp_df.columns:
        st.warning("Data for 'Hiring Trends' (all_employees.csv with 'hire_date') not available.")
        return None
    if not pd.api.types.is_datetime64_any_dtype(emp_df['hire_date']):
        # Attempt conversion if not datetime, show error if fails
        try:
            emp_df['hire_date'] = pd.to_datetime(emp_df['hire_date'])
        except Exception: # Catch generic exception from to_datetime
            st.error("'hire_date' column in all_employees.csv is not in a valid date format for hiring trends.")
            return None
    
    emp_df_filtered = emp_df.dropna(subset=['hire_date']) # Remove rows where hire_date is NaT
    if emp_df_filtered.empty:
        st.warning("No valid 'hire_date' data available after attempting to clean for hiring trends.")
        return None

    emp_df_filtered['hire_year'] = emp_df_filtered['hire_date'].dt.year
    hire_trends = emp_df_filtered['hire_year'].value_counts().sort_index().reset_index()
    hire_trends.columns = ['year', 'hires']

    fig = px.line(
        hire_trends, x='year', y='hires', title="Hiring Trends Over Time",
        markers=True, text=hire_trends['hires'], line_shape='linear',
        color_discrete_sequence=[COLORS['purple']],
        labels={'year': 'Year of Hire', 'hires': 'Number of Hires'}
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        xaxis_title="Year", yaxis_title="Number of Hires",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig

def plot_turnover_analysis(dfs: dict):
    turnover_df = dfs.get('job_turnover_analysis', pd.DataFrame())
    if turnover_df.empty:
        st.warning("Data for 'Turnover Rate by Job' (job_turnover_analysis.csv) not available.")
        return None
    required_cols = ['job_title', 'turnover_rate_(%)']
    if not all(col in turnover_df.columns for col in required_cols):
        st.error(f"Missing required columns in job_turnover_analysis.csv. Need: {', '.join(required_cols)}")
        return None
    if not pd.api.types.is_numeric_dtype(turnover_df['turnover_rate_(%)']):
        try:
            turnover_df['turnover_rate_(%)'] = pd.to_numeric(turnover_df['turnover_rate_(%)'])
        except ValueError:
            st.error("'turnover_rate_(%)' column in job_turnover_analysis.csv must be numeric.")
            return None
    
    turnover_df_sorted = turnover_df.dropna(subset=['turnover_rate_(%)', 'job_title']).sort_values('turnover_rate_(%)', ascending=True)
    if turnover_df_sorted.empty:
        st.warning("No valid data to display for turnover analysis after cleaning.")
        return None

    fig = px.bar(
        turnover_df_sorted, y='job_title', x='turnover_rate_(%)',
        title="Turnover Rate by Job Title", orientation='h',
        text=turnover_df_sorted['turnover_rate_(%)'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else ""),
        color='turnover_rate_(%)', color_continuous_scale=COLORS['continuous_scale'],
        labels={
            'job_title': 'Job Title',
            'turnover_rate_(%)': 'Turnover Rate (%)'
        }
    )
    fig.update_traces(textposition='auto')
    fig.update_layout(
        xaxis_title="Turnover Rate (%)", yaxis_title="Job Title",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig

def plot_tenure_distribution(dfs: dict):
    tenure_df = dfs.get('tenure_comparison', pd.DataFrame())
    if tenure_df.empty or 'tenure' not in tenure_df.columns:
        st.warning("Data for 'Tenure Distribution' (tenure_comparison.csv with 'tenure' column) not available.")
        return None
    if not pd.api.types.is_numeric_dtype(tenure_df['tenure']):
        try:
            tenure_df['tenure'] = pd.to_numeric(tenure_df['tenure'])
        except ValueError:
            st.error("'tenure' column in tenure_comparison.csv must be numeric.")
            return None
            
    tenure_df_cleaned = tenure_df.dropna(subset=['tenure'])
    if tenure_df_cleaned.empty:
        st.warning("No valid tenure data to display after cleaning.")
        return None

    fig = px.histogram(
        tenure_df_cleaned, x='tenure', title="Employee Tenure Distribution", nbins=20,
        histnorm='percent', text_auto='.1f', color_discrete_sequence=[COLORS['light_purple']],
        labels={'tenure': 'Tenure (Years)'}
    )
    fig.update_layout(
        xaxis_title="Tenure (Years)", yaxis_title="Percentage of Employees (%)",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig

def plot_salary_distribution(dfs: dict):
    salary_dist_df = dfs.get('salary_distribution', pd.DataFrame())
    if salary_dist_df.empty:
        st.warning("Data for 'Salary Distribution' (salary_distribution.csv) not available.")
        return None
    
    # Assuming columns are 'salary_range' and 'employee_count'
    # If column names vary, this part needs to be more flexible or ensure consistent naming in CSV.
    expected_cols = ['salary_range', 'employee_count']
    if not all(col in salary_dist_df.columns for col in expected_cols):
        if len(salary_dist_df.columns) >= 2:
            st.info("Attempting to use first two columns for salary distribution as 'salary_range' and 'employee_count'.")
            salary_dist_df.columns = ['salary_range', 'employee_count'] + list(salary_dist_df.columns[2:])
        else:
            st.error(f"Salary distribution data needs at least two columns. Expected: {', '.join(expected_cols)}.")
            return None

    if not pd.api.types.is_numeric_dtype(salary_dist_df['employee_count']):
        try:
            salary_dist_df['employee_count'] = pd.to_numeric(salary_dist_df['employee_count'])
        except ValueError:
            st.error("'employee_count' column in salary_distribution.csv must be numeric.")
            return None
            
    salary_dist_df_cleaned = salary_dist_df.dropna(subset=['employee_count', 'salary_range'])
    if salary_dist_df_cleaned.empty:
        st.warning("No valid data for salary distribution after cleaning.")
        return None
        
    fig = px.pie(
        salary_dist_df_cleaned, names='salary_range', values='employee_count',
        hole=0.3, title="Salary Range Distribution",
        color_discrete_sequence=COLORS['pie_colors']
    )
    fig.update_traces(textinfo='percent+label', textposition='inside', insidetextorientation='radial')
    fig.update_layout(
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'],
        legend_title_text='Salary Range'
    )
    return fig

def plot_location_report(dfs: dict):
    loc_df = dfs.get('location_employee_report', pd.DataFrame())
    if loc_df.empty:
        st.warning("Data for 'Location Report' (location_employee_report.csv) not available.")
        return None
    required_cols = ['city', 'average_salary', 'employee_count'] # 'department' for text is optional
    if not all(col in loc_df.columns for col in required_cols):
        st.error(f"Missing required columns in location_employee_report.csv. Need at least: {', '.join(required_cols)}")
        return None
    # Ensure numeric types
    for col in ['average_salary', 'employee_count']:
        if not pd.api.types.is_numeric_dtype(loc_df[col]):
            try:
                loc_df[col] = pd.to_numeric(loc_df[col])
            except ValueError:
                st.error(f"Column '{col}' in location_employee_report.csv must be numeric.")
                return None
                
    loc_df_cleaned = loc_df.dropna(subset=required_cols)
    if loc_df_cleaned.empty:
        st.warning("No valid data for location report after cleaning.")
        return None
        
    text_col = 'department' if 'department' in loc_df_cleaned.columns else None

    fig = px.scatter(
        loc_df_cleaned, x='city', y='average_salary', size='employee_count',
        color='average_salary', color_continuous_scale=COLORS['continuous_scale'],
        title="Employee Distribution and Salary by Location",
        text=text_col, size_max=60,
        labels={
            'city': 'City',
            'average_salary': 'Average Salary (Currency)',
            'employee_count': 'Number of Employees',
            'department': 'Department (hover/text)'
        },
        hover_name='city' # Better hover information
    )
    if text_col:
        fig.update_traces(textposition='top center')
    fig.update_layout(
        xaxis_title="City", yaxis_title="Average Salary (Currency)",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig

def plot_salary_growth(dfs: dict):
    growth_df = dfs.get('salary_growth', pd.DataFrame())
    if growth_df.empty or 'growth_%' not in growth_df.columns:
        st.warning("Data for 'Salary Growth' (salary_growth.csv with 'growth_%' column) not available.")
        return None
    if not pd.api.types.is_numeric_dtype(growth_df['growth_%']):
        try:
            growth_df['growth_%'] = pd.to_numeric(growth_df['growth_%'])
        except ValueError:
            st.error("'growth_%' column in salary_growth.csv must be numeric.")
            return None

    growth_df_cleaned = growth_df.dropna(subset=['growth_%'])
    if growth_df_cleaned.empty:
        st.warning("No valid salary growth data after cleaning.")
        return None
        
    bins = [-float('inf'), -50, -0.0001, 0.0001, 50, float('inf')] # Refined bins to separate negative, zero, positive
    labels = ['Decrease >50%', 'Decrease 0-50%', 'No Change', 'Increase 0-50%', 'Increase >50%']
    # Adjust right=False if you want intervals like [0, 50) instead of (-50, 0]
    growth_df_cleaned['growth_bucket'] = pd.cut(growth_df_cleaned['growth_%'], bins=bins, labels=labels, include_lowest=True, right=True)
    
    growth_dist = growth_df_cleaned['growth_bucket'].value_counts().reindex(labels).fillna(0).reset_index()
    growth_dist.columns = ['growth_range', 'count']

    color_map = {
        'Decrease >50%': COLORS['navy'],
        'Decrease 0-50%': COLORS['light_navy'],
        'No Change': COLORS['light_purple'], # A more neutral color for no change
        'Increase 0-50%': COLORS['purple'],
        'Increase >50%': COLORS['indigo']
    }

    fig = px.bar(
        growth_dist, x='growth_range', y='count',
        title="Distribution of Salary Growth Percentage",
        text='count', color='growth_range',
        color_discrete_map=color_map,
        labels={'growth_range': 'Salary Growth Range (%)', 'count': 'Number of Employees'}
    )
    fig.update_traces(textposition='outside') # 'outside' can be better if bars are short
    fig.update_layout(
        xaxis_title="Growth Range (%)", yaxis_title="Number of Employees",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'],
        showlegend=False
    )
    return fig

def plot_top_salaries(dfs: dict):
    top_df = dfs.get('top_salaries', pd.DataFrame())
    if top_df.empty:
        st.warning("Data for 'Top Salaries' (top_salaries.csv) not available.")
        return None
    required_cols = ['name', 'salary'] # Assuming these column names
    if not all(col in top_df.columns for col in required_cols):
        st.error(f"Missing required columns in top_salaries.csv. Need: {', '.join(required_cols)}")
        return None
    if not pd.api.types.is_numeric_dtype(top_df['salary']):
        try:
            top_df['salary'] = pd.to_numeric(top_df['salary'])
        except ValueError:
            st.error("'salary' column in top_salaries.csv must be numeric.")
            return None
            
    top_df_cleaned = top_df.dropna(subset=['name', 'salary'])
    if top_df_cleaned.empty:
        st.warning("No valid data for top salaries after cleaning.")
        return None
        
    top_df_sorted = top_df_cleaned.sort_values('salary', ascending=False).head(15) # Show top N, e.g., 15

    fig = px.bar(
        top_df_sorted, x='name', y='salary', title="Top 15 Employee Salaries",
        text=top_df_sorted['salary'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A"),
        color='salary', color_continuous_scale=COLORS['continuous_scale'],
        labels={'name': 'Employee Name', 'salary': 'Salary (Currency)'}
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Employee", yaxis_title="Salary (Currency)",
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'],
        xaxis_tickangle=-45 # Angle names if they overlap
    )
    return fig

def main():
    st.set_page_config(layout="wide", page_title="HR Workforce Dynamics Dashboard")

    # Apply custom CSS using the COLORS dictionary (same as previous rewritten script)
    st.markdown(f"""
    <style>
    /* Main app background */
    .main .block-container {{
        background-color: {COLORS['background']};
        padding-top: 3rem; /* Add some padding at the top */
        padding-bottom: 3rem;
    }}
    /* Sidebar styling */
    .st-emotion-cache-16txtl3 {{ /* Target specific Streamlit sidebar class if needed, or use general .sidebar */
        background-color: {COLORS['sidebar']};
    }}
    /* Text styling */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLORS['title_color']}; /* Main title color */
    }}
    h2, h3 {{
        color: {COLORS['navy']}; /* Subheader colors */
    }}
    p, .stMarkdown {{
        color: {COLORS['text']};
    }}
    /* Button styling */
    .stButton>button {{
        background-color: {COLORS['button_bg']};
        color: {COLORS['button_text']};
        border-radius: 5px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {COLORS['purple']}; /* Slightly darker/different on hover */
        color: {COLORS['button_text']};
    }}
    /* Card styling for Home page */
    .card {{
        background-color: {COLORS['card_bg']};
        padding: 20px; /* Increased padding */
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border: 1px solid {COLORS['light_purple']}; /* Subtle border */
        height: 150px; /* Fixed height for cards to ensure alignment */
        display: flex; /* Enable flexbox */
        flex-direction: column; /* Stack children vertically */
        justify-content: center; /* Center content vertically */
        align-items: center; /* Center content horizontally */
    }}
    .card h3 {{ /* Metric value */
        margin: 0 0 5px 0;
        font-size: 28px; /* Larger font for metric */
        color: {COLORS['purple']}; /* Key metric color */
        font-weight: bold;
    }}
    .card p {{ /* Metric label */
        margin: 0;
        font-size: 16px;
        color: {COLORS['secondary_text']};
    }}
    /* GIF container */
    .gif-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }}
    /* Ensure Plotly charts respect the background */
    .plotly-graph-div {{
        background-color: {COLORS['graph_bg']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("HR Dashboard Navigation")
    page_options = ["Home", "Demographics", "Salary Analysis", "Hiring Trends", "Turnover Analysis",
                    "Tenure Distribution", "Salary Distribution", "Location Report",
                    "Salary Growth", "Top Salaries"]
    page = st.sidebar.radio("Select Visualization", page_options)

    # Load and clean data (same as previous rewritten script)
    raw_dfs = load_csv_files(DATA_DIR)
    if not raw_dfs:
        st.error("No CSV files found or loaded from the directory. Dashboard cannot be displayed.")
        return # Stop execution if no data

    dfs = {}
    date_cols_to_clean = ['hire_date', 'start_date', 'end_date', 'date_of_birth']
    for name, df_raw in raw_dfs.items():
        dfs[name] = clean_dataframe(df_raw, date_cols=date_cols_to_clean)

    st.markdown(f"<h1 style='text-align: center; color: {COLORS['title_color']};'>{page} - HR Workforce Dynamics</h1>", unsafe_allow_html=True)
    st.markdown("---") # Thematic break

    if page == "Home":
        if os.path.exists(GIF_PATH):
            st.markdown('<div class="gif-container">', unsafe_allow_html=True)
            st.image(GIF_PATH, width=450)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.sidebar.warning(f"HR GIF not found at {GIF_PATH}.")

        st.markdown("### Key Workforce Metrics")

        # Prepare data for cards, with robust checks (same as previous rewritten script)
        all_employees_df = dfs.get('all_employees', pd.DataFrame())
        job_salary_stats_df = dfs.get('job_salary_statistics', pd.DataFrame())
        dept_salary_analysis_df = dfs.get('department_salary_analysis', pd.DataFrame())
        job_turnover_analysis_df = dfs.get('job_turnover_analysis', pd.DataFrame())
        tenure_comparison_df = dfs.get('tenure_comparison', pd.DataFrame())
        location_report_df = dfs.get('location_employee_report', pd.DataFrame())

        total_employees = len(all_employees_df) if not all_employees_df.empty else "N/A"

        max_salary_val = "N/A"
        if not job_salary_stats_df.empty and 'max_salary' in job_salary_stats_df.columns:
            max_val = job_salary_stats_df['max_salary'].max()
            max_salary_val = f"${max_val:,.0f}" if pd.notnull(max_val) else "N/A"

        top_dept = "N/A"
        if not dept_salary_analysis_df.empty and 'department' in dept_salary_analysis_df.columns and 'employee_count' in dept_salary_analysis_df.columns:
            top_dept_series = dept_salary_analysis_df.sort_values('employee_count', ascending=False)
            if not top_dept_series.empty:
                top_dept = top_dept_series.iloc[0]['department']

        turnover_high_role = "N/A"
        if not job_turnover_analysis_df.empty and 'job_title' in job_turnover_analysis_df.columns and 'turnover_rate_(%)' in job_turnover_analysis_df.columns:
            turnover_series = job_turnover_analysis_df.sort_values('turnover_rate_(%)', ascending=False)
            if not turnover_series.empty:
                turnover_high_role = turnover_series.iloc[0]['job_title']

        avg_tenure_val = "N/A"
        if not tenure_comparison_df.empty and 'tenure' in tenure_comparison_df.columns:
            mean_tenure = tenure_comparison_df['tenure'].mean()
            avg_tenure_val = f"{mean_tenure:.1f} Years" if pd.notnull(mean_tenure) else "N/A"

        top_location = "N/A"
        if not location_report_df.empty and 'employee_count' in location_report_df.columns:
            loc_col_options = ['region', 'city', 'location']
            loc_col_to_use = next((col for col in loc_col_options if col in location_report_df.columns), None)
            if loc_col_to_use:
                top_loc_series = location_report_df.sort_values('employee_count', ascending=False)
                if not top_loc_series.empty:
                    top_location = top_loc_series.iloc[0][loc_col_to_use]

        # Display metrics in a 2-column layout (3 rows of 2 cards)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="card"><h3>{total_employees}</h3><p>Total Employees</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{top_dept}</h3><p>Largest Department</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{avg_tenure_val}</h3><p>Average Tenure</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="card"><h3>{max_salary_val}</h3><p>Highest Salary</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{turnover_high_role}</h3><p>Highest Turnover Role</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{top_location}</h3><p>Top Employee Region/City</p></div>', unsafe_allow_html=True)

    elif page == "Demographics":
        st.subheader("Department Salary Metrics")
        st.markdown("Compare average, minimum, and maximum salaries across different departments.")
        fig = plot_employee_demographics(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    # ... (rest of the elif page == "..." conditions remain the same as the previous full script) ...
    elif page == "Salary Analysis":
        st.subheader("Experience vs. Salary Analysis")
        st.markdown("Explore the correlation between average years of experience and average salary, with a trendline indicating the general relationship.")
        fig = plot_salary_analysis(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Hiring Trends":
        st.subheader("Annual Hiring Trends")
        st.markdown("Visualize the number of new hires per year to understand recruitment patterns over time.")
        fig = plot_hiring_trends(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Turnover Analysis":
        st.subheader("Job Title Turnover Rates")
        st.markdown("Identify which job titles experience the highest and lowest employee turnover rates.")
        fig = plot_turnover_analysis(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Tenure Distribution":
        st.subheader("Employee Tenure Distribution")
        st.markdown("See the distribution of employee tenure in years, showing how long employees tend to stay with the company.")
        fig = plot_tenure_distribution(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Salary Distribution":
        st.subheader("Salary Range Distribution")
        st.markdown("Understand the proportion of employees falling into different salary ranges.")
        fig = plot_salary_distribution(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Location Report":
        st.subheader("Employee Distribution and Salary by Location")
        st.markdown("Visualize employee counts and average salaries across various company locations or cities.")
        fig = plot_location_report(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Salary Growth":
        st.subheader("Salary Growth Percentage Distribution")
        st.markdown("Analyze the distribution of salary growth percentages experienced by employees (e.g., comparing first vs. current salary).")
        fig = plot_salary_growth(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

    elif page == "Top Salaries":
        st.subheader("Top Employee Salaries")
        st.markdown("Display a list of the top-earning employees in the organization.")
        fig = plot_top_salaries(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()