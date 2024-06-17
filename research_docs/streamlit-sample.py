import os
import requests
from openai import OpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.memory import ConversationBufferMemory
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
nvapi_key = os.getenv("NVIDIA_API_KEY")
# llm_model = "writer/palmyra-med-70b-32k"
llm_model = "mistralai/mixtral-8x22b-instruct-v0.1"
ctgov_api_base_url = "https://clinicaltrials.gov/api/query/full_studies"

st.title("Clinical Trial Assistant")

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = nvapi_key
)

def fetch_clinical_trial_details(trial_id):
    url = f"{ctgov_api_base_url}?expr={trial_id}&min_rnk=1&max_rnk=1&fmt=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print('==== fetched clinical trial data')
        if data['FullStudiesResponse']['NStudiesFound'] > 0:
            trial_data = {
                "trial_id": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["IdentificationModule"]["NCTId"],
                "brief_trial_title": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["IdentificationModule"]["BriefTitle"],
                "official_trial_title": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["IdentificationModule"]["OfficialTitle"],
                "brief_summary": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["DescriptionModule"]["BriefSummary"],
                "detailed_description": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["DescriptionModule"]["DetailedDescription"],
                "eligibility_criteria": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["EligibilityModule"]["EligibilityCriteria"],
                "healthy_volunteers": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["EligibilityModule"]["HealthyVolunteers"],
                "gender": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["EligibilityModule"]["Gender"],
                "minimum_age": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["EligibilityModule"]["MinimumAge"],
                "contact": data['FullStudiesResponse']['FullStudies'][0]["Study"]["ProtocolSection"]["ContactsLocationsModule"]
            }
            return trial_data
        else:
            return "No study found for the given ID."
    else:
        return "Error fetching data from ClinicalTrials.gov API."

if "messages" not in st.session_state:
    st.session_state.messages = []

if "trial_details" not in st.session_state:
    st.session_state.trial_details = None


trial_id = st.text_input("Enter Clinical Trial ID:")

if trial_id and st.session_state.trial_details is None:
    trial_details = fetch_clinical_trial_details(trial_id)
    if isinstance(trial_details, dict):
        st.session_state.trial_details = trial_details
        st.session_state.messages.append(
            {"role": "system", "content": f"You are a Clinical Trial Assistant. Provide detailed responses based on the following clinical trial details: {trial_details}"}
        )
    else:
        st.error(trial_details)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is clinical trial?"):
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        messages = st.session_state.messages
        # messages = [st.session_state.messages[0]] + st.session_state.messages[1:]

        print(f'messages: {st.session_state.messages}')

        stream = client.chat.completions.create(
            model=llm_model,
            messages=messages,
            temperature=0.1,
            top_p=0.9,
            max_tokens=1024,
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})