import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime

# --- Configuration ---
DATA_DIR = "HR_ALL"  # Adjust this to your HR_DIR path
DATE_FORMAT = "%d-%b-%y"  # Matches '17-JUN-03' from PL/SQL
GIF_PATH = "emp.gif"  # Adjust this to the actual path of your GIF

# --- Color Palette (Light Blue and Navy Theme) ---
# --- Color Palette (Navy, Purple, Indigo, Magenta Theme) ---
COLORS = {
    'background': '#F5F6F5',         # Light grayish background for dashboard (neutral to complement vibrant colors)
    'sidebar': '#D1C4E9',            # Light purple for sidebar (derived from Purple #6F42C1)
    'text': '#343A40',               # Navy for primary text (high contrast)
    'secondary_text': '#9C27B0',     # Lighter magenta for secondary text
    'navy': '#343A40',               # Primary navy for emphasis
    'light_navy': '#5C6BC0',         # Lighter navy for softer elements
    'purple': '#6F42C1',             # Primary purple for key metrics
    'light_purple': '#B39DDB',       # Lighter purple for secondary elements
    'indigo': '#4B0082',             # Primary indigo for high values
    'light_indigo': '#7E57C2',       # Lighter indigo for mid-range
    'magenta': '#FF00FF',            # Primary magenta for highlights
    'soft_magenta': '#F06292',       # Softer magenta for neutral elements
    'card_bg': '#EDE7F6',            # Very light purple for cards
    'graph_bg': '#FAF9FE',           # Near-white with purple tint for graph backgrounds
    # Color sequences for graphs
    'discrete_sequence': ['#343A40', '#6F42C1', '#4B0082', '#FF00FF', '#5C6BC0', '#B39DDB', '#7E57C2', '#F06292'],
    'continuous_scale': ['#B39DDB', '#6F42C1', '#4B0082'],  # Purple to Indigo for gradients
    'bar_colors': ['#6F42C1', '#7E57C2', '#343A40'],        # Purple, Light Indigo, Navy for bar graphs
    'pie_colors': ['#6F42C1', '#343A40', '#FF00FF', '#5C6BC0'],  # Purple, Navy, Magenta, Light Navy
}

# --- Data Loading Functions ---
def load_csv_files(directory):
    dataframes = {}
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            try:
                df = pd.read_csv(filepath)
                df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
                dataframes[filename[:-4]] = df
            except Exception as e:
                st.warning(f"Error loading {filename}: {e}")
    return dataframes

