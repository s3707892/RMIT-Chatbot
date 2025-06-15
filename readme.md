# Assignment 3 Chatbot Deployment Guide - Group 47

**Purpose:** Help users to run this chatbot using windows or Mac

---

## 🗂️ Preparation

### 📁 Step 0: Download Starter Files

Download the starter files either from the Github repo, or from the student submission.

* The folder structure looks like this:

```
DCNC/
├── .venv\
├── data\
├── ────chroma_db\
├── ────2026-course-guide.pdf
├── ────rmit-course-data.json
├── app.py
├── requirements.txt
├── config.json
├── readme.md
```

---

## 🧰 Step 1: Check Python Version

### ✅ Requirement: Python 3.11

Open Terminal (macOS) or Command Prompt / PowerShell (Windows), and run:

```bash
python --version
```

If the version is **not 3.11.x**, download and install it from: [https://www.python.org/downloads/release/python-3110/](https://www.python.org/downloads/release/python-3110/)

---

## 🐍 Step 2: Set Up Virtual Environment (Recommended)

In your terminal, navigate into the unzipped folder:

```bash
cd path/to/DCNC
```

Create and activate a virtual environment:

### Windows:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```


##IF THIS DOES NOT WORK, TRY RUNNING COMMAND PROMPT AS AN ADMINISTRATOR, AND RUNNING THE COMMANDS FROM THERE.
```bash
Use cd c:\folder\folder
```
With folder as the directory your project is located
then use .venv\scripts\activate

### macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 📦 Step 3: Install Dependencies



Once your virtual environment is activated, install all dependencies:

```bash
pip install -r requirements.txt
```

If this does not work properly, please try to upgrade your pip first using:

```bash
python -m pip install --upgrade pip
```

you may need to install the packages individually, try:

```bash
pip install boto3
pip install chromadb
pip install streamlit
```

finally, if this does not work, you may need to install a specific version of numpy first, try:

```bash
pip install boto3
pip installnumpy==1.24.3
pip install chromadb
pip install streamlit
```


If installation is successful, you’ll return to the prompt without errors.

Sometimes, You might see the warning like 'Import "streamlit" could not be resolvedPylancereportMissingImports' in your VS Code editor. Don't worry — this warning is from the VS Code language server (Pylance) and does not affect code execution as long as streamlit is installed correctly.

This usually happens when:

VS Code is not using the correct Python interpreter (e.g. your virtual environment), or

The language server hasn't picked up the environment changes yet.

✅ If you have already installed the requirements and can run the app using:

streamlit run app.py
then everything is working as expected, and you can safely ignore this warning.


---
## Step 4: Input credentials to config.json

Sample credentials are already entered, and can be used if needed.
Otherwise, open the file and replace details with your own.

## 🚀 Step 5: Run the Chatbot

To launch the chatbot UI:

```bash
streamlit run app.py
```

This will open a browser window with your chatbot interface.


---



## 💬 Step 5: Start Chatting

The chatbot may initially take about 1 minute to launch.
This only happens if its never been launched before, as it needs to initialise the database.
There is a database file saved already, but on new computers sometimes a new one will need to be generated.

There is also a startup time of about 8 seconds that initialises the connection with AWS Bedrock
Having this at the start speeds up the response times whilst chatting.

Prompt the chatbot with things such as "I like plants, help me choose a course"
If you try to talk about non course related topics, the chatbot will steer you towards course oriented conversation.

The chatbot has memory retention, so you can ask for further information. It has access to information such as atar requirements, pathways and prerequisites.

---

## ❓ Troubleshooting

| Issue                          | Solution                                                      |
| ------------------------------ | ------------------------------------------------------------- |
| `streamlit: command not found` | Make sure virtual environment is activated                    |
| Cannot install packages        | Ensure you have Python 3.11 and pip is working                |
| No browser opens               | Visit [http://localhost:8501](http://localhost:8501) manually |
| Data not loaded properly       | Check file formats and filenames                              |

---

## ✅ Done!

References:

Please note, a large amount of the formatting was thanks to "Cyber Security Course Advisor via AWS Bedrock Author: Cyrus Gao, extended by Xiang Li Updated: May 2025"
