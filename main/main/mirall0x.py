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


from datetime import datetime as dt
from datetime import timedelta
import whois



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


@st.cache_data
def input_csv(file):
    df = pd.read_csv(file)
    return(df)

@st.cache_data
def subprocess_github_lego(git_parameters):
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

    ##### ISSUE - adicionar no MIro - add cache porque faz as verificaçãoes do website
    ##### add some loading bar here too

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

#________________________ main __________________________________________________________________________



with header: 
    st.title('Mirall0x') 
    st.markdown('#### LOOK INSIDE PROJECTS')
    st.markdown('This is a application to check details and metadata of projects applying for funding. It empowers humans with metadata and automations to check the assests of projects and spot inconsistencies, for more information check the docs ;) [link]')

    

with inputs:
    
    st.markdown("#### PROJECTS TO CHECK")  # trocar aqui por dados direto da chain com os meta dados  dos projetos inscritos? verificar doc do ALLO
    # File uploader
    file = st.file_uploader("Upload CSV file, please check the docs for the correct schema", type="csv", key = 'main_csv')
    

    if file:
        df = input_csv(file)
        if file is not None:
            file_name = file.name
            st.markdown("###### THE INPUTED CSV:")
            st.dataframe(df)
            series = list(df['github_project_url'].copy()) # ajustar pro schema final


    st.markdown("#### INPUTS AND PARAMETERS")

    col1,col2 = st.columns(2) 
    
with col1 : 
    git_PAT = st.text_input('please enter yout github PAT', key = 'git_PAT')
    round_start = st.text_input('input the round start date (or round subscription date) like "yyyy-mm-dd"' , key = 'round_start') 

                    
    main_button =  st.button('SEND PARAMETERS')

    
    if 'start_button' not in st.session_state: 
            st.session_state.start_button = False 
    
    
###### issue -- aqui que entra a escolha do lego o botão dipara os calculos de acordo com as legos escolhidos não direto pro git hub
    if main_button or st.session_state.start_button:
        
        st.session_state.start_button = True 
        start_week = dt.strptime(round_start,"%Y-%m-%d").date().isocalendar().week
        year_start = dt.strptime(round_start,"%Y-%m-%d").date().isocalendar().year
        finish_week = subtract_weeks(start_week, year_start)[0]
        year_finish = subtract_weeks(start_week, year_start)[1] # issue
        
        git_parameters = (f'{git_PAT} {start_week} {finish_week} {year_start} {year_finish} {file_name}')
        
        output = subprocess_github_lego(git_parameters)
        
        st.write(output.stdout.decode())


        with legos:

                legos_avaluations = df[['website', 'github_project_url']].copy()


#_______________________________________github lego

                repo_additions = pd.read_csv('repo_additions.csv') 
    
                repo_additions.rename(columns = {'Unnamed: 0': 'github_project_url'}, inplace = True)

                inactive_weeks = repo_additions.set_index('github_project_url').T.isna().sum()
                inactive_weeks = pd.DataFrame(inactive_weeks, columns = ['weeks_not_active'])
                inactive_months = inactive_weeks['weeks_not_active'] // 4
                active_months = 6 - inactive_months
                active_months = pd.DataFrame(active_months)
                active_months.rename(columns = {'weeks_not_active': 'months_active'}, inplace = True)

                active_months = active_months.reset_index().copy()


#______________________________________website validation lego 
    
                
                web_df = website_validation_lego(df['website'].copy())

                last_update_days = []
                website = []
                available_dates = web_df[(web_df['website_date_evaluation'] != 'no date available')
                           &  (web_df['website_date_evaluation'] != 'website not working')].copy()

                available_dates.reset_index(inplace = True)
                
                    
                for i in range(0,available_dates.shape[0]):

                    last_update_days.append((((dt.strptime(round_start,"%Y-%m-%d").date()) - available_dates['website_date_evaluation'][i])).days)

                    website.append(available_dates['website'][i])

                count_days_df = pd.DataFrame(data = {'website': website,'last_update_days' : last_update_days})


    ## ________________merging legos results 

                legos_avaluations = legos_avaluations.merge(active_months, on = 'github_project_url', how = 'left')  # github lego 
                legos_avaluations = legos_avaluations.merge(web_df, on = 'website', how = 'left')# website evaluations
                legos_avaluations = legos_avaluations.merge(count_days_df, on = 'website', how = 'left') # website available dates days count
                st.markdown('###### DATAFRAME WITH PROJECTS METADATA')

                legos_avaluations.to_csv('legos_avaluations.csv', index = False)
                st.write(legos_avaluations)

        #_______________________________________ legos weights

                with weights: 
                    ### could cache the reading
                    @st.cache_data
                    def read_lego_df(csv_name):
                        legos_avaluations = pd.read_csv(csv_name) 
                        return legos_avaluations
                
                    legos_avaluations = read_lego_df('legos_avaluations.csv')
                    
                    legos_avaluations['web_not_working'] = np.where(legos_avaluations['website_date_evaluation'] =='website not working', True, False)

                    with st.form('weights'):
                        #### can I created a session a way of not rerinning when changing here?
                        st.markdown("#### WEIGHTING THE LEGOS")
                        st.markdown("input the weight for each lego (from -3 to 3) given your understand of the importance of each analysis. Remenber: the final score represents how trustworth a project is, so positive weights means trustfull behaviour, there fore posite scores and vice-versa")
                        weight_githb_active_months = st.number_input("input weight for each month of existence of the Github repo", step = 1, key = "weight_githb_less_1")
                       
                        weight_website = st.number_input("input weights for websites that are not working", step = 1, key = "weight_website") 
                        weight_web_days = st.number_input("input a weight for every day that a website existed before the start of your round", step = 0.001, key = "weight_web_date") 


                        calculations_button = st.form_submit_button('START CALCULATIONS')

                    if 'calc_button' not in st.session_state: 
                        st.session_state.calc_button = False 
                        
                    if calculations_button or st.session_state.calc_button:
                            github_score = []

                            web_score = [] 

                            for i in range( 0, legos_avaluations.shape[0]):

                                github_score.append(np.nansum(
                                         weight_githb_active_months * legos_avaluations['months_active'][i]))


                            for i in range( 0, legos_avaluations.shape[0]):

                                web_score.append(( np.nansum([
                                weight_website * legos_avaluations['web_not_working'][i], 
                                weight_web_days * legos_avaluations['last_update_days'][i]])))


                            legos_avaluations['web_score'] = web_score
                            legos_avaluations['github_score'] = github_score


                            legos_avaluations['score'] = legos_avaluations['web_score'] + legos_avaluations['github_score']

                            plot  = px.scatter_3d(legos_avaluations, x ='github_score', y = 'web_score', z = 'score'  , color = 'score' , hover_data =[legos_avaluations['github_project_url']]
                        )
                            ### -  issue colocar comunicaçao para pessoa ver em full screen 

                            st.markdown("### VIZUALISE AND COMPARE THE PROJECTs")
                            st.markdown("tip : click on the two arrows on the right corner to full screen the graph. Hover the mouse to see more information of each dot (projet)") 
                            st.plotly_chart(plot)
                            st.markdown("")
                            st.markdown("#### CHECK THE PROJECT INFORMATIONS AND SCORES")
                            st.write(legos_avaluations)



# with download_archives: 
    

            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        