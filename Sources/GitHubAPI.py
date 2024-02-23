from Sources.downloader import download
from requests.models import Response
from typing import List
import math
from datetime import datetime
import streamlit as st

# https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository
# https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#get-workflow-run-usage

class RunnerUsageTime:
    def __init__(self, name: str, total_ms: int):
        self.name = name
        self.total_ms = total_ms
        self.total_min = math.ceil(total_ms / 1000 / 60)

class WorkflowRun:
    def __init__(self, id: str, name: str, created_at: str, run_duration_ms: int, runners_usage: List[RunnerUsageTime]):
        self.id = id
        self.name = name
        self.created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        self.run_duration_ms = run_duration_ms
        self.run_duration_min = round(run_duration_ms / 1000 / 60)
        self.runners_usage = runners_usage
    
    def to_dict(self) -> dict:
        dict = {
            # 'id': self.id,
            'Created': self.created_at,
            'Name': self.name,
            # 'run_duration_ms': self.run_duration_ms,
            'Run duration (min)': self.run_duration_min,
        }
        for runner_usage in self.runners_usage:
            dict[runner_usage.name] = runner_usage.total_min

        return dict

class GitHubAPI:
    def __init__(self, token):
        self.token = token

    def get_runs_with_timing(self, repo: str, start_date, end_date) -> List[WorkflowRun]:
        runs = self.__get_runs(repo, start_date, end_date)
        runs_with_timing = []
        runs_count = len(runs)
        run_idx = 0
        for run in runs:
            run_id = run['id']
            run_name = run['name']
            created_at = run['created_at']
            billable_time = self.__get_timing_for_run(repo, run_id, run_idx, runs_count)
            run_duration_ms = billable_time.get('run_duration_ms', 0)
            billable = billable_time['billable']
            runners_usage = []
            for runner_name, runner_data in billable.items():
                runners_usage.append(RunnerUsageTime(runner_name, runner_data['total_ms']))
        
            runs_with_timing.append(WorkflowRun(run_id, run_name, created_at, run_duration_ms, runners_usage))
            run_idx += 1

        return runs_with_timing


    def __get_runs(self, repo: str, start_date, end_date):
        url = f'https://api.github.com/repos/{repo}/actions/runs'

        all_runs = []
        page = 0
        # format YYYY-MM-DD..YYYY-MM-DD
        created_range = f'{start_date}..{end_date}'
        while True:
            query_params = {
                'page': str(page),
                'per_page': '50',
                'created': created_range
            }
            response = download(url, self.token, f'Downloading workflow runs... {page}. page', query_params)

            if response is None:
                return all_runs
            
            all_runs.extend(response.json().get('workflow_runs', []))
            
            link = response.headers.get('Link')
            if link is None:
                break

            next_link_exists = link.find('rel="next"')

            if next_link_exists:
                page += 1
            else:
                break

        return all_runs
    
    @st.cache_data(ttl="90d", show_spinner=False)
    def __get_timing_for_run(_self, repo:str, run_id: str, _run_idx: int, _runs_count: int):
        url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/timing'
        response = download(url, _self.token, f'Downloading timing for run... {_run_idx + 1}/{_runs_count}')
        return response.json() if response else None