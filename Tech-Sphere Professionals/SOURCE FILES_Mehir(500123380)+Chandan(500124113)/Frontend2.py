import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import hashlib
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
import urllib.request
import time
from datetime import datetime
import requests
import warnings
import json
import os

# Suppress warnings
warnings.filterwarnings("ignore")

# ====================== CONFIGURATION ======================
# Environment variables for sensitive data
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', 'ec70c1e9bbmsh1a7dca9ef97a387p19ee42jsnbe4f065214d1')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '98093fbf8bcd4a37a7035b52273c50bf')

# Email configuration - Replace with your actual credentials
EMAIL_CONFIG = {
    'sender': os.getenv('EMAIL_SENDER', 'mehirsaxena34@gmail.com'),
    'password': os.getenv('EMAIL_PASSWORD', 'rtmd wkzq enat kxyt'),  # Use app password if 2FA enabled
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587))
}

# ====================== BACKEND CLASSES ======================
class JobFinder:
    def __init__(self, file_path="Job opportunities1.csv"):
        """Load job dataset"""
        try:
            self.df = pd.read_csv(file_path, encoding="ISO-8859-1")
            # Clean data
            self.df['Required Skills'] = self.df['Required Skills'].fillna('')
            self.df['Location'] = self.df['Location'].fillna('Remote')
        except Exception as e:
            st.error(f"Error loading job data: {str(e)}")
            self.df = pd.DataFrame()

    def filter_jobs(self, Required_Skill="", location="", experience=""):
        """Filter jobs based on skill, location, and experience"""
        if self.df.empty:
            return None
            
        filtered_df = self.df.copy()

        if Required_Skill:
            filtered_df = filtered_df[filtered_df['Required Skills'].str.contains(Required_Skill, case=False, na=False)]
        if location:
            filtered_df = filtered_df[filtered_df['Location'].str.contains(location, case=False, na=False)]

        experience_levels = {
            "entry": ["Entry Level"],
            "junior": ["Junior", "1-2 Years"],
            "mid": ["Mid-Level", "3-5 Years"],
            "senior": ["Senior", "5-10 Years"],
            "executive": ["Executive", "Director", "10+ Years"]
        }

        if experience.lower() in experience_levels:
            exp_categories = experience_levels[experience.lower()]
            filtered_df = filtered_df[filtered_df['Experience Level'].str.contains('|'.join(exp_categories), case=False, na=False)]

        return filtered_df if not filtered_df.empty else None

    def get_skill_demand(self):
        if self.df.empty:
            return pd.Series()
        return self.df['Required Skills'].str.split(', ').explode().value_counts().head(10)

    def get_location_distribution(self):
        if self.df.empty:
            return pd.Series()
        return self.df['Location'].value_counts().head(5)

    def get_salary_distribution(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df[['Experience Level', 'Salary Range']].dropna()

class RealTimeJobFetcher:
    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_jobs(self, skill, location=""):
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            query = f"{skill} developer"
            if location:
                query += f" in {location}"
                
            querystring = {
                "query": query,
                "page": "1",
                "num_pages": "1",
                "date_posted": "month"
            }
            
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching jobs: {str(e)}")
            return []
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return []

# ====================== INITIALIZATION ======================
job_finder = JobFinder()
job_fetcher = RealTimeJobFetcher(RAPIDAPI_KEY)

# ====================== DATABASE FUNCTIONS ======================
def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect('techsphere.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, 
                      password TEXT, 
                      email TEXT,
                      skills TEXT,
                      last_notification_check TIMESTAMP)''')

        # Saved jobs table
        c.execute('''CREATE TABLE IF NOT EXISTS saved_jobs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT,
                      job_id TEXT,
                      job_details TEXT,
                      source TEXT,
                      saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      UNIQUE(username, job_id))''')

        # Notifications table
        c.execute("DROP TABLE IF EXISTS notifications")  # Ensure fresh start
        c.execute('''CREATE TABLE IF NOT EXISTS notifications
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT,
                      message TEXT,
                      job_details TEXT,
                      is_read INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        conn.commit()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
    finally:
        conn.close()

