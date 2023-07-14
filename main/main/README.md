Main files. To run it locally you should keep them all in the same folder. 

### Installation

#### On windows using venv:
```bash	
git clone https://github.com/OpenDataforWeb3/Mirall0x
cd Mirall0x
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run main\\main\\mirall0x.py
```

#### 💻 On MAC OS Using venv

⬇️ Download the github repo by running
```
git clone https://github.com/OpenDataforWeb3/Mirall0x
```
📁 Change directory to Mirallox app
```
cd Mirall0x/main/main/
```
🐍 Create a python virtual environment
```
python3 -m venv .venv
```
💥Activate the virtual environment
```
source .venv/bin/activate
```
⚙️Install the required packages for th application.
```
pip install -r requirements.txt
```
🚀 Lunch the Streamlit app
```
streamlit run mirall0x.py
```
### ⚠ PS
To run the app successfully, you need to create a **.streamlit** directory in the main folder containing the mirallOx.py  <br>
<img width="342" alt="Screenshot 2023-07-14 at 18 55 06" src="https://github.com/AlexPam/Mirall0x/assets/55463668/8ef07625-20c9-467e-9354-fce186b13f74">


This folder would contain a secrets.toml file for you to store you covalent_api and github_PAT keys which can be gotten  <br>
here respectively _[Covalent](https://www.covalenthq.com/docs/api/)_ and _[GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)_. 
