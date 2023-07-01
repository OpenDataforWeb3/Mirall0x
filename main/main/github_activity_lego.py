

import requests
import json
import pandas as pd
import datetime 
from datetime import datetime as dt
import pytz
import time
import re


######### functions

def github_code_stats( owner, repo, authorization_token):
    url = "https://api.github.com/repos/{owner}/{repo}/stats/code_frequency"
    headers = {
     'X-GitHub-Api-Version': '2022-11-28', 
     'accept':'application/vnd.github+json', 
     'Authorization': authorization_token
     }
    
    response = requests.get(url.format(owner=owner, repo=repo), headers=headers)
    response_status = response.status_code
    response_json = {}
    if (
        response.status_code != 204 and
        response.headers["content-type"].strip().startswith("application/json")
    ):
        try:
            response_json  = response.json()

        except ValueError:
            pass

    return {'status_code': response_status ,'repo_data' : response_json}


#-----------------
# get the owner and the repo name of a list of projects github urls
# accepts URLS give back a df with URL / owner of the repo / Repo name
# does not work with None values
#function return a df

def get_owner_repo(github_urls):

    owner = []
    repo = []
    url = []

    for i in github_urls:
        matches = re.search(r"github\.com\/([\w\-\.]+)\/([\w\-\.]+)", i)
        if matches:
            username = matches.group(1)
            repository_name = matches.group(2)
            url.append(i)
            owner.append(username)
            repo.append(repository_name)
        else:
            matches = re.search(r"github\.com\/([\w\-\.]+)", i)
            if matches:
                owner_name = matches.group(1)
                url.append(i)
                owner.append(owner_name)
                repo.append(None)
            else:
                url.append(i)
                owner.append(None)
                repo.append(None)

    github_owner_repo = pd.DataFrame(data= {'url': url, 'owner': owner, 'repo': repo})
    return github_owner_repo
    
#------------------------
# receives the df produced on the last function
# makes a first call for every line 
# saves the status code and the json returned
# as long we have 202 as status  code ( github is still gathering data for that repo)
# it waits and makes calls till it gets '200' and the repo data
# return a df with the columns =  ['url', 'owner', 'repo', 'extract_status_code', 'repo_data']

def retrive_git_data(owner_repo_names, authorization_token):
    
        column_names = ['url', 'owner', 'repo', 'extract_status_code', 'repo_data']
        git_data  = pd.DataFrame([],columns = column_names)

        for i in range(0,len(owner_repo_names['owner'])):
                # gettin owner and repo
                git_owner = owner_repo_names.iloc[i]['owner']
                git_repo = owner_repo_names.iloc[i]['repo']

                # pocking the APi to start gathering the stats
                git_extract = github_code_stats(git_owner, git_repo, authorization_token)
                
                data = [{'url' : owner_repo_names.iloc[i]['url'], 'owner' : git_owner, 'repo' : git_repo,  'extract_status_code': 
                        git_extract['status_code'] , 'repo_data': git_extract['repo_data']}]
                df = pd.DataFrame(data = data)
                
                git_data = pd.concat([git_data, df])


        git_data.set_index('url', inplace = True)

        while git_data['extract_status_code'].isin([202]).sum() != 0:

            time.sleep(20)

            redo_df = git_data[git_data['extract_status_code'] == 202].reset_index().copy()
            for i in range(len(redo_df)):

                redo_owner = redo_df.loc[i, 'owner']
                redo_repo = redo_df.loc[i, 'repo']

                git_extract = github_code_stats(redo_owner, redo_repo, authorization_token)

                if (git_extract['status_code'] != 403):

                    git_data.at[redo_df['url'][i], 'extract_status_code'] = git_extract['status_code']
                    git_data.at[redo_df['url'][i], 'repo_data'] = git_extract['repo_data']

                else:

                    break


        return git_data

#---------------------------------------------------------------------
# function used inside 'timeframing_data' to get the time stamp of the sunday of a given week by its number
# its used to filter the start and finish of the period to colect the data 

def sunday_timestamp(week_number, year):
    # Create a datetime object for the first day of the given year
    first_day = datetime.datetime(year, 1, 1, tzinfo=pytz.utc)
    
    # Calculate the number of days to the first Sunday of the year
    days_to_first_sunday = (6 - first_day.weekday()) % 7
    
    # Calculate the number of days to the Sunday of the given week
    days_to_sunday = (week_number - 1) * 7 + days_to_first_sunday
    
    # Create a datetime object for the Sunday of the given week
    sunday = first_day + datetime.timedelta(days=days_to_sunday)
    
    # Convert the datetime object to a UTC timestamp
    return int(sunday.timestamp())




