import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import statsmodels.api as sm
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import statsmodels.api 

DATA_DIR = "HR_ALL"
DATE_FORMAT = "%d-%b-%y"
GIF_PATH = "./assets/emp.gif"

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
 'pie_colors': ['#6F42C1', '#343A40', '#FF00FF', '#5C6BC0', '#B39DDB', '#4B0082'],
}
# --- Data Loading and Caching ---
@st.cache_data
def load_csv_files(directory: str) -> dict:
    """Loads all CSV files from a directory into pandas DataFrames."""
    dataframes = {}
    if not os.path.exists(directory) or not os.path.isdir(directory):
        # This error will be caught in main() if directory doesn't exist.
        # Still good to have a check here if called elsewhere.
        return dataframes
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            try:
                df = pd.read_csv(filepath)
                # Standardize column names
                df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
                dataframes[filename[:-4].lower().replace(" ", "_").replace("-", "_")] = df # Standardize dict keys
            except Exception as e:
                st.warning(f"Error loading {filename}: {e}")
    return dataframes

@st.cache_data
def clean_dataframe(df: pd.DataFrame, date_cols: list = None, numeric_cols: list = None) -> pd.DataFrame:
    """Cleans a DataFrame: handles NA, strips strings, converts dates and numerics."""
    df_copy = df.copy() # Work on a copy to avoid mutating cached objects inplace

    df_copy.replace(['NULL', 'null', '', 'NA', 'N/A', 'NaN', 'nan'], pd.NA, inplace=True)

    for col in df_copy.select_dtypes(include=['object']).columns:
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].astype(str).str.strip().str.replace('"', '', regex=False)
            df_copy[col].replace(['None', '<NA>'], pd.NA, inplace=True) # Replace string 'None' or '<NA>' after strip

    if date_cols:
        for col in date_cols:
            if col in df_copy.columns:
                df_copy[col] = pd.to_datetime(df_copy[col], format=DATE_FORMAT, errors='coerce')

    # Define a more comprehensive list of potential numeric columns likely in HR data
    default_numeric_cols = [
        'employee_count', 'salary', 'avg_salary', 'min_salary', 'max_salary',
        'median_salary', 'tenure', 'growth_%', 'turnover_rate_(%)',
        'average_salary', 'avg_experience_(years)', 'age', 'performance_rating',
        'bonus', 'compensation', 'fte' # Full-Time Equivalent
    ]
    numeric_cols_to_convert = list(set((numeric_cols or []) + default_numeric_cols))

    for col in numeric_cols_to_convert:
        if col in df_copy.columns:
            # Attempt to remove currency symbols or commas before converting
            if df_copy[col].dtype == 'object':
                df_copy[col] = df_copy[col].astype(str).str.replace(r'[$,]', '', regex=True)
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
    return df_copy

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
            try: dept_salary_df[col] = pd.to_numeric(dept_salary_df[col])
            except ValueError:
                st.error(f"Column '{col}' in department_salary_analysis.csv must be numeric for demographics plot.")
                return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dept_salary_df['department'], y=dept_salary_df['avg_salary'],
        name='Avg Salary', marker_color=COLORS['purple'],
        text=dept_salary_df['avg_salary'].round(0).astype(str), textposition='auto'
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
    for col in ['avg_experience_(years)', 'avg_salary']:
        if not pd.api.types.is_numeric_dtype(exp_df[col]):
            try:
                exp_df[col] = pd.to_numeric(exp_df[col])
            except ValueError:
                st.error(f"Column '{col}' in job_experience_salary.csv must be numeric.")
                return None

    trendline_arg = 'ols'
    try:
  
        import statsmodels.api # Try to import to see if it's available
    except ImportError:
        trendline_arg = None # Set trendline to None if statsmodels is not found
        st.info("`statsmodels` library not found. Plotting Experience vs. Salary without OLS trendline. To enable trendline, please install statsmodels (`pip install statsmodels`).")

    fig = px.scatter(
        exp_df,
        x='avg_experience_(years)',
        y='avg_salary',
        hover_name='job_title',
        hover_data={'avg_experience_(years)': ':.1f', 'avg_salary': ':,.0f', 'job_title': False},
        trendline=trendline_arg, # Use the determined trendline_arg
        color='avg_salary',
        color_continuous_scale=COLORS['continuous_scale'],
        title="Experience vs. Salary" + (" (Hover for Job Title)" if trendline_arg else " (Hover for Job Title - Trendline disabled)"),
        labels={
            'avg_experience_(years)': 'Average Experience (Years)',
            'avg_salary': 'Average Salary (Currency)',
        }
    )
    fig.update_layout(
        paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text']
    )
    return fig


