# pip install htmldate  ## verify docker and necessity of using it 
# pip install import plotly_express as px 
# pip install python-whois


import streamlit as st
import pandas as pd 
import numpy as np 
import subprocess
import datetime 
import plotly_express as px 
import seaborn as sns
import matplotlib.pyplot as plt
import requests
from requests.auth import HTTPBasicAuth
import whois
import json
import pytz
import time
import re

from datetime import datetime as dt
from datetime import timedelta





header = st.container()
inputs = st.container()
execute_button =st.container()
legos = st.container()
viz = st.container()
weights  = st.container()
download_archives =  st.container()



#_________ Functions_____________

#_____________ gitub ativity lego_______

def github_code_stats( owner, repo, authorization_token):
    url = "https://api.github.com/repos/{owner}/{repo}/stats/code_frequency"
    headers = {
     'X-GitHub-Api-Version': '2022-11-28', 
     'accept':'application/vnd.github+json', 
     'Authorization': f'Bearer {git_PAT}'
    }

    response = requests.get(url.format(owner=owner, repo=repo), headers=headers, verify = False)
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


##### _________________ final github lefo complie function_______________

@st.cache_data
def github_activity_lego(url_repo_series,start_date_aggregation,end_date_aggregation,year_to_start, year_to_finish, authorization_token ):
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


#_________ end of functions



    
    
    
#_____________________
def subtract_weeks(week_number, year):
    # Convert the week number and year to a date
    date_str = f"{year}-W{week_number}"
    date = dt.strptime(date_str + '-1', "%Y-W%W-%w")

    # Subtract 24 weeks ( 6 months)
    new_date = date - timedelta(weeks=26)

    # Extract the new week number and year from the new date
    new_week_number = int(new_date.strftime("%W"))
    new_year = int(new_date.strftime("%Y"))
    return new_week_number, new_year

def first_wallet_transaction(walletAddress,api_key,chainName):
    
    wallets = []
    answers = []
    
    url = f"https://api.covalenthq.com/v1/{chainName}/bulk/transactions/{walletAddress}/"

    headers = {
        "accept": "application/json",
    }

    basic = HTTPBasicAuth(api_key, '')

    response = requests.get(url, headers=headers, auth=basic, verify = False)

    if ((response.status_code == 200) & (len(response.json()['data']['items']) != 0)) == True:

        first_trx= response.json()['data']['items'][0]['block_signed_at']
        first_trx = first_trx.split("T")[0]
        first_trx  = dt.strptime(first_trx , '%Y-%m-%d')
        answers.append(first_trx)
        wallets.append(walletAddress)

    else: 
        wallets.append(walletAddress)
        answers.append('no data on this chain')
    return wallets[0], answers[0]

@st.cache_data
def wallets_age(recipients, api_key,chainName, round_start):
    
    w_creation_date = []
    recipient = []
    for i in recipients:
        recipient.append(i)
        w_creation_date.append(first_wallet_transaction(i,api_key,chainName)[1])

   
    w_creation = pd.DataFrame(data= {'recipient': recipient, f'w_creation_date_{chainName}': w_creation_date})

    months = []
    for i in range(0,w_creation[f'w_creation_date_{chainName}'].shape[0]):
        if (w_creation[f'w_creation_date_{chainName}'][i] != 'no data on this chain'):
            months.append(((dt.strptime(round_start,"%Y-%m-%d").date() - w_creation[f'w_creation_date_{chainName}'][i].date()).days)/30)
        else:
            months.append(None)
    
    w_creation[f'wallet_months_old_{chainName}'] = months
    return w_creation


@st.cache_data
def input_csv(file):
    df = pd.read_csv(file)
    return(df)

@st.cache_data
def subprocess_github_lego(git_parameters): # issue 7- 8 - 9
    output = subprocess.run(['python', 'github_activity_lego.py'], input =(git_parameters).encode(), capture_output = True)

    return(output)
        
