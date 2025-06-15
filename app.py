# CRMIT Course Advisor via AWS Bedrock
# Author: Cory McLean
# Updated: June 2025

import streamlit as st
import json
import boto3
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import time




st.set_page_config(page_title="RMITbot Course Advisor", layout="centered")

#Initialise the session (chatbot first message is pre determined to make intiial loading time faster)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm RMITbot, your helpful assistant for RMIT courses. How can I assist you today? I'd be happy to provide information about the official RMIT course offerings. Please let me know if you have any specific questions."}
    ]
if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None
if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False
if "context_messages" not in st.session_state:
    st.session_state.context_messages = []

# === Helper: Get AWS Credentials === #
def get_credentials(username, password):
    try:
        idp_client = boto3.client("cognito-idp", region_name=st.session_state.REGION)
        response = idp_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
            ClientId=st.session_state.APP_CLIENT_ID,
        )
        id_token = response["AuthenticationResult"]["IdToken"]

        identity_client = boto3.client("cognito-identity", region_name=st.session_state.REGION)
        identity_response = identity_client.get_id(
            IdentityPoolId=st.session_state.IDENTITY_POOL_ID,
            Logins={f"cognito-idp.{st.session_state.REGION}.amazonaws.com/{st.session_state.USER_POOL_ID}": id_token},
        )

        creds_response = identity_client.get_credentials_for_identity(
            IdentityId=identity_response["IdentityId"],
            Logins={f"cognito-idp.{st.session_state.REGION}.amazonaws.com/{st.session_state.USER_POOL_ID}": id_token},
        )

        return creds_response["Credentials"]
    except idp_client.exceptions.NotAuthorizedException as e:
        st.error("Authentication failed: Invalid username or password. Please check your credentials in config.json")
        raise
    except idp_client.exceptions.UserNotFoundException:
        st.error("Authentication failed: User not found. Please check your username in config.json")
        raise
    except Exception as e:
        st.error(f"An unexpected error occurred during authentication: {str(e)}")
        raise

def initialize_aws():
    try:
        #Load configuration from config.json
        st.session_state.REGION = st.secrets["region"]
        st.session_state.MODEL_ID = st.secrets["model_id"]
        st.session_state.IDENTITY_POOL_ID = st.secrets["identity_pool_id"]
        st.session_state.USER_POOL_ID = st.secrets["user_pool_id"]
        st.session_state.APP_CLIENT_ID = st.secrets["app_client_id"]
        st.session_state.USERNAME = st.secrets["username"]
        st.session_state.PASSWORD = st.secrets["password"]


        #Get credentials and initialize client
        credentials = get_credentials(st.session_state.USERNAME, st.session_state.PASSWORD)
        st.session_state.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=st.session_state.REGION,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretKey"],
            aws_session_token=credentials["SessionToken"],
        )
    except Exception as e:
        st.error(f"Failed to initialize AWS: {str(e)}")
        raise


#Set up timers
start_total = time.time()

start_aws = time.time()
#initialise AWS if its the first loading of session
if "aws_initialized" not in st.session_state:
    initialize_aws()
    st.session_state.aws_initialized = True


start_chroma = time.time()
client = chromadb.PersistentClient(path="data\\chroma_db")
collection = client.get_or_create_collection("courses")


#Will only load data if it hasnt been loaded before
start_populate = time.time()
if collection.count() == 0:
    with open("data\\rmit_course_data.json", "r", encoding="utf-8") as f:
        courses_json = json.load(f)
    course_list = []
    documents = []  
    metadatas = []  
    for course in courses_json:
        #make structured text data for the chatbot to read
        if course['name'] is None:
            name = "unknown"
        else:
            name = course['name']
            course_list.append(name)
        if course['rmit_code'] is None:
            rmit_code = "unknown"
        else:
            rmit_code = course['rmit_code']
        if course['campus'] is None:
            campus = "unknown"
        else:
            campus = course['campus']
        if course['atar'] is None:
            atar = "unknown"
        else:
            atar = course['atar']
        if course['duration'] is None:
            duration = "unknown"
        else:
            duration = course['duration']
        if course['prerequisites'] is None:
            prerequisites = "unknown"
        else:
            prerequisites = course['prerequisites']
        if course['pathways'] is None:
            pathways = "unknown"
        else:
            pathways = ""
            for pathway in pathways:
                pathways += f"{pathway}\n"
        doc = f"""
        {name}
        RMIT Code: {rmit_code}
        Campus: {campus}
        ATAR: {atar}
        Duration: {duration}
        Prerequisites: {prerequisites}
        Pathways: {pathways}

        {course['raw_text']}
        """
        documents.append(doc.strip())
        metadatas.append({"name": name, "rmit_code": rmit_code, "campus": campus, "ATAR": atar, "Duration": duration, "prerequisites": prerequisites, "pathways": pathways})
    print("Populating ChromaDB...")
    collection.add(
        documents=documents,              
        metadatas=metadatas,                
        ids=[f"course-{i}" for i in range(len(documents))]  
    )
    #Timer for first time launch (establishing vector storage)
    st.write(f"ChromaDB population took {time.time() - start_populate:.2f} seconds")