#-------------------------------------------------------
# function to treat the json data generated by github_code_stats returns a datafram with the url/weeks/ additons or deletion per week on that repo
# repo_data must be in json 
# start and end date aggregation in week number 
# year number like 'yyyy' = '2023'




def tretened_df(raw_git_data, start_date_aggregation, end_date_aggregation, year_to_start,year_to_finish ):

    columns_dates = [] 

    for w in range(end_date_aggregation, start_date_aggregation +1): # prestar atenção na questão do inclusivo exclusivo
        columns_dates.append(dt.date(dt.fromtimestamp(sunday_timestamp(w ,year_to_start))))

    addtions_df  = pd.DataFrame([], columns = columns_dates)


    deletions_df  = pd.DataFrame([], columns = columns_dates)

    valid_git_data = raw_git_data[raw_git_data['extract_status_code'] == 200]

    valid_git_data

    for n in range(0,(valid_git_data.shape[0])):  #" a questão tava aqui no "n'""
        weeks = []
        addition = []
        deletions = []

        for i in range(0,(len(valid_git_data['repo_data'][n])-1)):

            weeks.append(dt.date(dt.fromtimestamp(valid_git_data['repo_data'][n][i][0])))
            addition.append(valid_git_data['repo_data'][n][i][1])
            deletions.append(valid_git_data['repo_data'][n][i][2])


        week_addition = pd.DataFrame( data = [weeks, addition, deletions]).T

        week_addition.columns = ['weeks', 'addition', 'deletions']

        additions_by_week = week_addition[(week_addition['weeks']<= dt.date(dt.fromtimestamp(sunday_timestamp(start_date_aggregation,year_to_start))))
                                           & (week_addition['weeks'] >=  dt.date(dt.fromtimestamp(sunday_timestamp(end_date_aggregation,year_to_start))))]  


        ad_df = additions_by_week[['weeks','addition']].T
        ad_df.columns=ad_df.iloc[0] 
        ad_df.drop(labels='weeks', inplace = True)
        ad_df.rename(index = {'addition' :valid_git_data.index[n]}, inplace = True)
        addtions_df= pd.concat([addtions_df, ad_df])

        del_df = additions_by_week[['weeks','deletions']].T
        del_df.columns=del_df.iloc[0] 
        del_df.drop(labels='weeks', inplace = True)
        del_df.rename(index = {'deletions' :valid_git_data.index[n]}, inplace = True)
        deletions_df= pd.concat([deletions_df, del_df])

    return addtions_df, deletions_df


#--------------------------------------------


#########################################################final compile function #####################################


def repo_additions_deletion(url_repo_series,start_date_aggregation,end_date_aggregation,year_to_start, year_to_finish, authorization_token ):
    # from a list get the owner and repo names
    owner_repo_names  = get_owner_repo(url_repo_series)

    #cleaning the none values, dealing with index issues
    owner_repo_names = owner_repo_names[~owner_repo_names['repo'].isna()]
    owner_repo_names = owner_repo_names[owner_repo_names['repo'] != '']
    owner_repo_names = owner_repo_names.drop(owner_repo_names[owner_repo_names.duplicated()].index)
    owner_repo_names.reset_index(drop = True, inplace = True)


    #  pocking , waiting and getting the data from the API. 
    # returning repo infos and raw json with all weeks and adds and dels by week timestamp
    raw_git_data = retrive_git_data(owner_repo_names, authorization_token)

    # treats the data to the dates we specifyed a
    #  returns addtions and deletions data frames together with the raw dataframe

    return tretened_df(raw_git_data, start_date_aggregation, end_date_aggregation, year_to_start,year_to_finish ) , raw_git_data


####### end of functions

############## inputu ########################

inp = input('')  


git_PAT = inp.split()[0]
start_week = int(inp.split()[1])
finish_week = int(inp.split()[2])
year_start = int(inp.split()[3])
year_finish  = int(inp.split()[4])

df = pd.read_csv(f'{inp.split()[5]}')

#######################

sample = df['github_project_url'] # aqui vai ter que trazer e alguma maneira a series


url_repo_series =  sample
url_repo_series = url_repo_series[~url_repo_series.isna()]

authorization_token = git_PAT

start_date_aggregation = start_week #  September 7 started the GR15 round
end_date_aggregation = finish_week # 6 months back

year_to_start = year_start
year_to_finish = year_finish

x1, x2 = repo_additions_deletion(url_repo_series,
                        start_date_aggregation,
                        end_date_aggregation,
                        year_to_start,
                        year_to_finish, 
 
                        authorization_token )
# this direction of saving should be changed to fit where the app is hosted

x1[0].to_csv('repo_additions.csv')
x1[1].to_csv('repo_deletions.csv')
x2.to_csv('repo_raw_data.csv')


print('finished')