@st.cache_data
def website_validation_lego(website_lists):
    web_df = website_lists
    web_df = pd.DataFrame(web_df)
    web_df = web_df[~web_df['website'].isna()]
    web_df = web_df[web_df['website'] != '']
    web_df = web_df.drop(web_df[web_df.duplicated()].index)
    web_df.reset_index(drop = True, inplace = True)   


    website_date_evaluation = []

    for i in web_df['website']:
        res = whois.whois(i)
        try:
            if (res.creation_date != None) and (type(res.creation_date) == list) :
                date = res.creation_date[0].date()
                website_date_evaluation.append(date) 

            elif res.creation_date == None:
                website_date_evaluation.append('website not working')

            else:
                date = res.creation_date.date()
                website_date_evaluation.append(date) 

        except:
            website_date_evaluation.append('error')

    web_df['website_date_evaluation'] = website_date_evaluation
    return web_df

@st.cache_data
def score_calculation(legos_avaluations,
                      weight_githb_active_months,
                      weight_githb_not_working,
                      weight_website,
                      weight_web_days,
                      weight_no_chain_history,
                      weight_wallet_age):
    github_score = []

    web_score = [] 

    wallet_age_score = []

    for i in range( 0, legos_avaluations.shape[0]):

        github_score.append(np.nansum([
                 weight_githb_active_months * legos_avaluations['months_active'][i],
                 weight_githb_not_working* legos_avaluations['invadalid_repo'][i]]))


    for i in range( 0, legos_avaluations.shape[0]):

        web_score.append(( np.nansum([
        weight_website * legos_avaluations['web_not_working'][i], 
        weight_web_days * legos_avaluations['months_of_existance'][i]])))


    for i in range( 0, legos_avaluations.shape[0]):

        wallet_age_score.append(( np.nansum([
        weight_no_chain_history * legos_avaluations[f'no_history_{chainName}'][i], 
        weight_wallet_age * legos_avaluations[f'wallet_months_old_{chainName}'][i]])))



    legos_avaluations['web_score'] = web_score
    legos_avaluations['github_score'] = github_score
    legos_avaluations['wallet_age_score'] = wallet_age_score

    legos_avaluations['score'] = (
    legos_avaluations['web_score'] + 
    legos_avaluations['github_score'] + 
    legos_avaluations['wallet_age_score']
    )
    
    return legos_avaluations

#______________________ Assets 

covalent_chains = ['eth-mainnet' , 'optimism-mainnet' , 'matic-mainnet' , 'btc-mainnet' ] ## issue #12
  
api_key = st.secrets['covalent_api']
git_PAT = st.secrets['github_PAT']
#________________________ main __________________________________________________________________________



with header: 
    st.title('Mirall0x') 
    st.markdown('#### Welcome!')
    st.markdown('This is an open source project developed to empower communities when analyzing candidates for grants. It uses on-chain and off-chain metadata to deliver quality information in a centralized and visual way for key decision making. Please, read the instructions on how to use it: [How to use Mirall0x](https://github.com/OpenDataforWeb3/Mirall0x/wiki/How-to-use-Mirall0x)')

    

with inputs:
    
    st.markdown("#### PROJECTS TO CHECK")  
    # File uploader
    file = st.file_uploader("Upload CSV file, please check the instructions for the correct schema.", type="csv", key = 'main_csv') # issue 3 
    

    if file:
        df = input_csv(file)
        if file is not None:
            file_name = file.name
            st.markdown("###### THE INPUTED CSV")
            st.dataframe(df)


    st.markdown("#### PARAMETERS")

    col1,col2 = st.columns(2) 
    