def plot_hiring_trends(dfs: dict):
    emp_df = dfs.get('all_employees', pd.DataFrame()) # Assuming 'all_employees' is the correct key
    if emp_df.empty or 'hire_date' not in emp_df.columns:
        st.warning("Data for 'Hiring Trends' (all_employees.csv with 'hire_date') not available.")
        return None
    if not pd.api.types.is_datetime64_any_dtype(emp_df['hire_date']):
        try: emp_df['hire_date'] = pd.to_datetime(emp_df['hire_date'])
        except Exception:
            st.error("'hire_date' column in all_employees.csv is not in a valid date format for hiring trends.")
            return None
    
    emp_df_filtered = emp_df.dropna(subset=['hire_date'])
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
        try: turnover_df['turnover_rate_(%)'] = pd.to_numeric(turnover_df['turnover_rate_(%)'])
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
    tenure_df = dfs.get('tenure_comparison', pd.DataFrame()) # Key for tenure data
    if tenure_df.empty or 'tenure' not in tenure_df.columns:
        st.warning("Data for 'Tenure Distribution' (tenure_comparison.csv with 'tenure' column) not available.")
        return None
    if not pd.api.types.is_numeric_dtype(tenure_df['tenure']):
        try: tenure_df['tenure'] = pd.to_numeric(tenure_df['tenure'])
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
    
    expected_cols = ['salary_range', 'employee_count']
    if not all(col in salary_dist_df.columns for col in expected_cols):
        if len(salary_dist_df.columns) >= 2:
            st.info("Attempting to use first two columns for salary distribution as 'salary_range' and 'employee_count'.")
            salary_dist_df.columns = ['salary_range', 'employee_count'] + list(salary_dist_df.columns[2:])
        else:
            st.error(f"Salary distribution data needs at least two columns. Expected: {', '.join(expected_cols)}.")
            return None

    if not pd.api.types.is_numeric_dtype(salary_dist_df['employee_count']):
        try: salary_dist_df['employee_count'] = pd.to_numeric(salary_dist_df['employee_count'])
        except ValueError:
            st.error("'employee_count' column in salary_distribution.csv must be numeric.")
            return None
            
    salary_dist_df_cleaned = salary_dist_df.dropna(subset=['employee_count', 'salary_range'])
    if salary_dist_df_cleaned.empty:
        st.warning("No valid data for salary distribution after cleaning.")
        return None
        
    # Sort the data by salary range for better visualization
    salary_dist_df_cleaned = salary_dist_df_cleaned.sort_values('employee_count', ascending=False)
    
    
    fig = px.bar(
        salary_dist_df_cleaned, 
        x='salary_range', 
        y='employee_count',
        title="Salary Range Distribution",
        color='salary_range',
        color_discrete_sequence=COLORS['pie_colors'],
        text='employee_count'
    )
    
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        paper_bgcolor=COLORS['graph_bg'], 
        plot_bgcolor=COLORS['graph_bg'], 
        font_color=COLORS['text'],
        xaxis_title="Salary Range",
        yaxis_title="Number of Employees",
        showlegend=False,
        xaxis={'categoryorder': 'total descending'}  # Sort bars by value
    )
    
    # Rotate x-axis labels if needed
    if len(salary_dist_df_cleaned) > 5:
        fig.update_layout(xaxis_tickangle=-45)
    
    return fig