init_db()

# ====================== AUTHENTICATION FUNCTIONS ======================
def make_hashes(password):
    """Generate password hash"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Verify password hash"""
    return make_hashes(password) == hashed_text

def create_user(username, password, email):
    """Create a new user account"""
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                   (username, make_hashes(password), email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False
    finally:
        conn.close()

def login_user(username, password):
    """Authenticate user"""
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_hashes(password, user['password']):
            return dict(user)
        return None
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return None
    finally:
        conn.close()

def update_user_profile(username, email=None, skills=None):
    """Update user profile information"""
    conn = get_db_connection()
    try:
        if email is not None:
            conn.execute('UPDATE users SET email = ? WHERE username = ?', (email, username))
        if skills is not None:
            conn.execute('UPDATE users SET skills = ? WHERE username = ?', (skills, username))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Profile update error: {str(e)}")
        return False
    finally:
        conn.close()

# ====================== JOB FUNCTIONS ======================
def save_job(username, job_id, job_details, source):
    """Save a job to user's collection"""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT OR IGNORE INTO saved_jobs (username, job_id, job_details, source) VALUES (?, ?, ?, ?)',
            (username, job_id, json.dumps(job_details), source)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving job: {str(e)}")
        return False
    finally:
        conn.close()

def get_saved_jobs(username):
    """Retrieve user's saved jobs"""
    conn = get_db_connection()
    try:
        jobs = conn.execute(
            'SELECT job_id, job_details, source FROM saved_jobs WHERE username = ? ORDER BY saved_at DESC',
            (username,)
        ).fetchall()
        
        saved_jobs = []
        for job in jobs:
            try:
                details = json.loads(job['job_details'])
                details['job_id'] = job['job_id']
                details['source'] = job['source']
                saved_jobs.append(details)
            except json.JSONDecodeError:
                # Handle dataset jobs referenced by index
                try:
                    idx = int(job['job_id'])
                    row = job_finder.df.loc[idx].to_dict()
                    row['job_id'] = str(idx)
                    row['source'] = job['source']
                    saved_jobs.append(row)
                except:
                    continue
        return saved_jobs
    except Exception as e:
        st.error(f"Error loading saved jobs: {str(e)}")
        return []
    finally:
        conn.close()

def delete_saved_job(username, job_id):
    """Remove a job from user's saved jobs"""
    conn = get_db_connection()
    try:
        conn.execute(
            'DELETE FROM saved_jobs WHERE username = ? AND job_id = ?',
            (username, job_id)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting job: {str(e)}")
        return False
    finally:
        conn.close()

# ====================== NOTIFICATION FUNCTIONS ======================
def check_job_alerts(username):
    """Check for new jobs matching user skills and create notifications"""
    conn = get_db_connection()
    try:
        # Get user skills
        user = conn.execute('SELECT skills FROM users WHERE username = ?', (username,)).fetchone()
        if not user or not user['skills']:
            return
        
        skills = user['skills']
        
        # Fetch new jobs
        jobs = job_fetcher.fetch_jobs(skills)
        if jobs:
            for job in jobs[:5]:  # Limit to 5 most recent jobs
                # Check if we already notified about this job
                existing = conn.execute('''SELECT 1 FROM notifications 
                                        WHERE username = ? AND job_details LIKE ?''',
                                      (username, f'%{job.get("job_id", "")}%')).fetchone()
                
                if not existing:
                    message = f"🔔 New {job.get('job_title', 'job')} position at {job.get('employer_name', 'a company')}"
                    add_notification(username, message, job)
                    
                    # Send email notification if user has email
                    user_email = conn.execute('SELECT email FROM users WHERE username = ?', (username,)).fetchone()
                    email = user_email['email'] if user_email else None
                    if email:
                        send_job_email(username, job)
        
        conn.commit()
    except Exception as e:
        st.error(f"Error checking job alerts: {str(e)}")
    finally:
        conn.close()

def add_notification(username, message, job_details=None):
    """Add a new notification for the user"""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO notifications (username, message, job_details) VALUES (?, ?, ?)',
            (username, message, json.dumps(job_details) if job_details else None)
        )
        conn.commit()
    except Exception as e:
        st.error(f"Error adding notification: {str(e)}")
    finally:
        conn.close()

def get_unread_notifications(username):
    """Get user's unread notifications"""
    conn = get_db_connection()
    try:
        notifications = conn.execute(
            '''SELECT id, message, job_details, created_at 
               FROM notifications 
               WHERE username = ? AND is_read = 0 
               ORDER BY created_at DESC''',
            (username,)
        ).fetchall()
        
        result = []
        for note in notifications:
            try:
                job_details = json.loads(note['job_details']) if note['job_details'] else None
                result.append({
                    'id': note['id'],
                    'message': note['message'],
                    'job_details': job_details,
                    'created_at': note['created_at']
                })
            except:
                continue
        return result
    except Exception as e:
        st.error(f"Error getting notifications: {str(e)}")
        return []
    finally:
        conn.close()

def mark_notifications_read(username):
    """Mark all notifications as read for a user"""
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE notifications SET is_read = 1 WHERE username = ?',
            (username,)
        )
        conn.commit()
    except Exception as e:
        st.error(f"Error marking notifications read: {str(e)}")
    finally:
        conn.close()

