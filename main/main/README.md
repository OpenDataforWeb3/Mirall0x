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
To run the app successfully, you need to create a **.streamlit** directory in the main folder containing you mirallOx.py  <br>


This folder would contain a secrets.toml file for you to store you covalent_api and github_api keys which can be gotten  <br>
here respectively _[Covalent](https://www.covalenthq.com/docs/api/)_ and _[GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)_. 