def plot_location_report(dfs: dict):
    loc_df = dfs.get('location_employee_report', pd.DataFrame())
    if loc_df.empty:
        st.warning("Data for 'Location Report' (location_employee_report.csv) not available.")
        return None
    required_cols = ['city', 'average_salary', 'employee_count']
    if not all(col in loc_df.columns for col in required_cols):
        st.error(f"Missing required columns in location_employee_report.csv. Need at least: {', '.join(required_cols)}")
        return None
    for col in ['average_salary', 'employee_count']:
        if not pd.api.types.is_numeric_dtype(loc_df[col]):
            try: loc_df[col] = pd.to_numeric(loc_df[col])
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
        hover_name='city'
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
        try: growth_df['growth_%'] = pd.to_numeric(growth_df['growth_%'])
        except ValueError:
            st.error("'growth_%' column in salary_growth.csv must be numeric.")
            return None

    growth_df_cleaned = growth_df.dropna(subset=['growth_%'])
    if growth_df_cleaned.empty:
        st.warning("No valid salary growth data after cleaning.")
        return None
        
    bins = [-float('inf'), -50.0001, -0.0001, 0.0001, 50.0001, float('inf')]
    labels = ['Decrease >50%', 'Decrease 0-50%', 'No Change', 'Increase 0-50%', 'Increase >50%']
    growth_df_cleaned['growth_bucket'] = pd.cut(growth_df_cleaned['growth_%'], bins=bins, labels=labels, include_lowest=True, right=True)
    
    growth_dist = growth_df_cleaned['growth_bucket'].value_counts().reindex(labels).fillna(0).reset_index()
    growth_dist.columns = ['growth_range', 'count']

    color_map = {
        'Decrease >50%': COLORS['navy'], 'Decrease 0-50%': COLORS['light_navy'],
        'No Change': COLORS['light_purple'],
        'Increase 0-50%': COLORS['purple'], 'Increase >50%': COLORS['indigo']
    }

    fig = px.bar(
        growth_dist, x='growth_range', y='count',
        title="Distribution of Salary Growth Percentage",
        text='count', color='growth_range', color_discrete_map=color_map,
        labels={'growth_range': 'Salary Growth Range (%)', 'count': 'Number of Employees'}
    )
    fig.update_traces(textposition='outside')
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
    required_cols = ['name', 'salary']
    if not all(col in top_df.columns for col in required_cols):
        st.error(f"Missing required columns in top_salaries.csv. Need: {', '.join(required_cols)}")
        return None
    if not pd.api.types.is_numeric_dtype(top_df['salary']):
        try: top_df['salary'] = pd.to_numeric(top_df['salary'])
        except ValueError:
            st.error("'salary' column in top_salaries.csv must be numeric.")
            return None
            
    top_df_cleaned = top_df.dropna(subset=['name', 'salary'])
    if top_df_cleaned.empty:
        st.warning("No valid data for top salaries after cleaning.")
        return None
        
    top_df_sorted = top_df_cleaned.sort_values('salary', ascending=False).head(15)

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
        xaxis_tickangle=-45
    )
    return fig


