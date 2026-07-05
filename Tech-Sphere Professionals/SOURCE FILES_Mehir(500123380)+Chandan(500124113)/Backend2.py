import pandas as pd
import requests
from newsapi import NewsApiClient

class JobFinder:
    def __init__(self, file_path=r"C:\Users\8HIN\Desktop\Data Science project\Job opportunities1.csv"):
        """Load job dataset"""
        self.df = pd.read_csv(file_path, encoding="ISO-8859-1")

    def filter_jobs(self, Required_Skill="", location="", experience=""):
        """Filter jobs based on skill, location, and experience"""
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
        return self.df['Required Skills'].str.split(', ').explode().value_counts().head(10)

    def get_location_distribution(self):
        return self.df['Location'].value_counts().head(5)

    def get_salary_distribution(self):
        return self.df[['Experience Level', 'Salary Range']]

class RealTimeJobFetcher:
    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_jobs(self, skill):
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {"query": skill, "page": "1", "num_pages": "1"}
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            return []

class CompanyNewsFetcher:
    def __init__(self, news_api_key):
        self.client = NewsApiClient(api_key=news_api_key)

    def get_company_news(self, company_name):
        articles = self.client.get_everything(q=company_name, language='en', sort_by='publishedAt')
        return articles['articles'][:5]

# Testable module
if __name__ == "__main__":
    job_finder = JobFinder()
    sample_jobs = job_finder.filter_jobs(Required_Skill="Python", location="London", experience="mid")
    print(sample_jobs.head())