# ====================== EMAIL FUNCTIONS ======================
def send_email(receiver_email, subject, body):
    """Send email using SMTP"""
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = receiver_email
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server and send
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender'], EMAIL_CONFIG['password'])
            server.sendmail(EMAIL_CONFIG['sender'], receiver_email, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        st.error("Email authentication failed. Please check your email credentials.")
        return False
    except Exception as e:
        st.error(f"Email sending failed: {str(e)}")
        return False

def send_job_email(username, job_details):
    """Send job details to user's email"""
    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT email FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        
        if not user or not user['email']:
            st.warning("No email address found in your profile")
            return False
            
        email = user['email']
        subject = f"Job Opportunity: {job_details.get('Job Title', job_details.get('job_title', 'N/A'))}"
        
        # Build email body
        body = f"""Job Details:\n\n"""
        if 'Job Title' in job_details:  # Database job
            body += f"Title: {job_details['Job Title']}\n"
            body += f"Company: {job_details['Company']}\n"
            body += f"Location: {job_details['Location']}\n"
            body += f"Skills: {job_details.get('Required Skills', 'N/A')}\n"
            if 'Apply Link' in job_details:
                body += f"Apply here: {job_details['Apply Link']}\n"
        else:  # Live API job
            body += f"Title: {job_details.get('job_title', 'N/A')}\n"
            body += f"Company: {job_details.get('employer_name', 'N/A')}\n"
            body += f"Location: {job_details.get('job_city', 'Remote')}\n"
            body += f"Posted: {job_details.get('job_posted_at_datetime_utc', 'N/A')}\n"
            if 'job_apply_link' in job_details:
                body += f"Apply here: {job_details['job_apply_link']}\n"
        
        return send_email(email, subject, body)
    except Exception as e:
        st.error(f"Error sending job email: {str(e)}")
        return False
    finally:
        conn.close()

# ====================== UI COMPONENTS ======================
def show_home_page():
    """Display the home page"""
    st.markdown('<div class="header">TechSphere Professional</div>', unsafe_allow_html=True)
    
    # Header image (smaller size)
    try:
        image_url = "https://img.freepik.com/free-vector/business-team-putting-together-jigsaw-puzzle-isolated-flat-vector-illustration-cartoon-partners-working-connection-teamwork-partnership-cooperation-concept_74855-9814.jpg"
        urllib.request.urlretrieve(image_url, "header_img.jpg")
        st.image("header_img.jpg", use_container_width=True, width=400)  # Adjusted width
    except:
        st.image("https://via.placeholder.com/800x300?text=TechSphere+Professional", use_container_width=True, width=400)
    
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <h3 style="color: #FFFFFF;">Your Complete Career Intelligence Platform</h3>
        <p style="font-size: 16px; color: #CCCCCC;">
            Advanced analytics, real-time opportunities, and strategic insights for professionals
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    cols = st.columns(3)
    features = [
        ("📊", "Market Analytics", "Real-time skill demand visualization"),
        ("🔍", "Smart Search", "AI-powered job matching"),
        ("🔔", "Live Alerts", "Instant notifications for new opportunities")
    ]
    
    for idx, (icon, title, desc) in enumerate(features):
        with cols[idx]:
            st.markdown(f"""
            <div class="feature-card">
                <h3>{icon} {title}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

def show_login_page():
    """Display the login page"""
    st.subheader("Secure Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        
        if st.form_submit_button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    st.markdown("Don't have an account? **Sign up** from the sidebar menu.")

def show_signup_page():
    """Display the signup page"""
    st.subheader("New Account Registration")
    
    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type='password')
        confirm = st.text_input("Confirm Password", type='password')
        
        if st.form_submit_button("Register"):
            if password == confirm:
                if create_user(username, password, email):
                    st.success("Account created successfully")
                    st.info("Please login with your new credentials")
                else:
                    st.error("Username already exists")
            else:
                st.warning("Passwords do not match")

def show_dashboard_page(username):
    """Display the user dashboard"""
    st.subheader("Career Dashboard")
    
    # Check for job alerts
    check_job_alerts(username)
    
    # Notification section
    notifications = get_unread_notifications(username)
    if notifications:
        with st.expander(f"🔔 New Alerts ({len(notifications)})", expanded=True):
            for note in notifications:
                timestamp = datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S')
                job_details = note['job_details']
                
                st.markdown(f"""
                <div class="notification">
                    <small>{timestamp.strftime('%Y-%m-%d %H:%M')}</small>
                    <p><strong>{note['message']}</strong></p>
                    {f"<p>Location: {job_details.get('job_city', 'Remote')}</p>" if job_details else ""}
                    {f"<p>Company: {job_details.get('employer_name', '')}</p>" if job_details else ""}
                    {f"<a href='{job_details.get('job_apply_link', '#')}' target='_blank' class='apply-button'>Apply Now</a>" if job_details and job_details.get('job_apply_link') else ""}
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("Mark all as read"):
                mark_notifications_read(username)
                st.rerun()
    else:
        st.info("No new notifications")
    
    # Skills section
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT skills FROM users WHERE username = ?', (username,)).fetchone()
        current_skills = user['skills'] if user and user['skills'] else ""
    finally:
        conn.close()
    
    new_skills = st.text_input("Update your skills (comma separated)", value=current_skills)
    if new_skills != current_skills:
        update_user_profile(username, skills=new_skills)
        st.success("Skills updated")
    
    # Market insights
    st.markdown("### Market Intelligence")
    tab1, tab2, tab3 = st.tabs(["Skill Demand", "Location Trends", "Salary Analysis"])
    
    with tab1:
        st.write("Top 10 In-Demand Skills")
        skill_demand = job_finder.get_skill_demand()
        if not skill_demand.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(
                x=skill_demand.values, 
                y=skill_demand.index, 
                ax=ax, 
                palette="Blues_d", 
                hue=skill_demand.index, 
                legend=False
            )
            ax.set_facecolor('#1E1E1E')
            fig.patch.set_facecolor('#1E1E1E')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            st.pyplot(fig)
        else:
            st.warning("No skill demand data available")
    
    with tab2:
        st.write("Top Hiring Locations")
        loc_dist = job_finder.get_location_distribution()
        if not loc_dist.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.barplot(
                x=loc_dist.values, 
                y=loc_dist.index, 
                ax=ax, 
                palette="Greens_d", 
                hue=loc_dist.index, 
                legend=False
            )
            ax.set_facecolor('#1E1E1E')
            fig.patch.set_facecolor('#1E1E1E')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            st.pyplot(fig)
        else:
            st.warning("No location data available")
    
    with tab3:
        st.write("Salary Distribution by Experience")
        salary_dist = job_finder.get_salary_distribution()
        if not salary_dist.empty:
            st.dataframe(salary_dist.style.background_gradient(cmap='YlOrBr'))
        else:
            st.warning("No salary data available")

def show_job_search_page(username):
    """Display the job search page"""
    st.subheader("Advanced Job Search")
    
    tab1, tab2 = st.tabs(["Database Search", "Live Job Search"])
    
    with tab1:
        st.markdown("#### Search Local Database")
        col1, col2 = st.columns(2)
        
        with col1:
            skill = st.text_input("Skill", key="db_skill")
            location = st.text_input("Location", key="db_location")
        
        with col2:
            experience = st.selectbox("Experience Level", 
                                   ["Any", "Entry", "Junior", "Mid", "Senior", "Executive"],
                                   key="db_experience")
        
        if st.button("Search Database", key="db_search"):
            jobs = job_finder.filter_jobs(
                skill if skill else "",
                location if location else "",
                experience if experience != "Any" else ""
            )
            
            if jobs is not None:
                for idx, row in jobs.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class="job-card">
                            <h4>{row['Job Title']}</h4>
                            <p><strong>{row['Company']}</strong> • {row['Location']}</p>
                            <p>{row['Required Skills']}</p>
                            <div style="display: flex; justify-content: space-between;">
                                <small>Posted: {row.get('Posting Date', 'N/A')}</small>
                                <div>
                                    <a href='{row.get('Apply Link', '#')}' target='_blank' class='apply-button'>Apply</a>
                                    <button class='save-button'>Save</button>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Unique key for each save button
                        if st.button(f"Save Job {idx}", key=f"save_db_{idx}"):
                            if save_job(username, str(idx), row.to_dict(), "database"):
                                st.success("Job saved to your profile")
                                st.rerun()
                            else:
                                st.warning("Job already saved")
            else:
                st.warning("No jobs found matching your criteria")
    
    with tab2:
        st.markdown("#### Search Live Jobs")
        col1, col2 = st.columns(2)
        
        with col1:
            live_skill = st.text_input("Search by Skill", "python", key="live_skill")
        
        with col2:
            live_location = st.text_input("Filter by Location (optional)", key="live_location")
        
        if st.button("Search Live Jobs", key="live_search"):
            with st.spinner("Fetching live jobs..."):
                jobs = job_fetcher.fetch_jobs(live_skill, live_location)
                
                if jobs:
                    for job in jobs:
                        if live_location and job.get('job_city', '').lower() != live_location.lower():
                            continue
                            
                        with st.container():
                            st.markdown(f"""
                            <div class="job-card">
                                <h4>{job.get('job_title', 'N/A')}</h4>
                                <p><strong>{job.get('employer_name', 'N/A')}</strong> • {job.get('job_city', 'Remote')}</p>
                                <p>{job.get('job_description', '')[:200]}...</p>
                                <div style="display: flex; justify-content: space-between;">
                                    <small>Posted: {job.get('job_posted_at_datetime_utc', 'N/A')}</small>
                                    <div>
                                        <a href='{job.get('job_apply_link', '#')}' target='_blank' class='apply-button'>Apply Now</a>
                                        <button class='save-button'>Save</button>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Unique key for each save button
                            job_id = job.get('job_id', str(time.time()))
                            if st.button(f"Save {job_id[:6]}", key=f"save_live_{job_id}"):
                                if save_job(username, job_id, job, "api"):
                                    st.success("Job saved to your profile")
                                    st.rerun()
                                else:
                                    st.warning("Job already saved")
                else:
                    st.warning("No live jobs found. Try different search terms.")

def show_saved_jobs_page(username):
    """Display saved jobs page"""
    st.subheader("Your Saved Opportunities")
    saved_jobs = get_saved_jobs(username)
    
    if saved_jobs:
        for job in saved_jobs:
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h4>{job.get('Job Title', job.get('job_title', 'N/A'))}</h4>
                    <p><strong>{job.get('Company', job.get('employer_name', 'N/A'))}</strong> • {job.get('Location', job.get('job_city', 'Remote'))}</p>
                    <p>{job.get('Required Skills', job.get('job_description', ''))[:200]}...</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <small>Saved from: {job.get('source', 'unknown')}</small>
                        <div>
                            <a href='{job.get('Apply Link', job.get('job_apply_link', '#'))}' target='_blank' class='apply-button'>Apply</a>
                            <button class='save-button' style='background-color: #f44336 !important;'>Remove</button>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Email and remove buttons
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button(f"Email Me This Job", key=f"email_{job.get('job_id', '')}"):
                        if send_job_email(username, job):
                            st.success("Email sent successfully!")
                        else:
                            st.error("Failed to send email")
                
                with col2:
                    if st.button(f"Remove Job", key=f"remove_{job.get('job_id', '')}"):
                        if delete_saved_job(username, job.get('job_id')):
                            st.success("Job removed")
                            st.rerun()
                        else:
                            st.error("Failed to remove job")
    else:
        st.info("You haven't saved any jobs yet")
        st.image("https://img.freepik.com/free-vector/no-data-concept-illustration_114360-536.jpg", width=300)

def show_help_page(username):
    """Display help and support page"""
    st.subheader("Help & Support Center")
    
    tab1, tab2, tab3 = st.tabs(["User Guide", "FAQ", "Feedback"])
    
    with tab1:
        st.markdown("""
        ### How to Use TechSphere Professional
        
        **1. Getting Started**
        - Register an account or login if you already have one
        - Complete your profile with your skills and email
        
        **2. Job Searching**
        - Use the "Job Search" tab to find opportunities
        - Save interesting jobs to your profile
        - Set up email notifications for new matches
        
        **3. Market Insights**
        - View skill demand trends
        - Analyze salary distributions
        - See hiring locations
        
        **4. Running the App**
        ```bash
        pip install streamlit pandas matplotlib seaborn pillow requests
        streamlit run app.py
        ```
        """)
    
    with tab2:
        st.markdown("""
        ### Frequently Asked Questions
        
        **Q: How often are job listings updated?**  
        A: Our database is updated weekly, and live API searches show real-time results.
        
        **Q: How do I get email notifications?**  
        A: Ensure your email is set in your profile and skills are updated. New matching jobs will trigger notifications.
        
        **Q: Can I export my saved jobs?**  
        A: Currently this feature is in development. In the meantime, you can email jobs to yourself individually.
        
        **Q: Why aren't my saved jobs showing up?**  
        A: Make sure you're logged in with the same account you used to save the jobs. If issues persist, try logging out and back in.
        
        **Q: How do I change my email preferences?**  
        A: You can update your email address in your profile settings. Notifications will be sent to the most recent email on file.
        """)
    
    with tab3:
        st.markdown("### We'd love your feedback!")
        with st.form("feedback_form"):
            feedback = st.text_area("Your comments or suggestions")
            if st.form_submit_button("Submit Feedback"):
                conn = get_db_connection()
                try:
                    conn.execute(
                        'INSERT INTO feedback (username, message) VALUES (?, ?)',
                        (username, feedback)
                    )
                    conn.commit()
                    st.success("Thank you! Your feedback has been recorded.")
                except Exception as e:
                    st.error(f"Failed to submit feedback: {str(e)}")
                finally:
                    conn.close()

def show_profile_page(username):
    """Display user profile page"""
    st.subheader("Your Profile")
    
    conn = get_db_connection()
    try:
        user = conn.execute(
            'SELECT email, skills FROM users WHERE username = ?', 
            (username,)
        ).fetchone()
        current_email = user['email'] if user and user['email'] else ""
        current_skills = user['skills'] if user and user['skills'] else ""
    finally:
        conn.close()
    
    new_email = st.text_input("Email", value=current_email)
    new_skills = st.text_input("Your Skills", value=current_skills)
    
    if st.button("Update Profile"):
        if update_user_profile(username, new_email, new_skills):
            st.success("Profile updated successfully")
        else:
            st.error("Failed to update profile")
    
    st.markdown("---")
    st.subheader("Account Actions")
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.success("Logged out successfully")
        time.sleep(1)
        st.rerun()

# ====================== MAIN APP ======================
def main():
    # Page configuration
    st.set_page_config(
        page_title="TechSphere Pro",
        page_icon="💼",
        layout="wide"
    )
    
    # Dark theme styling
    st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        
        /* Text color */
        .stTextInput>label, .stSelectbox>label, .stTextArea>label,
        .stNumberInput>label, .stDateInput>label {
            color: #FAFAFA !important;
        }
        
        /* Header styling */
        .header {
            font-size: 2em;
            color: #FFFFFF;
            text-align: center;
            padding: 15px 0;
            margin-bottom: 20px;
        }
        
        /* Cards */
        .feature-card {
            background-color: #1E1E1E;
            color: #FFFFFF;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 15px;
            border: 1px solid #333;
        }
        
        /* Job cards */
        .job-card {
            background-color: #1E1E1E;
            color: #FFFFFF;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            border: 1px solid #333;
        }
        
        /* Notifications */
        .notification {
            background-color: #1A3A5F;
            color: #FFFFFF;
            padding: 8px;
            border-radius: 4px;
            margin: 4px 0;
            border-left: 3px solid #2196F3;
        }
        
        /* Apply button styling */
        .apply-button {
            background-color: #2196F3 !important;
            color: white !important;
            border: none !important;
            padding: 5px 10px !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            margin-right: 5px !important;
            text-decoration: none !

        }

        /* Save button styling */
        .save-button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 5px 10px !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            text-decoration: none !important;
            display: inline-block !important;
        }
        
        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #0E1117;
        }
        
        /* Dropdown menu styling */
        .dropdown-menu {
            background-color: #1E1E1E;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
    
    # Navigation menu
    if st.session_state.logged_in:
        with st.sidebar:
            st.title("Navigation")
            
            # Main dropdown menu
            menu_choice = st.selectbox(
                "Main Menu",
                ["Dashboard", "Job Search", "Saved Jobs", "Profile", "Help"],
                key="main_menu"
            )
            
            # Additional features dropdown
            st.markdown("---")
            with st.expander("Additional Features"):
                st.markdown("""
                - **Company News**: Get latest news about companies
                - **Skill Analysis**: Detailed breakdown of skill demand
                - **Salary Benchmark**: Compare salaries across industries
                """)
            
            st.markdown("---")
            st.markdown(f"Logged in as **{st.session_state.username}**")
    else:
        with st.sidebar:
            st.title("Navigation")
            menu_choice = st.selectbox(
                "Main Menu",
                ["Home", "Login", "SignUp"],
                key="main_menu"
            )
    
    # Page routing
    if menu_choice == "Home":
        show_home_page()
    elif menu_choice == "Login" and not st.session_state.logged_in:
        show_login_page()
    elif menu_choice == "SignUp" and not st.session_state.logged_in:
        show_signup_page()
    elif st.session_state.logged_in:
        if menu_choice == "Dashboard":
            show_dashboard_page(st.session_state.username)
        elif menu_choice == "Job Search":
            show_job_search_page(st.session_state.username)
        elif menu_choice == "Saved Jobs":
            show_saved_jobs_page(st.session_state.username)
        elif menu_choice == "Profile":
            show_profile_page(st.session_state.username)
        elif menu_choice == "Help":
            show_help_page(st.session_state.username)
    else:
        st.warning("Please login to access this page")
        show_login_page()

if __name__ == '__main__':
    main()