import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import sqlite3
import os
import time

# Set page config
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .insight-box {
        background-color: #1e1e1e;
        color: white;
        padding: 12px;
        margin: 8px 0;
        border-radius: 10px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.5);
        font-size: 15px;
    }
    .data-entry-form {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Database functions
@st.cache_resource
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('student_performance.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Month TEXT,
            Date TEXT,
            Subject TEXT,
            Topic TEXT,
            Rank INTEGER,
            Percentage REAL,
            Marks REAL,
            Average_Marks REAL,
            Highest_Mark REAL,
            Exam_Type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

# def insert_data_to_db(conn, df):
#     """Insert DataFrame to database"""
#     try:
#         df_copy = df.copy()
#         # Add created_at timestamp if not present
#         if 'created_at' not in df_copy.columns:
#             df_copy['created_at'] = datetime.now()
        
#         df_copy.to_sql('student_data', conn, if_exists='append', index=False)
#         return True, "Data successfully added to database!"
#     except Exception as e:
#         return False, f"Error inserting data: {str(e)}"


def insert_data_to_db(conn, df):
    """Insert DataFrame to database with full row duplicate check"""
    try:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            # Check if exact same row already exists (excluding id & created_at)
            cursor.execute("""
                SELECT COUNT(*) FROM student_data
                WHERE Name=? AND Month=? AND Date=? AND Subject=? AND Topic=? 
                AND Rank=? AND Percentage=? AND Marks=? AND Average_Marks=? 
                AND Highest_Mark=? AND Exam_Type=?
            """, (
                row['Name'], row.get('Month', ''),
                row['Date'], row['Subject'], row.get('Topic', ''),
                row.get('Rank', 0), row.get('Percentage', 0.0),
                row['Marks'], row.get('Average_Marks', 0.0),
                row['Highest_Mark'], row['Exam_Type']
            ))
            exists = cursor.fetchone()[0]

            if exists > 0:
                return False, f"⚠️ Duplicate entry detected: This exact record already exists."

            # Insert new row
            cursor.execute("""
                INSERT INTO student_data
                (Name, Month, Date, Subject, Topic, Rank, Percentage, Marks, Average_Marks, Highest_Mark, Exam_Type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['Name'], row.get('Month', ''),
                row['Date'], row['Subject'], row.get('Topic', ''),
                row.get('Rank', 0), row.get('Percentage', 0.0),
                row['Marks'], row.get('Average_Marks', 0.0),
                row['Highest_Mark'], row['Exam_Type'],
                datetime.now()
            ))
        
        conn.commit()
        return True, "✅ Data successfully added!"
    except Exception as e:
        return False, f"Error inserting data: {str(e)}"



def load_data_from_db(conn):
    """Load all data from database"""
    try:
        df = pd.read_sql_query("SELECT * FROM student_data ORDER BY created_at DESC", conn)
        return df
    except Exception as e:
        st.error(f"Error loading data from database: {str(e)}")
        return load_sample_data()

def delete_student_data(conn, student_name):
    """Delete all data for a specific student"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_data WHERE Name = ?", (student_name,))
        conn.commit()
        return True, f"All data for {student_name} has been deleted."
    except Exception as e:
        return False, f"Error deleting data: {str(e)}"

def reset_entire_database(conn):
    """Delete all data from the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_data")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='student_data'")  # Reset auto-increment
        conn.commit()
        return True, "All data has been successfully deleted from the database."
    except Exception as e:
        return False, f"Error resetting database: {str(e)}"

def get_database_stats(conn):
    """Get database statistics"""
    try:
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM student_data")
        total_records = cursor.fetchone()[0]
        
        # Total students
        cursor.execute("SELECT COUNT(DISTINCT Name) FROM student_data")
        total_students = cursor.fetchone()[0]
        
        # Total subjects
        cursor.execute("SELECT COUNT(DISTINCT Subject) FROM student_data")
        total_subjects = cursor.fetchone()[0]
        
        # Latest entry date
        cursor.execute("SELECT MAX(created_at) FROM student_data")
        latest_entry = cursor.fetchone()[0]
        
        return {
            'total_records': total_records,
            'total_students': total_students,
            'total_subjects': total_subjects,
            'latest_entry': latest_entry
        }
    except Exception as e:
        return None

# Sample data function (kept for fallback)
@st.cache_data
def load_sample_data():
    data = {
        'Name': ['Asgar Hussain Sayyed'] * 5,
        'Month': ['August'] * 5,
        'Date': ['03/08/2025', '04/08/2025', '05/08/2025', '05/08/2025', '09/08/2025'],
        'Subject': ['PM', 'Math', 'Chemistry', 'Physics', 'Chemistry'],
        'Topic': ['Kinematics,Trigonometric Function', 'Quadratic Equation', 'Structure of autom', 'Kinematics', 'Organic Chemistry'],
        'Rank': [15, 0, 0, 51, 37],
        'Percentage': [27, 0, 0.00, 32, 71.25],
        'Marks': [27, 0, 0, 19, 57],
        'Average_Marks': [58.05, 19.9, 33.44, 29.67, 60.05],
        'Highest_Mark': [96, 40, 60, 51, 80],
        'Exam_Type': ['Weekly', 'DCT', 'DCT', 'DCT', 'DCT']
    }
    return pd.DataFrame(data)

def show_data_entry_form(conn):
    """Display data entry form"""
    st.markdown("### 📝 Add New Performance Data")
    
    with st.form("data_entry_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Student Name*", placeholder="Enter student name")
            month = st.selectbox("Month", 
                               ['January', 'February', 'March', 'April', 'May', 'June',
                                'July', 'August', 'September', 'October', 'November', 'December'])
            date = st.date_input("Exam Date", value=datetime.now())
        
        with col2:
            subject = st.selectbox("Subject", 
                                 ['Math', 'Physics', 'Chemistry', 'Biology', 'English', 'PM', 'Other'])
            if subject == 'Other':
                subject = st.text_input("Specify Subject")
            
            topic = st.text_input("Topic", placeholder="Enter topic/chapter")
            exam_type = st.selectbox("Exam Type", ['DCT', 'Weekly', 'Monthly', 'Term', 'Final'])
        
        with col3:
            marks = st.number_input("Marks Obtained*", min_value=0.0, step=0.1)
            highest_mark = st.number_input("Highest Mark in Class*", min_value=0.0, step=0.1)
            average_marks = st.number_input("Class Average", min_value=0.0, step=0.1)
            rank = st.number_input("Rank (0 if not available)", min_value=0, step=1)
        
        # Add percentage input option
        # st.markdown("---")
        # st.markdown("**📊 Percentage Calculation**")
        
        # col1, col2 = st.columns(2)
        # with col1:
        #     percentage_option = st.radio(
        #         "How would you like to handle percentage?",
        #         ["Auto-calculate from marks", "Enter percentage manually"],
        #         help="Auto-calculate uses (Marks ÷ Highest Mark) × 100"
        #     )

        st.markdown("**📊 Enter Percentage Manually**")
        percentage = st.number_input("Percentage*", min_value=0.0, max_value=100.0, step=0.1)

        
        # with col2:
        #     if percentage_option == "Enter percentage manually":
        #         percentage = st.number_input("Percentage*", min_value=0.0, max_value=100.0, step=0.1)
        #     else:
        #         percentage = None
        #         if marks > 0 and highest_mark > 0:
        #             calculated_percentage = (marks / highest_mark) * 100
        #             st.info(f"📊 Auto-calculated percentage: **{calculated_percentage:.2f}%**")
        #         else:
        #             st.warning("Enter marks and highest mark to see calculated percentage")
        
        submitted = st.form_submit_button("✅ Add Data", type="primary")
        
        if submitted:
            if name and subject and marks and highest_mark:
                # Calculate or use provided percentage
                # if percentage_option == "Auto-calculate from marks":
                #     final_percentage = (marks / highest_mark) * 100 if highest_mark > 0 else 0
                # else:
                #     final_percentage = percentage if percentage is not None else 0
                final_percentage = percentage if percentage is not None else 0

                
                # # Validation
                # if percentage_option == "Enter percentage manually" and percentage is None:
                #     st.error("Please enter the percentage value.")
                #     return
                
                # Create new data entry
                new_data = {
                    'Name': [name],
                    'Month': [month],
                    'Date': [date.strftime('%d/%m/%Y')],
                    'Subject': [subject],
                    'Topic': [topic],
                    'Rank': [rank],
                    'Percentage': [final_percentage],
                    'Marks': [marks],
                    'Average_Marks': [average_marks],
                    'Highest_Mark': [highest_mark],
                    'Exam_Type': [exam_type]
                }
                
                new_df = pd.DataFrame(new_data)
                success, message = insert_data_to_db(conn, new_df)
                
                if success:
                    st.success(f"✅ {message}")
                    st.info(f"📊 Added: {name} | {subject} | {final_percentage:.1f}% | {exam_type}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please fill in all required fields (marked with *)")

def bulk_upload_csv(conn, uploaded_file):
    """Handle bulk CSV upload with improved error handling"""
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Check if file is empty
        content = uploaded_file.getvalue()
        if len(content) == 0:
            st.error("The uploaded file is empty. Please upload a valid CSV file.")
            return False
        
        # Reset file pointer again
        uploaded_file.seek(0)
        
        # Try different encodings and separators
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        separators = [',', ';', '\t']
        
        df = None
        for encoding in encodings:
            for separator in separators:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=separator)
                    
                    # Check if we got valid data
                    if len(df.columns) > 1 and len(df) > 0:
                        st.info(f"File successfully read with encoding: {encoding}, separator: '{separator}'")
                        break
                except:
                    continue
            if df is not None and len(df.columns) > 1:
                break
        
        if df is None or len(df.columns) <= 1:
            st.error("""
            Could not parse the CSV file. Please ensure:
            1. The file is a valid CSV format
            2. It contains data with proper headers
            3. Columns are separated by commas, semicolons, or tabs
            4. The file is not corrupted
            """)
            return False
        
        # Display detected structure
        st.info(f"Detected {len(df.columns)} columns and {len(df)} rows")
        st.write("**Detected columns:**", list(df.columns))
        
        # Clean column names (remove extra spaces)
        df.columns = df.columns.str.strip()
        
        # Validate required columns
        required_columns = ['Name', 'Subject', 'Marks', 'Highest_Mark']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"""
            Missing required columns: {', '.join(missing_columns)}
            
            **Available columns:** {', '.join(df.columns.tolist())}
            
            **Required columns:** {', '.join(required_columns)}
            """)
            return False
        
        # Remove empty rows
        df = df.dropna(subset=required_columns, how='all')
        
        if len(df) == 0:
            st.error("No valid data rows found after removing empty rows.")
            return False
        
        # Data type conversions and validation
        try:
            df['Marks'] = pd.to_numeric(df['Marks'], errors='coerce')
            df['Highest_Mark'] = pd.to_numeric(df['Highest_Mark'], errors='coerce')
            
            # Remove rows where Marks or Highest_Mark couldn't be converted
            invalid_rows = df[df['Marks'].isna() | df['Highest_Mark'].isna()]
            if len(invalid_rows) > 0:
                st.warning(f"Removed {len(invalid_rows)} rows with invalid Marks or Highest_Mark values")
                df = df.dropna(subset=['Marks', 'Highest_Mark'])
        except Exception as e:
            st.error(f"Error converting numeric data: {str(e)}")
            return False
        
        if len(df) == 0:
            st.error("No valid data rows remaining after data validation.")
            return False
        
        # Calculate percentage if not provided
        if 'Percentage' not in df.columns or df['Percentage'].isna().all():
            df['Percentage'] = (df['Marks'] / df['Highest_Mark']) * 100
        
        # Fill missing values with defaults
        if 'Month' not in df.columns or df['Month'].isna().all():
            df['Month'] = datetime.now().strftime('%B')
        
        if 'Date' not in df.columns or df['Date'].isna().all():
            df['Date'] = datetime.now().strftime('%d/%m/%Y')
        
        if 'Topic' not in df.columns:
            df['Topic'] = ''
        
        if 'Rank' not in df.columns:
            df['Rank'] = 0
        else:
            df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce').fillna(0)
        
        if 'Average_Marks' not in df.columns:
            df['Average_Marks'] = 0
        else:
            df['Average_Marks'] = pd.to_numeric(df['Average_Marks'], errors='coerce').fillna(0)
        
        if 'Exam_Type' not in df.columns or df['Exam_Type'].isna().all():
            df['Exam_Type'] = 'DCT'
        
        # Final validation
        df = df.fillna('')  # Fill any remaining NaN values with empty strings
        
        success, message = insert_data_to_db(conn, df)
        
        if success:
            st.success(f"{message} Successfully added {len(df)} records.")
            return True
        else:
            st.error(message)
            return False
            
    except Exception as e:
        st.error(f"Unexpected error processing CSV file: {str(e)}")
        st.error("Please check that your CSV file is properly formatted and try again.")
        return False

# [Keep all the existing chart functions unchanged]
def create_performance_overview(df):
    """Create performance overview metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_percentage = df['Percentage'].mean()
        st.metric(
            label="Overall Average %",
            value=f"{avg_percentage:.1f}%",
            delta=f"{avg_percentage - 50:.1f}% vs 50% benchmark"
        )
    
    with col2:
        total_exams = len(df)
        passed_exams = len(df[df['Percentage'] >= 35])
        st.metric(
            label="Pass Rate",
            value=f"{passed_exams}/{total_exams}",
            delta=f"{(passed_exams/total_exams)*100:.1f}% success rate"
        )
    
    with col3:
        best_subject = df.loc[df['Percentage'].idxmax(), 'Subject']
        best_score = df['Percentage'].max()
        st.metric(
            label="Best Performance",
            value=f"{best_subject}",
            delta=f"{best_score:.1f}%"
        )
    
    with col4:
        avg_rank = df[df['Rank'] > 0]['Rank'].mean()
        st.metric(
            label="Average Rank",
            value=f"{avg_rank:.0f}" if not pd.isna(avg_rank) else "N/A",
            delta="Lower is better"
        )

def create_subject_performance_chart(df):
    """Create subject-wise performance analysis"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Performance by Subject', 'Marks vs Average Comparison', 
                       'Performance vs Class Average', 'Exam Type Analysis'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": True}, {"secondary_y": False}]]
    )
    
    # Chart 1: Performance by Subject
    subject_perf = df.groupby('Subject')['Percentage'].mean().reset_index()
    fig.add_trace(
        go.Bar(x=subject_perf['Subject'], y=subject_perf['Percentage'], 
               name='Average %', marker_color='lightblue'),
        row=1, col=1
    )
    
    # Chart 2: Marks vs Average Comparison
    fig.add_trace(
        go.Scatter(x=df['Subject'], y=df['Marks'], mode='markers+lines',
                  name='Student Marks', marker=dict(size=10, color='red')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=df['Subject'], y=df['Average_Marks'], mode='markers+lines',
                  name='Class Average', marker=dict(size=8, color='blue')),
        row=1, col=2
    )
    
    # Chart 3: Performance vs Class Average (with rank on secondary y-axis)
    fig.add_trace(
        go.Bar(x=df['Date'], y=df['Percentage'], name='Student %', 
               marker_color='lightgreen'),
        row=2, col=1
    )

    # Add rank on secondary y-axis (only for non-zero ranks)
    rank_data = df[df['Rank'] > 0]
    if len(rank_data) > 0:
        fig.add_trace(
            go.Scatter(x=rank_data['Date'], y=rank_data['Rank'], 
                      mode='markers+lines', name='Rank', 
                      marker=dict(color='orange', size=8)),
            row=2, col=1, secondary_y=True
        )

        # Invert the secondary y-axis so that rank 1 is at the top
        fig.update_yaxes(
            title_text="Rank",
            autorange="reversed",
            secondary_y=True,
            row=2, col=1
        )
    
    # Chart 4: Exam Type Analysis
    exam_type_perf = df.groupby('Exam_Type')['Percentage'].mean().reset_index()
    fig.add_trace(
        go.Bar(x=exam_type_perf['Exam_Type'], y=exam_type_perf['Percentage'],
               name='Avg % by Exam Type', marker_color='purple'),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=True, title_text="Comprehensive Performance Analysis")
    fig.update_yaxes(title_text="Percentage", row=1, col=1)
    fig.update_yaxes(title_text="Marks", row=1, col=2)
    fig.update_yaxes(title_text="Percentage", row=2, col=1)
    fig.update_yaxes(title_text="Rank", secondary_y=True, row=2, col=1)
    fig.update_yaxes(title_text="Percentage", row=2, col=2)
    
    return fig

def create_trend_analysis(df, subject=None):
    """Create trend analysis over time, overall or subject-wise"""
    df['Date_parsed'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    df_sorted = df.sort_values('Date_parsed')

    if subject and subject != "Overall":
        df_sorted = df_sorted[df_sorted['Subject'] == subject]

    fig = go.Figure()

    # Performance trend
    fig.add_trace(go.Scatter(
        x=df_sorted['Date'],
        y=df_sorted['Marks'],
        mode='lines+markers',
        name='Performance',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))

    # Class average
    if subject and subject != "Overall":
        class_avg_line = df[df['Subject'] == subject]['Average_Marks'].mean()
    else:
        class_avg_line = df['Average_Marks'].mean()

    fig.add_hline(y=class_avg_line, line_dash="dash", line_color="yellow", 
                  annotation_text=f"Class Avg: {class_avg_line:.1f}")

    # Student average
    if subject and subject != "Overall":
        student_avg_line = df[df['Subject'] == subject]['Marks'].mean()
    else:
        student_avg_line = df['Marks'].mean()

    fig.add_hline(y=student_avg_line, line_dash="dash", line_color="red", 
                  annotation_text=f"Student Avg: {student_avg_line:.1f}")

    # Pass line
    if subject and subject != "Overall":
        subject_max = df[df['Subject'] == subject]['Highest_Mark'].mean()
    else:
        subject_max = df['Highest_Mark'].mean()
    
    pass_line = subject_max * 0.35  

    fig.add_hline(
        y=pass_line,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Pass Mark: {pass_line:.1f}"
    )
    
    fig.update_layout(
        title=f"Performance Trend Over Time ({subject if subject else 'Overall'})",
        xaxis_title="Date",
        yaxis_title="Marks",
        height=450
    )

    return fig

def generate_insights(df):
    """Generate analytical insights"""
    insights = []
    
    # Performance insights
    avg_perf = df['Percentage'].mean()
    if avg_perf >= 75:
        insights.append("🎉 **Excellent Overall Performance**: Above 75% average!")
    elif avg_perf >= 60:
        insights.append("👍 **Good Performance**: Solid academic standing with room for improvement")
    elif avg_perf >= 35:
        insights.append("⚠️ **Average Performance**: Meeting basic requirements but needs focus")
    else:
        insights.append("🚨 **Needs Improvement**: Below average performance requires immediate attention")
    
    # Subject-specific insights
    best_subject = df.loc[df['Percentage'].idxmax(), 'Subject']
    worst_subject = df.loc[df['Percentage'].idxmin(), 'Subject']
    insights.append(f"📈 **Strongest Subject**: {best_subject} ({df['Percentage'].max():.1f}%)")
    insights.append(f"📉 **Focus Area**: {worst_subject} ({df['Percentage'].min():.1f}%)")
    
    # Exam type analysis
    exam_type_avg = df.groupby('Exam_Type')['Percentage'].mean()
    if len(exam_type_avg) > 1:
        best_exam_type = exam_type_avg.idxmax()
        insights.append(f"📝 **Best Exam Format**: {best_exam_type} ({exam_type_avg.max():.1f}% avg)")
    
    # Consistency analysis
    std_dev = df['Percentage'].std()
    if std_dev < 15:
        insights.append("🎯 **Consistent Performance**: Low variation in scores")
    else:
        insights.append("📊 **Variable Performance**: High variation suggests inconsistent preparation")
    
    # Comparison with class
    above_avg_count = len(df[df['Marks'] > df['Average_Marks']])
    total_count = len(df)
    if above_avg_count > total_count/2:
        insights.append(f"🌟 **Above Class Average**: Outperforming class in {above_avg_count}/{total_count} exams")
    else:
        insights.append(f"📚 **Below Class Average**: Need to improve in {total_count-above_avg_count}/{total_count} exams")
    
    return insights

def main():
    # Initialize database
    conn = init_database()
    
    # Header
    st.markdown('<h1 class="main-header">📊 Student Performance Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation and data input
    st.sidebar.header("Navigation & Data Management")
    
    # Main navigation
    page = st.sidebar.selectbox(
        "Choose Page:",
        ["📊 Analytics Dashboard", "📝 Add New Data", "📁 Data Management"]
    )
    
    if page == "📝 Add New Data":
        st.markdown("## 📝 Data Entry")
        
        # Tabs for different input methods
        tab1, tab2 = st.tabs(["Manual Entry", "CSV Upload"])
        
        with tab1:
            show_data_entry_form(conn)
        
        with tab2:
            st.markdown("### 📁 Upload CSV File")
            
            # Create sample CSV template
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📋 CSV Template**")
                template_data = {
                    'Name': ['John Doe', 'Jane Smith'],
                    'Month': ['September', 'September'],
                    'Date': ['01/09/2025', '02/09/2025'],
                    'Subject': ['Math', 'Physics'],
                    'Topic': ['Algebra', 'Kinematics'],
                    'Rank': [15, 8],
                    'Marks': [85, 78],
                    'Average_Marks': [75, 72],
                    'Highest_Mark': [95, 90],
                    'Exam_Type': ['Weekly', 'DCT']
                }
                template_df = pd.DataFrame(template_data)
                st.dataframe(template_df, use_container_width=True)
                
                # Download template
                template_csv = template_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV Template",
                    data=template_csv,
                    file_name="student_data_template.csv",
                    mime="text/csv",
                    type="secondary"
                )
            
            with col2:
                st.markdown("**📝 Column Requirements:**")
                st.markdown("""
                **Required columns:**
                - `Name` - Student name
                - `Subject` - Subject name
                - `Marks` - Marks obtained
                - `Highest_Mark` - Maximum marks in class
                
                **Optional columns:**
                - `Month` - Exam month
                - `Date` - Exam date (DD/MM/YYYY format)
                - `Topic` - Topic/chapter name
                - `Rank` - Student rank (0 if not available)
                - `Average_Marks` - Class average marks
                - `Exam_Type` - Type of exam (DCT, Weekly, etc.)
                - `Percentage` - Will be calculated automatically if not provided
                
                **File format tips:**
                - Use comma (,) as separator
                - Ensure proper headers in first row
                - Save as .csv format
                - Use UTF-8 encoding if possible
                """)
            
            st.markdown("---")
            
            uploaded_file = st.file_uploader(
                "Choose a CSV file",
                type="csv",
                help="Upload a CSV file with student performance data"
            )
            
            if uploaded_file is not None:
                # Show file details
                st.info(f"**File:** {uploaded_file.name} | **Size:** {uploaded_file.size} bytes")
                
                # Preview option
                if st.checkbox("Preview data before upload"):
                    try:
                        uploaded_file.seek(0)
                        preview_df = pd.read_csv(uploaded_file, nrows=5)  # Show only first 5 rows
                        st.markdown("#### Preview (first 5 rows):")
                        st.dataframe(preview_df, use_container_width=True)
                        uploaded_file.seek(0)  # Reset file pointer
                    except Exception as e:
                        st.warning(f"Could not preview file: {str(e)}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📤 Upload to Database", type="primary"):
                        with st.spinner("Processing CSV file..."):
                            success = bulk_upload_csv(conn, uploaded_file)
                        if success:
                            st.success("✅ Data uploaded successfully!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                
                with col2:
                    if st.button("🔄 Reset", type="secondary"):
                        st.rerun()
    
    elif page == "📁 Data Management":
        st.markdown("## 📁 Data Management")
        
        # Load current data
        df_all = load_data_from_db(conn)
        
        # Get database statistics
        db_stats = get_database_stats(conn)
        
        if db_stats and db_stats['total_records'] == 0:
            st.info("No data found in database. Please add some data first.")
            st.markdown("### 🚀 Quick Start Options")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Load Sample Data", type="primary"):
                    sample_df = load_sample_data()
                    success, message = insert_data_to_db(conn, sample_df)
                    if success:
                        st.success("Sample data loaded successfully!")
                        st.rerun()
                    else:
                        st.error(message)
            with col2:
                st.markdown("Or go to **📝 Add New Data** to start entering your data.")
            return
        
        # Display current data stats
        if db_stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Records", db_stats['total_records'])
            with col2:
                st.metric("👥 Total Students", db_stats['total_students'])
            with col3:
                st.metric("📚 Subjects Covered", db_stats['total_subjects'])
            with col4:
                latest = db_stats['latest_entry']
                if latest:
                    latest_date = datetime.fromisoformat(latest).strftime("%d/%m/%Y")
                    st.metric("📅 Latest Entry", latest_date)
                else:
                    st.metric("📅 Latest Entry", "N/A")
        
        # Tabs for different management options
        tab1, tab2, tab3 = st.tabs(["📋 View Data", "🗑️ Delete Data", "🔄 Reset Database"])
        
        with tab1:
            st.markdown("### 📋 Current Data")
            if len(df_all) > 0:
                # Add search and filter options
                col1, col2 = st.columns(2)
                with col1:
                    search_student = st.selectbox("Filter by Student (Optional):", 
                                                ["All Students"] + df_all['Name'].unique().tolist())
                with col2:
                    search_subject = st.selectbox("Filter by Subject (Optional):",
                                                ["All Subjects"] + df_all['Subject'].unique().tolist())
                
                # Apply filters
                filtered_df = df_all.copy()
                if search_student != "All Students":
                    filtered_df = filtered_df[filtered_df['Name'] == search_student]
                if search_subject != "All Subjects":
                    filtered_df = filtered_df[filtered_df['Subject'] == search_subject]
                
                st.dataframe(filtered_df, use_container_width=True)
                st.info(f"Showing {len(filtered_df)} of {len(df_all)} records")
            else:
                st.info("No data available")
        
        # with tab2:
        #     st.markdown("### 🗑️ Delete Student Data")
        #     if len(df_all) > 0:
        #         students = df_all['Name'].unique()
                
        #         col1, col2 = st.columns([2, 1])
        #         with col1:
        #             student_to_delete = st.selectbox("Select student to delete all data:", students)
        #             student_records = len(df_all[df_all['Name'] == student_to_delete])
        #             st.warning(f"⚠️ This will delete {student_records} records for {student_to_delete}")
                
        #         with col2:
        #             st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        #             if st.button("🗑️ Delete Student Data", type="secondary"):
        #                 success, message = delete_student_data(conn, student_to_delete)
        #                 if success:
        #                     st.success(message)
        #                     time.sleep(1)
        #                     st.rerun()
        #                 else:
        #                     st.error(message)
        #     else:
        #         st.info("No students found to delete")
        with tab2:
            st.markdown("### 🗑️ Delete Student Data")
            if len(df_all) > 0:
                # Delete all records of a student (your existing code)
                students = df_all['Name'].unique()
                student_to_delete = st.selectbox("Select student to delete all data:", students)
                student_records = len(df_all[df_all['Name'] == student_to_delete])
                st.warning(f"⚠️ This will delete {student_records} records for {student_to_delete}")

                if st.button("🗑️ Delete All Records for Student", type="secondary"):
                    success, message = delete_student_data(conn, student_to_delete)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

                st.markdown("---")

                # ✅ Delete specific record option
                st.markdown("### 🗑️ Delete Specific Record")
                record_to_delete = st.selectbox(
                    "Select record to delete:",
                    df_all.apply(
                        lambda r: f"{r['id']} | {r['Name']} | {r['Month']} | {r['Date']} | {r['Subject']} | {r['Topic']} | "
                                  f"Rank: {r['Rank']} | %: {r['Percentage']} | Marks: {r['Marks']} | "
                                  f"Avg: {r['Average_Marks']} | High: {r['Highest_Mark']} | {r['Exam_Type']}",
                        axis=1
                    )
                )


                if st.button("🗑️ Delete This Record", type="primary"):
                    rec_id = int(record_to_delete.split(" | ")[0])
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM student_data WHERE id=?", (rec_id,))
                    conn.commit()
                    st.success("Record deleted successfully!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("No data available for deletion")

        
        with tab3:
            st.markdown("### 🔄 Reset Entire Database")
            st.error("⚠️ **DANGER ZONE** ⚠️")
            st.markdown("""
            **This action will:**
            - Delete ALL student data from the database
            - Remove ALL performance records
            - Reset the database to empty state
            - **This action CANNOT be undone!**
            """)
            
            if db_stats and db_stats['total_records'] > 0:
                st.warning(f"You are about to delete **{db_stats['total_records']} records** from **{db_stats['total_students']} students**")
                
                # Double confirmation
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    confirm1 = st.checkbox("I understand this will delete ALL data")
                with col2:
                    confirm2 = st.checkbox("I want to start completely fresh")
                with col3:
                    confirm3 = st.checkbox("I cannot undo this action")
                
                if confirm1 and confirm2 and confirm3:
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        if st.button("🚨 RESET DATABASE 🚨", type="primary"):
                            with st.spinner("Resetting database..."):
                                success, message = reset_entire_database(conn)
                            if success:
                                st.success("✅ Database has been completely reset!")
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.info("Please check all confirmation boxes above to enable database reset.")
            else:
                st.info("Database is already empty - nothing to reset.")
        
        # Export data section
        if len(df_all) > 0:
            st.markdown("---")
            st.markdown("### 📤 Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df_all.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Data as CSV",
                    data=csv,
                    file_name=f"student_performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    type="secondary"
                )
            
            with col2:
                # Export filtered data if filters are applied
                if search_student != "All Students" or search_subject != "All Subjects":
                    filtered_csv = filtered_df.to_csv(index=False)
                    filename = f"filtered_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    st.download_button(
                        label="📥 Download Filtered Data",
                        data=filtered_csv,
                        file_name=filename,
                        mime="text/csv",
                        type="secondary"
                    )
    
    else:  # Analytics Dashboard
        st.markdown("## 📊 Analytics Dashboard")
        
        # Load data from database
        df = load_data_from_db(conn)
        
        if len(df) == 0:
            st.warning("No data available. Please add some data first.")
            # Show sample data as fallback
            if st.button("Load Sample Data for Demo"):
                sample_df = load_sample_data()
                insert_data_to_db(conn, sample_df)
                st.rerun()
            return
        
        # Data preprocessing
        df['Percentage'] = pd.to_numeric(df['Percentage'], errors='coerce').fillna(0)
        df['Marks'] = pd.to_numeric(df['Marks'], errors='coerce').fillna(0)
        df['Average_Marks'] = pd.to_numeric(df['Average_Marks'], errors='coerce').fillna(0)
        df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce').fillna(0)
        
        # Student selector
        students = df['Name'].unique()
        selected_student = st.sidebar.selectbox("Select Student:", students)
        df_filtered = df[df['Name'] == selected_student].copy()
        
        # Display student name
        st.markdown(f"## 👨‍🎓 Performance Analysis for: **{selected_student}**")
        
        # Performance Overview
        st.markdown("### 📈 Performance Overview")
        create_performance_overview(df_filtered)
        
        # Main visualizations
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📊 Detailed Performance Analysis")
            fig1 = create_subject_performance_chart(df_filtered)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.markdown("### 🎯 Key Insights")
            insights = generate_insights(df_filtered)
            for insight in insights:
                st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
        
        # Trend Analysis
        st.markdown("### 📈 Performance Trend")
        
        # Subject selection for trend analysis
        subjects = ['Overall'] + sorted(df_filtered['Subject'].dropna().unique().tolist())
        selected_subject = st.selectbox("Select Subject for Trend Analysis:", subjects)
        
        fig2 = create_trend_analysis(df_filtered, selected_subject)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed Data Table
        st.markdown("### 📋 Detailed Exam Records")
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            subject_filter = st.multiselect("Filter by Subject:", 
                                           options=df_filtered['Subject'].unique(),
                                           default=df_filtered['Subject'].unique())
        with col2:
            exam_type_filter = st.multiselect("Filter by Exam Type:",
                                             options=df_filtered['Exam_Type'].unique(),
                                             default=df_filtered['Exam_Type'].unique())
        with col3:
            min_percentage = st.slider("Minimum Percentage:", 0, 100, 0)
        
        # Apply filters
        filtered_data = df_filtered[
            (df_filtered['Subject'].isin(subject_filter)) &
            (df_filtered['Exam_Type'].isin(exam_type_filter)) &
            (df_filtered['Percentage'] >= min_percentage)
        ]
        
        # Color code the dataframe
        def color_performance(val):
            if val >= 75:
                return 'background-color: #d4edda; color: #155724'
            elif val >= 60:
                return 'background-color: #fff3cd; color: #856404'
            elif val >= 35:
                return 'background-color: #f8d7da; color: #721c24'
            else:
                return 'background-color: #f5c6cb; color: #721c24'
        
        styled_df = filtered_data.style.applymap(color_performance, subset=['Percentage'])
        st.dataframe(styled_df, use_container_width=True)

if __name__ == "__main__":
    main()