def bedrock_prompt_assist(prompt_text, max_tokens=640, temperature=0.3, top_p=0.9):
    #Send user message to a chatbot, it will generate keywords based off the user message
    prompt = [{"role": "user", "content": f"can you generate keywords for courses that suit the user prompt. Keep it very brief, just a list of keywords. Use information from the prompt to infer what the user may like. If the user prompt can not be related to coursework, just reply back with the user prompt. User prompt: {prompt_text}**PLEASE ONLY RESPOND WITH VERY BASIC KEYWORDS** If the user prompt seems like a reply to something, please just respond back with the user prompt, and do not generate a list"}]
    print(F"OG PROMPT: {prompt_text}")
    st.session_state.context_messages.append({"role": "user", "content": prompt_text})
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "messages": prompt
    }
    response = st.session_state.bedrock_runtime.invoke_model(
        body=json.dumps(payload),
        modelId=st.session_state.MODEL_ID,
        contentType="application/json",
        accept="application/json"
    )


    result = json.loads(response["body"].read())
    content = result["content"][0]["text"]
    print(f"Course suggestions: {content}")
    st.session_state.context_messages.append({"role": "assistant", "content": content})
    return search_chromedb(content, prompt_text)

def search_chromedb(query, prompt):
    result = ""

    print(f"Searching ChromaDB with: {query}")
    results = collection.query(
        query_texts=[query],
        n_results=5,
        include=["documents", "distances", "metadatas"]
    )

    print(f"Raw search results: {results}")
    
    #Dont use documents unless they are similar
    threshold = 2.0
    relevant_docs = [
        (doc, dist) for doc, dist in zip(results["documents"][0], results["distances"][0])
        if dist <= threshold
    ]
    
    print(f"Number of relevant docs found: {len(relevant_docs)}")
    print(f"Distances: {results['distances'][0]}")
    
    if relevant_docs:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            result += f"Matched Course: {meta['name']}\nCourse Details:\n {doc}\n {'='*60}\n"      
        print(f"Final result string: {result}")
        #Send the search results query to the chatbot, the prompt is customised to ensure a good response
        return invoke_bedrock(f"You are an RMIT Chatbot. Only provide information that an RMIT chatbot would, such as course information. Speak in plain text. The students know that you are an rmit chatbot, so there is no need to specify. specific course details such as atar, pathways etc* *repeat for more course options if required* Use the following results to provide a response to the student query. Primarily \n {result} **IF THE STUDENT QUERY IS CONVERSATIONAL, MAKE BRIEF CONVERSATION BUT STEER IT TOWARDS COURSE HELP**. If you get the data, please respond with details such as ATAR and other requirements/information. Student Query: {prompt}. if the original student query doesn't have any information about what kind of course might be good for them, respond to them briefly with no course data, and prompt for them to provide you with more information")  
    else:
        print("No relevant documents found within threshold")
        #If no relevant docs found, send prompt to chatbot about there being no matching data
        return invoke_bedrock(f"If there is text saying about replying back with user prompt, please ignore it. We found no matching data, please respond briefly and steer the conversation towards course help. Student query: {prompt}")

# === Helper: Invoke Claude via Bedrock === #
def invoke_bedrock(prompt_text, max_tokens=640, temperature=0.3, top_p=0.9):
    st.session_state.context_messages.append({"role": "user", "content": prompt_text})
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "messages": st.session_state.context_messages
    }

    response = st.session_state.bedrock_runtime.invoke_model(
        body=json.dumps(payload),
        modelId=st.session_state.MODEL_ID,
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    content = result["content"][0]["text"]
    st.session_state.context_messages.append({"role": "assistant", "content": content})
    return content

st.title("\U0001F393 RMITBot Course Advisor")

#Display chat history when page refreshes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#If there's a pending user message, show it and a loading spinner
if st.session_state.pending_user_message:
    with st.chat_message("user"):
        st.markdown(st.session_state.pending_user_message)
    with st.chat_message("assistant"):
        with st.spinner("Generating advice..."):
            st.write("Processing data...")  #Show instant feedback to user to make chat loading experience feel smooth
#Check for user input
user_question = st.chat_input("Send a message")
if user_question:
    st.session_state.pending_user_message = user_question
    st.session_state.awaiting_response = True
    st.rerun()

# On refresh, generate chatbot response (this happens because it makes the loading sequence more user friendly)
if st.session_state.awaiting_response and st.session_state.pending_user_message:
    #Add user message to message history
    st.session_state.messages.append({
        "role": "user",
        "content": st.session_state.pending_user_message
    })
    #Get response from bot on refresh
    with st.spinner("Generating advice..."):
        answer = bedrock_prompt_assist(st.session_state.pending_user_message)
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
    #Reset message state
    st.session_state.pending_user_message = None
    st.session_state.awaiting_response = False
    st.rerun()

if user_question:
    try:
        #Append user message and display it
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        #Show loading spinner to user
        with st.spinner("\U0001F50D Generating advice..."):
            answer = bedrock_prompt_assist(user_question)

        #Add chatbots message to message list and display it on screen
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.rerun()

    except Exception as e:
        st.error(f"\u274C Error: {str(e)}")










