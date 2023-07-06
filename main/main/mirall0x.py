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
def wallets_age(addresses, api_key,chainName, round_start):
    
    w_creation_date = []
    address = []
    for i in addresses:
        address.append(i)
        w_creation_date.append(first_wallet_transaction(i,api_key,chainName)[1])

   
    w_creation = pd.DataFrame(data= {'address': address, f'w_creation_date_{chainName}': w_creation_date})

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



#______________________ Assets 

covalent_chains = ['eth-mainnet' , 'optimism-mainnet' , 'matic-mainnet' , 'btc-mainnet' ] ## issue #12
  
api_key = ''  
#________________________ main __________________________________________________________________________



with header: 
    st.title('Mirall0x') 
    st.markdown('#### LOOK INSIDE PROJECTS')
    st.markdown('This is a application to check details and metadata of projects applying for funding. It empowers humans with metadata and automations to check the assests of projects and spot inconsistencies, for more information check the docs ;) [link]')

    

with inputs:
    
    st.markdown("#### PROJECTS TO CHECK")  
    # File uploader
    file = st.file_uploader("Upload CSV file, please check the docs for the correct schema", type="csv", key = 'main_csv') # issue 3 
    

    if file:
        df = input_csv(file)
        if file is not None:
            file_name = file.name
            st.markdown("###### THE INPUTED CSV:")
            st.dataframe(df)
            series = list(df['github_project_url'].copy()) 


    st.markdown("#### INPUTS AND PARAMETERS")

    col1,col2 = st.columns(2) 
    
with col1 : 
    git_PAT = st.text_input('please enter yout github PAT', key = 'git_PAT')
    round_start = st.text_input('input the round start date (or round subscription date) like "yyyy-mm-dd"' , key = 'round_start') 
    chainName = st.selectbox('Select the chain you would like to check the walle', covalent_chains) 
                    
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
        
        git_parameters = (f'{git_PAT} {start_week} {finish_week} {year_start} {year_finish} {file_name}')
        
        output = subprocess_github_lego(git_parameters)
        
        st.write(output.stdout.decode())
        
        #________________________ legos 


        with legos:


                legos_avaluations = df[['title_x', 'website', 'github_project_url','address_x']].copy() 



        #_______________________________________github lego age

                repo_additions = pd.read_csv('repo_additions.csv') 

                repo_additions.rename(columns = {'Unnamed: 0': 'github_project_url'}, inplace = True)

                inactive_weeks = repo_additions.set_index('github_project_url').T.isna().sum()
                inactive_weeks = pd.DataFrame(inactive_weeks, columns = ['weeks_not_active'])
                inactive_months = inactive_weeks['weeks_not_active'] // 4
                active_months = 6 - inactive_months
                active_months = pd.DataFrame(active_months)
                active_months.rename(columns = {'weeks_not_active': 'months_active'}, inplace = True)

                active_months = active_months.reset_index().copy()


        #_________________________________________ github lego inesxistant repo code (404)

                raw = pd.read_csv('repo_raw_data.csv')

                invadalid_repos = list(raw[raw['extract_status_code'] == 404]['url'])

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
        
                legos_avaluations.rename(columns = {'address_x' : 'address'},inplace = True) ### issue #3 - to be altered when adapeted to Allo Schema
                addresses = legos_avaluations['address'].copy().dropna()
                addresses = addresses.reset_index(drop = True)
                
                
                wallet_age_lego = wallets_age(addresses, api_key,chainName, round_start)
                

                

        ## ________________merging legos results 

                legos_avaluations = legos_avaluations.merge(active_months, on = 'github_project_url', how = 'left')  # github lego 
                legos_avaluations = legos_avaluations.merge(web_df, on = 'website', how = 'left')# website evaluations
                legos_avaluations = legos_avaluations.merge(count_days_df, on = 'website', how = 'left') # website available dates days count
                legos_avaluations = legos_avaluations.merge(wallet_age_lego, on = 'address', how = 'left')  # wallet age lego for the chooson chain


                legos_avaluations.to_csv('legos_avaluations.csv', index = False)
#                 st.write(legos_avaluations)

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
                st.markdown("input the weight for each lego (from -3 to 3) given your understand of the importance of each analysis. Remenber: the final score represents how trustworth a project is, so positive weights means trustfull behaviour, there fore posite scores and vice-versa")
                
                col3,col4 = st.columns(2)
                with col3:

                    weight_githb_active_months = st.number_input("input weight for every month the Github repo existed ", step = 1, key = "weight_githb_active_months")
                    
                    weight_web_days = st.number_input("input a weight for every month that a website existed", step = 1, key = "weight_web_date")

                    weight_wallet_age = st.number_input("input weight for each month old of the wallet on the choosen chain", step = 1, key = "weight_wallet_age")
                   
                    
                
                with col4:
                    
                    weight_githb_not_working = st.number_input("input weight for a Github repo that is not available", step = 1, key = "weight_githb_not_working")

                    
                    weight_website = st.number_input("input weight for a website that is not available", step = 1, key = "weight_website") 
                    
                    
                    weight_no_chain_history  = st.number_input("input weight for project wallet that have no transaction hitory", step = 1, key = "weight_no_chain_history")
                    
                    
                    
                    
                    
            #_________________________________________scores calculations
            
            
                calculations_button = st.form_submit_button('START CALCULATIONS')

            if 'calc_button' not in st.session_state: 
                st.session_state.calc_button = False 

            if calculations_button or st.session_state.calc_button:
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

                    plot  = px.scatter_3d(legos_avaluations, x ='github_score', y = 'wallet_age_score', z = 'score'  , color = 'score' , hover_data =[legos_avaluations['github_project_url']]
                )
                    
              #________________________________________ vizualisation      
            
                    ### -  issue #14 #15

                    st.markdown("### VIZUALISE AND COMPARE THE PROJECTs")
                    st.markdown("tip : click on the two arrows on the right corner to full screen the graph. Hover the mouse to see more information of each dot (projet)") 
                    st.plotly_chart(plot)
                    st.markdown("")
                    st.markdown("#### CHECK THE PROJECT INFORMATIONS AND SCORES")
                    st.write(legos_avaluations)



  

            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