def main():
    st.set_page_config(layout="wide", page_title="HR Workforce Dynamics Dashboard")

    st.markdown(f"""
    <style>
    /* Main app background */
    .main .block-container {{
        background-color: {COLORS['background']};
        padding-top: 2rem; padding-bottom: 3rem;
        padding-left: 2rem; padding-right: 2rem;
    }}
    /* Sidebar styling */
    [data-testid="stSidebar"] {{ /* More robust selector for sidebar */
        background-color: {COLORS['sidebar']};
    }}
    /* Text styling */
    h1 {{ color: {COLORS['title_color']}; }}
    h2, h3 {{ color: {COLORS['navy']}; }} /* Subheader colors */
    p, .stMarkdown, div[data-testid="stText"], li {{
        color: {COLORS['text']};
    }}
    /* Button styling */
    .stButton>button {{
        background-color: {COLORS['button_bg']}; color: {COLORS['button_text']};
        border-radius: 5px; border: none;
    }}
    .stButton>button:hover {{
        background-color: {COLORS['purple']}; opacity: 0.8;
    }}
    /* Card styling for Home page */
    .card {{
        background-color: {COLORS['card_bg']}; padding: 20px;
        border-radius: 10px; margin: 10px 0; text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border: 1px solid {COLORS['light_purple']}; height: 150px;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
    }}
    .card h3 {{ /* Metric value */
        margin: 0 0 5px 0; font-size: 26px; /* Slightly adjusted font size */
        color: {COLORS['purple']}; font-weight: bold;
    }}
    .card p {{ /* Metric label */
        margin: 0; font-size: 15px; color: {COLORS['secondary_text']};
    }}
    /* GIF container */
    
      .gif-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("HR Dashboard Navigation")
    page_options = ["Home", "Demographics", "Salary Analysis", "Hiring Trends", "Turnover Analysis",
                    "Tenure Distribution", "Salary Distribution", "Location Report",
                    "Salary Growth", "Top Salaries"]
    page = st.sidebar.radio("Select Visualization:", page_options)

    # Load and clean data
    if not os.path.exists(DATA_DIR) or not os.path.isdir(DATA_DIR):
        st.error(f"Error: Data directory '{DATA_DIR}' not found. Please create it and add your CSV files, or update the DATA_DIR path in the script.")
        st.info("The dashboard requires CSV files in this directory to function.")
        return # Stop execution if data directory is invalid

    raw_dfs = load_csv_files(DATA_DIR)
    if not raw_dfs:
        st.error(f"No CSV files were found or loaded from the directory: '{DATA_DIR}'.")
        st.info("Please ensure your CSV files are present in the specified directory.")
        return

    dfs = {}
    date_cols_to_clean = ['hire_date', 'start_date', 'end_date', 'date_of_birth', 'exit_date', 'last_promotion_date']
    for name, df_raw in raw_dfs.items():
        dfs[name] = clean_dataframe(df_raw, date_cols=date_cols_to_clean)

    st.markdown(f"<h1 style='text-align: center; color: {COLORS['title_color']}; margin-bottom: 1rem;'>{page} - HR Workforce Dynamics</h1>", unsafe_allow_html=True)
    
    if page != "Home": # Add a thematic break for non-home pages for visual separation
        st.markdown("---")

    if page == "Home":
        if os.path.exists(GIF_PATH):
            st.markdown('<div class="gif-container",use_column_width="auto">', unsafe_allow_html=True)
            # Increase the width here for a wider GIF
            st.image(GIF_PATH, width=650) # Example: Changed from 400 to 650
            st.markdown('</div>', unsafe_allow_html=True)
            
        else:
            st.sidebar.warning(f"HR GIF not found at {GIF_PATH}.")

        st.markdown("### Key Workforce Metrics")

        all_employees_df = dfs.get('all_employees', pd.DataFrame())
        job_salary_stats_df = dfs.get('job_salary_statistics', pd.DataFrame()) # Assumes a file with this name and max_salary col
        dept_salary_analysis_df = dfs.get('department_salary_analysis', pd.DataFrame())
        job_turnover_analysis_df = dfs.get('job_turnover_analysis', pd.DataFrame())
        tenure_df = dfs.get('tenure_comparison', pd.DataFrame()) # Or 'all_employees' if tenure is calculated from hire_date
        loc_report_df = dfs.get('location_employee_report', pd.DataFrame())

        total_employees = len(all_employees_df) if not all_employees_df.empty else "N/A"
        
        max_salary_val = "N/A"
        if not job_salary_stats_df.empty and 'max_salary' in job_salary_stats_df.columns:
            max_val = job_salary_stats_df['max_salary'].max()
            max_salary_val = f"${max_val:,.0f}" if pd.notnull(max_val) else "N/A"
        elif not all_employees_df.empty and 'salary' in all_employees_df.columns: # Fallback to all_employees salary
             max_val = all_employees_df['salary'].max()
             max_salary_val = f"${max_val:,.0f}" if pd.notnull(max_val) else "N/A"


        top_dept = "N/A"
        if not dept_salary_analysis_df.empty and 'department' in dept_salary_analysis_df.columns and 'employee_count' in dept_salary_analysis_df.columns:
            top_dept_series = dept_salary_analysis_df.sort_values('employee_count', ascending=False)
            if not top_dept_series.empty: top_dept = top_dept_series.iloc[0]['department']
        elif not all_employees_df.empty and 'department' in all_employees_df.columns: # Fallback
            top_dept = all_employees_df['department'].mode()[0] if not all_employees_df['department'].mode().empty else "N/A"


        turnover_high_role = "N/A"
        if not job_turnover_analysis_df.empty and 'job_title' in job_turnover_analysis_df.columns and 'turnover_rate_(%)' in job_turnover_analysis_df.columns:
            turnover_series = job_turnover_analysis_df.sort_values('turnover_rate_(%)', ascending=False)
            if not turnover_series.empty: turnover_high_role = turnover_series.iloc[0]['job_title']

        avg_tenure_val = "N/A"
        if not tenure_df.empty and 'tenure' in tenure_df.columns:
            mean_tenure = tenure_df['tenure'].mean()
            avg_tenure_val = f"{mean_tenure:.1f} Yrs" if pd.notnull(mean_tenure) else "N/A"
        elif not all_employees_df.empty and 'hire_date' in all_employees_df.columns: # Fallback: Calculate tenure if 'hire_date' exists
            if pd.api.types.is_datetime64_any_dtype(all_employees_df['hire_date']):
                current_date = pd.to_datetime("today") # Using current date for tenure calculation
                all_employees_df['calculated_tenure'] = (current_date - all_employees_df['hire_date']).dt.days / 365.25
                mean_tenure = all_employees_df['calculated_tenure'].mean()
                avg_tenure_val = f"{mean_tenure:.1f} Yrs" if pd.notnull(mean_tenure) else "N/A"


        top_location = "N/A"
        if not loc_report_df.empty and 'employee_count' in loc_report_df.columns:
            loc_col_options = ['city', 'region', 'location_name'] # Check for common location column names
            loc_col_to_use = next((col for col in loc_col_options if col in loc_report_df.columns), None)
            if loc_col_to_use:
                top_loc_series = loc_report_df.sort_values('employee_count', ascending=False)
                if not top_loc_series.empty: top_location = top_loc_series.iloc[0][loc_col_to_use]
        elif not all_employees_df.empty : # Fallback
             loc_col_options = ['city', 'region', 'location']
             loc_col_to_use = next((col for col in loc_col_options if col in all_employees_df.columns), None)
             if loc_col_to_use:
                top_location = all_employees_df[loc_col_to_use].mode()[0] if not all_employees_df[loc_col_to_use].mode().empty else "N/A"


        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="card"><h3>{total_employees}</h3><p>Total Employees</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{top_dept}</h3><p>Largest Department</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{avg_tenure_val}</h3><p>Average Tenure</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="card"><h3>{max_salary_val}</h3><p>Max Documented Salary</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{turnover_high_role}</h3><p>Highest Turnover Role</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{top_location}</h3><p>Top Employee Location</p></div>', unsafe_allow_html=True)

    elif page == "Demographics":
        st.subheader("Department Salary Metrics")
        st.markdown("Compare average, minimum, and maximum salaries across different departments.")
        fig = plot_employee_demographics(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the demographics chart.")

    elif page == "Salary Analysis":
        st.subheader("Experience vs. Salary Analysis")
        st.markdown("Explore the correlation between average years of experience and average salary, with a trendline indicating the general relationship.")
        fig = plot_salary_analysis(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the salary analysis chart.")

    elif page == "Hiring Trends":
        st.subheader("Annual Hiring Trends")
        st.markdown("Visualize the number of new hires per year to understand recruitment patterns over time.")
        fig = plot_hiring_trends(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the hiring trends chart.")

    elif page == "Turnover Analysis":
        st.subheader("Job Title Turnover Rates")
        st.markdown("Identify which job titles experience the highest and lowest employee turnover rates.")
        fig = plot_turnover_analysis(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the turnover analysis chart.")

    elif page == "Tenure Distribution":
        st.subheader("Employee Tenure Distribution")
        st.markdown("See the distribution of employee tenure in years, showing how long employees tend to stay with the company.")
        fig = plot_tenure_distribution(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the tenure distribution chart.")

    elif page == "Salary Distribution":
        st.subheader("Salary Range Distribution")
        st.markdown("Understand the proportion of employees falling into different salary ranges.")
        fig = plot_salary_distribution(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the salary distribution chart.")

    elif page == "Location Report":
        st.subheader("Employee Distribution and Salary by Location")
        st.markdown("Visualize employee counts and average salaries across various company locations or cities.")
        fig = plot_location_report(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the location report chart.")

    elif page == "Salary Growth":
        st.subheader("Salary Growth Percentage Distribution")
        st.markdown("Analyze the distribution of salary growth percentages experienced by employees (e.g., comparing first vs. current salary).")
        fig = plot_salary_growth(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the salary growth chart.")

    elif page == "Top Salaries":
        st.subheader("Top Employee Salaries")
        st.markdown("Display a list of the top-earning employees in the organization.")
        fig = plot_top_salaries(dfs)
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data available to display the top salaries chart.")

    st.sidebar.markdown("---")
    st.sidebar.info(f"Last data refresh: {pd.Timestamp('today').strftime('%Y-%m-%d %H:%M:%S')}") # Using pd.Timestamp for current time

if __name__ == "__main__":
    main()