with col1 : 
    round_start = st.text_input('Round start or round subscription date like "yyyy-mm-dd".' , key = 'round_start') 
    chainName = st.selectbox('Select the chain to check the recipient wallet address behavior.', covalent_chains) 
                    
    main_button =  st.button('SEND PARAMETERS')

    
    if 'start_button' not in st.session_state: 
            st.session_state.start_button = False 
    
    

    if main_button or st.session_state.start_button:
        
        #round_start = dt.strptime(round_start,"%Y-%m-%d").date()
        
        st.session_state.start_button = True 
        start_week = dt.strptime(round_start,"%Y-%m-%d").date().isocalendar().week
        year_start = dt.strptime(round_start,"%Y-%m-%d").date().isocalendar().year
        finish_week = subtract_weeks(start_week, year_start)[0]
        year_finish = subtract_weeks(start_week, year_start)[1] # issue
     
            

        url_repo_series =  df['github_project_url'].copy()
        url_repo_series = url_repo_series[~url_repo_series.isna()]

        authorization_token = git_PAT

        start_date_aggregation = start_week #  September 7 started the GR15 round
        end_date_aggregation = finish_week # 6 months back

        year_to_start = year_start
        year_to_finish = year_finish

        x1, repo_raw_data = github_activity_lego(url_repo_series,
                                start_date_aggregation,
                                end_date_aggregation,
                                year_to_start,
                                year_to_finish, 

                                authorization_token )

        repo_additions = x1[0]
        repo_deletions = x1[1]

        #________________________ legos 



        with legos:


                legos_avaluations = df[['title', 'website', 'github_project_url','recipient']].copy() 



        #_______________________________________github lego age

                repo_additions = repo_additions.reset_index()
                repo_additions = repo_additions.rename(columns={'index':'github_project_url'})
                
                inactive_weeks = repo_additions.set_index('github_project_url').T.isna().sum()
                inactive_weeks = pd.DataFrame(inactive_weeks, columns = ['weeks_not_active'])
                inactive_months = inactive_weeks['weeks_not_active'] // 4
                active_months = 6 - inactive_months
                active_months = pd.DataFrame(active_months)
                active_months.rename(columns = {'weeks_not_active': 'months_active'}, inplace = True)

                active_months = active_months.reset_index().copy()

                
                
        #_________________________________________ github lego inesxistant repo code (404)

                repo_raw_data = repo_raw_data.reset_index()

                invadalid_repos = list(repo_raw_data[repo_raw_data['extract_status_code'] == 404]['url'])

                invadalid_repo = np.where(df['github_project_url'].isin(invadalid_repos), True, False)

                legos_avaluations['invadalid_repo'] = invadalid_repo





        #______________________________________website validation lego 


                web_df = website_validation_lego(df['website'].copy())

                available_dates = web_df[(web_df['website_date_evaluation'] != 'no date available')
                           &  (web_df['website_date_evaluation'] != 'website not working')].copy()
                available_dates.reset_index(inplace = True)


                months_of_existance = []
                website = []
                for i in range(0,available_dates.shape[0]):

                    months_of_existance.append(((((dt.strptime(round_start,"%Y-%m-%d").date()) - available_dates['website_date_evaluation'][i])).days)/30)

                    website.append(available_dates['website'][i])

                count_days_df = pd.DataFrame(data = {'website': website,'months_of_existance' : months_of_existance})

                
         #_________________________________ wallet_age lego
        
                recipients = legos_avaluations['recipient'].copy().dropna()
                recipients = recipients.reset_index(drop = True)
                
                
                wallet_age_lego = wallets_age(recipients, api_key,chainName, round_start)
                

                

        ## ________________merging legos results 

                legos_avaluations = legos_avaluations.merge(active_months, on = 'github_project_url', how = 'left')  # github lego 
                legos_avaluations = legos_avaluations.merge(web_df, on = 'website', how = 'left')# website evaluations
                legos_avaluations = legos_avaluations.merge(count_days_df, on = 'website', how = 'left') # website available dates days count
                legos_avaluations = legos_avaluations.merge(wallet_age_lego, on = 'recipient', how = 'left')  # wallet age lego for the chooson chain


                legos_avaluations.to_csv('legos_avaluations.csv', index = False)


        #_______________________________________ legos weights

        with weights: 
           
            @st.cache_data
            def read_lego_df(csv_name):
                legos_avaluations = pd.read_csv(csv_name) 
                return legos_avaluations

            legos_avaluations = read_lego_df('legos_avaluations.csv')
            legos_avaluations['web_not_working'] = np.where(legos_avaluations['website_date_evaluation'] =='website not working', True, False)
            legos_avaluations[f'no_history_{chainName}'] = np.where(legos_avaluations[f'w_creation_date_{chainName}'] =='no data on this chain', True, False)
            
            
            
            with st.form('weights'):
               
                st.markdown("#### WEIGHTING THE LEGOS")
                st.markdown("Input the weight for each lego (from -3 to 3) given your understanding of the importance of each behaviour")
                
                col3,col4 = st.columns(2)
                with col3:

                    weight_githb_active_months = st.number_input("Input weight for every month the Github repo existed.", step = 1, key = "weight_githb_active_months")
                    
                    weight_web_days = st.number_input("Input a weight for every month that a website existed.", step = 1, key = "weight_web_date")

                    weight_wallet_age = st.number_input("Input weight for each month old of the wallet on the choosen chain.", step = 1, key = "weight_wallet_age")
                   
                    
                
                with col4:
                    
                    weight_githb_not_working = st.number_input("Input weight for a Github repo url that is not working.", step = 1, key = "weight_githb_not_working")

                    
                    weight_website = st.number_input("Input weight for a website that is not working.", step = 1, key = "weight_website") 
                    
                    
                    weight_no_chain_history  = st.number_input("Input weight for project wallet that have no transaction history.", step = 1, key = "weight_no_chain_history")
                    
                if 'calc_button' not in st.session_state: 
                        st.session_state.calc_button = False 
                    
                def activate_calc_buttom():
                    st.session_state.calc_button = True
                
                calculations_button = st.form_submit_button('START CALCULATIONS', on_click = activate_calc_buttom)

                
                    
                    
            #_________________________________________scores calculations
            
            
               
             if calculations_button or st.session_state.calc_button:
            
                    st.session_state.calc_buttom = True 
                    
                    final_dataframe = score_calculation(legos_avaluations,
                                              weight_githb_active_months,
                                              weight_githb_not_working,
                                              weight_website,
                                              weight_web_days,
                                              weight_no_chain_history,
                                              weight_wallet_age)
    
    
                    st.write(final_dataframe)
    
                    if "x_axis" not in st.session_state:
                        st.session_state.x_axis = 'github_score'
                    if 'y_axis' not in st.session_state:
                        st.session_state.y_axis = 'wallet_age_score'
    
                    possible_axis = ['wallet_age_score', 'github_score', 'web_score']
    
                    
                    
                    x_axis = st.selectbox('Select x_axis',possible_axis, key = 'x_axis' )
    
    
                    y_axis = st.selectbox('Select y_axis',possible_axis, key = 'y_axis' )
    
    
                    plot  = px.scatter_3d(final_dataframe, x = x_axis, y = y_axis, z = 'score'  , color = 'score' , hover_data =[final_dataframe['github_project_url']]
                


#________________________________Download the final df _______________________

 
                    st.markdown("#### CHECK THE PROJECT INFORMATIONS AND SCORES")
                    st.write(final_dataframe)
                    
                    @st.cache_data
                    def convert_df(final_dataframe):
                        # IMPORTANT: Cache the conversion to prevent computation on every rerun
                        return final_dataframe.to_csv().encode('utf-8')
                    
                    csv = convert_df(final_dataframe)
                    
                    st.download_button(
                    label="Download data as CSV",
                    data= csv,
                    file_name='final_dataframe.csv',
                    mime='text/csv',
                )
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