# --- Data Cleaning Functions ---
def clean_dataframe(df, date_cols=None):
    df.replace(['NULL', ''], pd.NA, inplace=True)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip().str.replace('"', '', regex=False)
    if date_cols:
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format=DATE_FORMAT, errors='coerce')
    for col in df.columns:
        if col in ['employee_count', 'salary', 'avg_salary', 'min_salary', 'max_salary', 'median_salary', 'tenure', 'growth_%', 'turnover_rate_(%)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# --- Visualization Functions ---
# --- Visualization Functions ---
def plot_employee_demographics(dfs):
    dept_salary_df = dfs.get('department_salary_analysis', pd.DataFrame())
    if dept_salary_df.empty:
        st.error("Missing 'department_salary_analysis.csv'.")
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dept_salary_df['department'], y=dept_salary_df['avg_salary'], name='Avg Salary', marker_color=COLORS['purple'], text=dept_salary_df['avg_salary'].round(0), textposition='auto'))
    fig.add_trace(go.Bar(x=dept_salary_df['department'], y=dept_salary_df['min_salary'], name='Min Salary', marker_color=COLORS['light_indigo'], text=dept_salary_df['min_salary'], textposition='auto'))
    fig.add_trace(go.Bar(x=dept_salary_df['department'], y=dept_salary_df['max_salary'], name='Max Salary', marker_color=COLORS['navy'], text=dept_salary_df['max_salary'], textposition='auto'))
    fig.update_layout(title="Department Salary Comparison", barmode='group', paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_salary_analysis(dfs):
    exp_df = dfs.get('job_experience_salary', pd.DataFrame())
    if exp_df.empty:
        st.error("Missing 'job_experience_salary.csv'.")
        return None
    fig = px.scatter(exp_df, x='avg_experience_(years)', y='avg_salary', text='job_title', trendline='ols', 
                     color='avg_salary', color_continuous_scale=COLORS['continuous_scale'], title="Experience vs. Salary")
    fig.update_traces(textposition='top center')
    fig.update_layout(paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_hiring_trends(dfs):
    emp_df = dfs.get('all_employees', pd.DataFrame())
    if emp_df.empty or 'hire_date' not in emp_df.columns:
        st.error("Missing 'all_employees.csv' or 'hire_date' column.")
        return None
    emp_df['hire_year'] = emp_df['hire_date'].dt.year
    hire_trends = emp_df['hire_year'].value_counts().sort_index().reset_index()
    hire_trends.columns = ['year', 'hires']
    fig = px.line(hire_trends, x='year', y='hires', title="Hiring Trends Over Time", markers=True, text=hire_trends['hires'],
                  line_shape='linear', color_discrete_sequence=[COLORS['purple']])
    fig.update_traces(textposition='top center')
    fig.update_layout(xaxis_title="Year", yaxis_title="Number of Hires", paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_turnover_analysis(dfs):
    turnover_df = dfs.get('job_turnover_analysis', pd.DataFrame())
    if turnover_df.empty:
        st.error("Missing 'job_turnover_analysis.csv'.")
        return None
    turnover_df = turnover_df.sort_values('turnover_rate_(%)', ascending=True)
    fig = px.bar(turnover_df, y='job_title', x='turnover_rate_(%)', title="Turnover Rate by Job", orientation='h',
                 text=turnover_df['turnover_rate_(%)'].round(1), color='turnover_rate_(%)', color_continuous_scale=COLORS['continuous_scale'])
    fig.update_traces(textposition='auto')
    fig.update_layout(xaxis_title="Turnover Rate (%)", yaxis_title="Job Title", paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_tenure_distribution(dfs):
    tenure_df = dfs.get('tenure_comparison', pd.DataFrame())
    if tenure_df.empty:
        st.error("Missing 'tenure_comparison.csv'.")
        return None
    fig = px.histogram(tenure_df, x='tenure', title="Tenure Distribution", nbins=20, histnorm='percent', 
                       text_auto='.1f', color_discrete_sequence=[COLORS['light_purple']])
    fig.update_layout(xaxis_title="Tenure (Years)", yaxis_title="Percentage of Employees (%)", 
                      paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_salary_distribution(dfs):
    salary_dist_df = dfs.get('salary_distribution', pd.DataFrame())
    if salary_dist_df.empty:
        st.error("Missing 'salary_distribution.csv'.")
        return None
    salary_dist_df.columns = ['salary_range', 'employee_count']
    salary_dist_df['employee_count'] = pd.to_numeric(salary_dist_df['employee_count'], errors='coerce')
    fig = px.pie(salary_dist_df.dropna(subset=['employee_count']), 
                 names='salary_range', 
                 values='employee_count', 
                 hole=0.3, 
                 title="Salary Distribution",
                 color_discrete_sequence=COLORS['pie_colors'])
    fig.update_traces(textinfo='percent+label', textposition='inside')
    fig.update_layout(paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_location_report(dfs):
    loc_df = dfs.get('location_employee_report', pd.DataFrame())
    if loc_df.empty:
        st.error("Missing 'location_employee_report.csv'.")
        return None
    fig = px.scatter(loc_df, x='city', y='average_salary', size='employee_count', color='average_salary', 
                     color_continuous_scale=COLORS['continuous_scale'], title="Employee Distribution by Location",
                     text=loc_df['department'], size_max=60)
    fig.update_traces(textposition='top center')
    fig.update_layout(paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

def plot_salary_growth(dfs):
    growth_df = dfs.get('salary_growth', pd.DataFrame())
    if growth_df.empty:
        st.error("Missing 'salary_growth.csv'.")
        return None
    bins = [-float('inf'), -50, 0, 50, float('inf')]
    labels = ['<-50%', '-50% to 0%', '0% to 50%', '>50%']
    growth_df['growth_bucket'] = pd.cut(growth_df['growth_%'], bins=bins, labels=labels, include_lowest=True)
    growth_dist = growth_df['growth_bucket'].value_counts().reindex(labels).fillna(0).reset_index()
    growth_dist.columns = ['growth_range', 'count']
    colors = [COLORS['navy'] if '<' in r else COLORS['light_purple'] if '>' in r else COLORS['indigo'] for r in growth_dist['growth_range']]
    fig = px.bar(growth_dist, x='growth_range', y='count', title="Salary Growth Distribution",
                 text=growth_dist['count'], color=growth_dist['growth_range'], color_discrete_sequence=colors)
    fig.update_traces(textposition='auto')
    fig.update_layout(xaxis_title="Growth Range (%)", yaxis_title="Number of Employees", 
                      paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200, showlegend=False)
    return fig

def plot_top_salaries(dfs):
    top_df = dfs.get('top_salaries', pd.DataFrame())
    if top_df.empty:
        st.error("Missing 'top_salaries.csv'.")
        return None
    top_df = top_df.sort_values('salary', ascending=False)
    fig = px.bar(top_df, x='name', y='salary', title="Top Salaries", text=top_df['salary'], 
                 color='salary', color_continuous_scale=COLORS['continuous_scale'])
    fig.update_traces(textposition='auto')
    fig.update_layout(xaxis_title="Employee", yaxis_title="Salary", paper_bgcolor=COLORS['graph_bg'], plot_bgcolor=COLORS['graph_bg'], font_color=COLORS['text'], width=1200)
    return fig

# --- Main Streamlit App ---
def main():
    st.markdown("""
    <style>
    .main {
        background-color: #E6F0FA;
        color: #1E3A8A;
    }
    .sidebar .sidebar-content {
        background-color: #B3CDE0;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    p {
        color: #60A5FA;
    }
    .stButton>button {
        background-color: #3B82F6;
        color: #FFFFFF;
    }
    .card {
        background-color: #DCE7F5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .card h3 {
        margin: 0;
        font-size: 24px;
        color: #1E3A8A;
    }
    .card p {
        margin: 5px 0 0;
        font-size: 16px;
        color: #60A5FA;
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("HR Dashboard Navigation")
    page = st.sidebar.radio("Select Visualization", ["Home", "Demographics", "Salary", "Hiring", "Turnover", "Tenure", "Salary Distribution", "Location", "Salary Growth", "Top Salaries"])

    dfs = load_csv_files(DATA_DIR)
    if not dfs:
        st.error("No CSV files found in the directory.")
        return
    
    date_cols = ['hire_date', 'start_date', 'end_date']
    for name, df in dfs.items():
        dfs[name] = clean_dataframe(df, date_cols=date_cols)

    dark_navy_color = "#453299"  # Hex code for dark navy

    st.markdown(f"<h1 style='color: {dark_navy_color};'>HR Workforce Dynamics Dashboard</h1>", unsafe_allow_html=True)
    if page == "Home":
        # Display GIF centered above the cards
        if os.path.exists(GIF_PATH):
            st.markdown('<div class="gif-container">', unsafe_allow_html=True)
            st.image(GIF_PATH, width=550)  # Adjust width as needed
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning(f"GIF not found at {GIF_PATH}. Please check the file path.")

    if page == "Home":
        st.markdown("### Workforce Insights")
        total_employees = len(dfs.get('all_employees', pd.DataFrame()))
        max_salary = dfs.get('job_salary_statistics', pd.DataFrame())['max_salary'].max()
        top_dept = dfs.get('department_salary_analysis', pd.DataFrame()).sort_values('employee_count', ascending=False).iloc[0]['department']
        turnover_high = dfs.get('job_turnover_analysis', pd.DataFrame()).sort_values('turnover_rate_(%)', ascending=False).iloc[0]['job_title']
        avg_tenure = dfs.get('tenure_comparison', pd.DataFrame())['tenure'].mean()
        top_location = dfs.get('location_employee_report', pd.DataFrame()).sort_values('employee_count', ascending=False).iloc[0]['region']

        # Two rows of two columns for four cards
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="card"><h3>{total_employees}</h3><p>Total Employees</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{top_dept}</h3><p>Largest Department</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="card"><h3>${max_salary:,.0f}</h3><p>Highest Salary</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card"><h3>{top_location}</h3><p>Top Region</p></div>', unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f'<div class="card"><h3>{turnover_high}</h3><p>Highest Turnover Role</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="card"><h3>{avg_tenure:.1f} Years</h3><p>Average Tenure</p></div>', unsafe_allow_html=True)

    elif page == "Demographics":
        st.subheader("Department Salary Comparison")
        st.markdown("Compare salary metrics across departments.")
        fig1 = plot_employee_demographics(dfs)
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)

    elif page == "Salary":
        st.subheader("Experience vs. Salary")
        st.markdown("Does experience correlate with higher pay?")
        fig2 = plot_salary_analysis(dfs)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)

    elif page == "Hiring":
        st.subheader("Hiring Trends")
        st.markdown("When did we hire our workforce?")
        fig3 = plot_hiring_trends(dfs)
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)

    elif page == "Turnover":
        st.subheader("Turnover Rate by Job")
        st.markdown("Which roles have the highest turnover?")
        fig4 = plot_turnover_analysis(dfs)
        if fig4:
            st.plotly_chart(fig4, use_container_width=True)

    elif page == "Tenure":
        st.subheader("Tenure Distribution")
        st.markdown("How long do employees stay with us?")
        fig5 = plot_tenure_distribution(dfs)
        if fig5:
            st.plotly_chart(fig5, use_container_width=True)

    elif page == "Salary Distribution":
        st.subheader("Salary Distribution")
        st.markdown("What’s the breakdown of salary ranges?")
        fig6 = plot_salary_distribution(dfs)
        if fig6:
            st.plotly_chart(fig6, use_container_width=True)

    elif page == "Location":
        st.subheader("Employee Distribution by Location")
        st.markdown("Where are our employees based?")
        fig7 = plot_location_report(dfs)
        if fig7:
            st.plotly_chart(fig7, use_container_width=True)

    elif page == "Salary Growth":
        st.subheader("Salary Growth Distribution")
        st.markdown("How is salary growth distributed across employees? (First vs. Current)")
        fig8 = plot_salary_growth(dfs)
        if fig8:
            st.plotly_chart(fig8, use_container_width=True)

    elif page == "Top Salaries":
        st.subheader("Top Salaries")
        st.markdown("Who are our top earners?")
        fig9 = plot_top_salaries(dfs)
        if fig9:
            st.plotly_chart(fig9, use_container_width=True)
