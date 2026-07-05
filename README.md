<h1 align="Left">Predictive Analytics of CSE Job Market using Machine Learning</h1>

<p align="Left">
An end-to-end Machine Learning and Data Science project that predicts Computer Science job market trends, analyzes skill demand, forecasts salaries, and provides interactive dashboards for data-driven career planning.
</p>

---

## Overview

The **Predictive Analytics of CSE Job Market** project leverages Machine Learning, Data Science, and Business Intelligence techniques to analyze and forecast trends in the Computer Science and Engineering (CSE) job market.

Using real-world job posting datasets, the system identifies in-demand technical skills, predicts salary ranges, forecasts future job opportunities, and visualizes employment trends through interactive dashboards. The project is designed to help students, job seekers, recruiters, and educational institutions make informed decisions through data-driven insights.

---

## Key Features

- Job Market Trend Analysis
- Salary Prediction using Machine Learning
- Future Job Demand Forecasting
- Skill Demand Analysis
- Exploratory Data Analysis (EDA)
- Interactive Dashboard
- Business Intelligence Reports
- Career Recommendation Insights
- Data Visualization
- Predictive Analytics

---

## Project Architecture

<p align="center">
    <img src="Images/architecture.png" alt="Project Architecture" width="950">
</p>

### Workflow

```text
Job Portals / Employment Dataset
                │
                ▼
        Data Collection
                │
                ▼
      Data Preprocessing
(Removing Null Values, Feature Engineering,
 Encoding, Cleaning)
                │
                ▼
   Exploratory Data Analysis (EDA)
                │
                ▼
     Machine Learning Models
   ├── Linear Regression
   ├── Prophet Forecasting
   ├── K-Means Clustering
   └── NLP Skill Extraction
                │
                ▼
      Model Evaluation
                │
                ▼
 Interactive Dashboard
(Streamlit + Flask + Power BI)
                │
                ▼
 Job Prediction • Salary Prediction
 Skill Analysis • Career Insights
```

---

## Machine Learning Models

- Linear Regression
- Prophet Time-Series Forecasting
- K-Means Clustering
- Natural Language Processing (NLP)

---

## Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- Prophet
- Streamlit
- Flask
- Power BI

---

## Dashboard Preview

<p align="Left">
    <img src="Images/Screenshot%202026-07-05%20225156.png" alt="Job Search Interface" width="900">
</p>

<p align="Left">
    <img src="Images/Screenshot%202026-07-05%20230238.png" alt="Interactive Career Dashboard" width="900">
</p>

---

## Performance

| Metric | Result |
|---------|--------|
| R² Score | **0.807** |
| Mean Absolute Error (MAE) | **₹5,784** |
| Cross Validated R² | **0.698 ± 0.210** |
| Job Demand Forecast Accuracy | **88%** |
| Job Classification Accuracy | **92.01%** |

---

## Repository Structure

```text
Predictive Analytics of CSE Job Market
│
├── README.md
├── Dataset
│   └── Job_Opportunities.csv
│
├── Source Code
│   ├── preprocessing.py
│   ├── eda.py
│   ├── salary_prediction.py
│   ├── forecasting.py
│   ├── clustering.py
│   └── app.py
│
├── Models
│
├── Dashboard
│   └── dashboard.pbix
│
├── Images
│   ├── Screenshot 2026-07-05 225156.png
│   └── Screenshot 2026-07-05 230238.png
│
├── Documentation
│   ├── Project_Report.pdf
│   └── Help_Manual.pdf
│
├── requirements.txt
└── LICENSE
```

---

## Project Workflow

1. Data Collection from multiple job portals
2. Data Cleaning and Preprocessing
3. Feature Engineering
4. Exploratory Data Analysis (EDA)
5. Salary Prediction using Linear Regression
6. Job Demand Forecasting using Prophet
7. Job Clustering using K-Means
8. NLP-based Skill Extraction
9. Model Evaluation and Validation
10. Interactive Dashboard Development
11. Career Insights and Job Recommendation

---

## Applications

- Career Planning
- Salary Prediction
- Job Market Forecasting
- Skill Gap Analysis
- Educational Curriculum Planning
- Business Intelligence
- Employment Analytics

---

## Future Scope

- Real-Time Job Data Integration using LinkedIn and Naukri APIs
- AI-powered Resume Analysis
- Personalized Career Recommendation System
- Skill Recommendation Engine
- Cloud Deployment
- Mobile Application Development
- AI Chatbot for Career Guidance

---

## Project Goal

The primary objective of this project is to bridge the gap between academic learning and industry requirements by leveraging Machine Learning and Data Science techniques to predict job market trends, forecast salaries, identify emerging skills, and provide actionable career insights through interactive dashboards.

---

## Author

**Mehir Saxena**

B.Tech Computer Science Engineering (Data Science)  
University of Petroleum and Energy Studies (UPES), Dehradun

GitHub: https://github.com/MehirSaxena736

LinkedIn: www.linkedin.com/in/mehirs
