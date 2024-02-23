import streamlit as st
from Sources.GitHubAPI import GitHubAPI, WorkflowRun
import pandas as pd

def app():
    github_api = GitHubAPI(st.secrets['github_token'])

    st.title('GitHub Action Usage')
    col1, col2 = st.columns(2)
    start_date = col1.date_input('Start Date')
    end_date = col2.date_input('End Date')
    repository_name = st.text_input('Repository Name', value='jll-labs/corrigo-enterprise-ios')
    cost_input = st.text_input('Cost ($/min)', value='UBUNTU=0.008;MACOS=0.08;MACOS_LARGE=0.12;MACOS_XLARGE=0.16')
    cost_per_runner = {runner.split('=')[0]: float(runner.split('=')[1]) for runner in cost_input.split(';')}

    if repository_name:
        # fetch workflow runs
        runs = github_api.get_runs_with_timing(repository_name, start_date, end_date)

        st.write('## Workflow Runs by Repository')
        st.write(f'### {repository_name}')

        # Convert the list of WorkflowRun instances to a list of dictionaries
        all_runs_data = [run.to_dict() for run in runs]

        # Convert the list of dictionaries to a DataFrame
        df_all = pd.DataFrame(all_runs_data).fillna(0)

        # Add cost columns
        for runner_name, cost in cost_per_runner.items():
            if runner_name in df_all.columns:
                df_all[f'{runner_name} ($)'] = df_all[runner_name] * cost
                df_all.drop(columns=[runner_name], inplace=True)

        # Add total cost column
        df_all['Total Cost ($)'] = df_all[[col for col in df_all.columns if col.endswith('($)')]].sum(axis=1)

        # Group by Name
        df_grouped_by_name = df_all.groupby('Name').agg({'Total Cost ($)': 'sum', 'Run duration (min)': 'sum'}).reset_index()

        # Adds runs count
        df_grouped_by_name['Runs count'] = df_all['Name'].value_counts().sort_index().values

        # Order grouped by total cost
        df_grouped_by_name = df_grouped_by_name.sort_values('Total Cost ($)', ascending=False)

        # Print
        st.table(df_grouped_by_name)
        st.expander('All Workflow Runs').table(df_all)

        # COST ESTIMATION

        # st.write('## iOS Cost Estimation')
        # df_all['< 1min'] = df_all['Run duration (min)'].apply(lambda x: 1 if x < 1 else 0)
        # df_all['1-5min'] = df_all['Run duration (min)'].apply(lambda x: 1 if x >= 1 and x < 5 else 0)
        # df_all['5-9min'] = df_all['Run duration (min)'].apply(lambda x: 1 if x >= 5 and x < 9 else 0)
        # df_all['> 9min'] = df_all['Run duration (min)'].apply(lambda x: 1 if x >= 9 else 0)
        # df_all['billable mins'] = df_all['< 1min'] + df_all['1-5min'] * 2.5*1.4 + df_all['5-9min'] * 7.5*1.4 + df_all['> 9min'] * 17
        # df_all['est cost xlarge'] = df_all['billable mins'] * 0.16
        # df_groupped_by_name = df_all.groupby('Name').agg({'> 20min' : 'sum', '< 1min': 'sum', '1-5min': 'sum', '5-9min': 'sum', '> 9min': 'sum', 'billable mins': 'sum', 'est cost xlarge' : 'sum'}).reset_index()

        # df_groupped_by_name.drop(columns=['< 1min', '1-5min', '5-9min', '> 9min'], inplace=True)

        # st.table(df_groupped_by_name)
        