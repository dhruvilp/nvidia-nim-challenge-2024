import os
import json
import requests
import markdown2
import pdfkit
import streamlit as st
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.tools import Tool
from langchain.schema import SystemMessage
import base64

load_dotenv()

# Load environment variables
nvapi_key = os.getenv("NVIDIA_API_KEY")
ctgov_api_base_url = "https://clinicaltrials.gov/api/query/full_studies"
llm_model = "mistralai/mixtral-8x22b-instruct-v0.1"
# llm_model = "microsoft/phi-3-mini-128k-instruct"

# Initialize NVIDIA ChatNVIDIA model
llm = ChatNVIDIA(model=llm_model, nvidia_api_key=nvapi_key, max_tokens=1024, temperature=0.2)

#######################################################

patient_data = {}
with open('gen_patient_data.json', 'r') as file:
    patient_data = json.load(file)

system_message = SystemMessage(
    content="""You are a world class researcher, who can do detailed research on any topic.

        Please make sure you complete the objective above with the following rules:
        1/ Your job is to first breakdown the topic into relevant questions for understanding the topic in detail. You should have at max only 3 questions not more than that, in case there are more than 3 questions consider only the first 3 questions and ignore the others.
        2/ You should use the search tool to get more information about the topic. You are allowed to use the search tool only 3 times in this process.    
        3/ Aggregate all the resources or urls that you can get on this topic.
        4/ Use the provide scrape tool to scrape through your aggregrated list of urls one by one.

        Your task is complete once you answer all the user queries.
        """
)

# Templates for generating consent form and education content
consent_form_template = """
You are a medical writer tasked with generating documents for a clinical trial. 

Below is the information about the clinical trial:
{trial_data}

Based on ONLY AND ONLY above clinical trial information, please generate the following in markdown format:

 1. **Informed Consent Document**:
    - Provide a clear and concise description of the trial.
    - Explain the purpose of the trial.
    - List the potential risks (ex: general, side effects, and drug risks) and benefits.
    - Describe how patient's medical information will be shared and with whom
    - Describe the procedures involved.
    - Outline the rights of the participants.
    - Include contact information for further questions.
    - Ensure adherence to the following ethical guidelines:
        1. **Respect for Persons**: Participants should be treated with dignity and their decisions respected. Individuals with limited ability to make decisions should receive fair protection. Ensure that informed consent is obtained, and participants are provided with sufficient information to make an informed decision.
        2. **Beneficence**: The study should do no harm and maximize possible benefits while minimizing possible harms. Ensure the risks and benefits are clearly communicated to participants.
        3. **Justice**: The benefits and burdens of research should be distributed fairly. Ensure that the selection of participants is equitable and that the trial does not exploit vulnerable populations.
        4. **Confidentiality**: Ensure that participants' privacy is protected and their data is kept confidential.
        5. **Informed Consent**: Provide a clear explanation of the study, its purpose, procedures, risks, benefits, and the rights of participants, ensuring they understand and voluntarily agree to participate.
    - Add "My signature agreeing to take part in the study" section at the end:
        - "I have read this consent form or had it read to me. I have discussed it with the study doctor and my questions have been answered. I will be given a signed and dated copy of this form. I agree to take part in the main study"
    - Ask for patient's signature and date at the end
                 
Ensure the language is accessible, accurate, and appropriate for the target audience. Make sure to follow ethical guidelines and maintain a professional tone.
"""

education_content_template = """
You are a medical writer tasked with generating documents for a clinical trial. 

Below is the information about the clinical trial:
{trial_data}

Based on ONLY AND ONLY above clinical trial information, please generate the following in markdown format:

1. **Patient Education Materials**:
    - **Introduction**: Provide a brief introduction to the trial, including its name, purpose, and importance.
    - **Trial Overview**: Summarize the trial in simple, non-technical language.
    - **Purpose and Importance**:
        - Explain why this trial is being conducted and its potential impact.
        - Highlight the significance of the trial in advancing medical knowledge or treatment.
    - **Participant Experience**:
        - Describe what participants can expect during the trial.
        - Detail the procedures, frequency of visits, and any special instructions.
    - **Potential Benefits and Risks**:
        - Clearly outline the potential benefits of participating.
        - Describe any possible risks or side effects in an honest but reassuring manner.
    - **Engagement and Support**:
        - Offer tips for participants on what to expect during the trial.
        - Provide information on resources or support available to participants, such as contact details for trial coordinators or support groups.
    - **Testimonials or Case Studies**:
        - Include engaging stories or testimonials from previous participants (real or hypothetical) to illustrate the potential positive outcomes. If stories or testimonials are hypothetical, then you MUST inform the user.
    - **Visual Aids**:
        - Use diagrams, infographics, or illustrations to explain complex concepts. Call the `fetch_visual_aids` method to retrieve relevant visual aids.
    - **Frequently Asked Questions (FAQs)**:
        - Generate FAQs based on the most probable questions that most people might have or questions that have not been covered in the education material yet. Ensure that the FAQs address common concerns and provide clear, concise answers.
    - **Call to Action**:
        - Encourage participants to contact the trial team with any questions and provide clear instructions on how to get involved.
               
Ensure the language is accessible, accurate, and appropriate for the target audience. Make sure to follow ethical guidelines and maintain a professional tone.
"""

consent_form_prompt = ChatPromptTemplate.from_template(consent_form_template)
education_content_prompt = ChatPromptTemplate.from_template(education_content_template)

#######################################################

# Function to fetch trial data from ClinicalTrials.gov API
def fetch_trial_data(trial_id):
    url = f"{ctgov_api_base_url}?expr={trial_id}&min_rnk=1&max_rnk=1&fmt=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
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

#######################################################

# Function to generate consent form and education content
def generate_documents(trial_data):

    consent_form_chain = consent_form_prompt | llm | StrOutputParser()
    consent_form_result = consent_form_chain.invoke({"trial_data": trial_data})
    consent_pdf_filename = "consent_form.pdf"
    save_markdown_to_pdf(consent_form_result, consent_pdf_filename)

    education_content_chain = education_content_prompt | llm | StrOutputParser()
    education_content_result = education_content_chain.invoke({"trial_data": trial_data})
    education_pdf_filename = "education_content.pdf"
    save_markdown_to_pdf(education_content_result, education_pdf_filename)

    return consent_pdf_filename, education_pdf_filename

#######################################################

# Function to save markdown as PDF
def save_markdown_to_pdf(markdown_text, filename):
    html_text = markdown2.markdown(markdown_text)
    pdfkit.from_string(html_text, filename)

#######################################################

# Streamlit application setup
st.title("Clinical Trial Assistant")


# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "trial_details" not in st.session_state:
    st.session_state.trial_details = None

if "patient_data" not in st.session_state:
    st.session_state.patient_data = patient_data

# Main streamlit logic
trial_id = st.text_input("Enter Clinical Trial ID:")

# Disable Generate PDFs button until trial_id has a valid value
if trial_id and st.button("Generate PDFs"):
    with st.spinner("Collecting trial data..."):
        trial_details = fetch_trial_data(trial_id)
        if isinstance(trial_details, dict):
            st.session_state.trial_details = trial_details
            st.session_state.messages.append(
                {"role": "system", "content": f"You are a Clinical Trial Assistant. Provide detailed responses based on the following clinical trial details: {trial_details}"}
            )
            consent_pdf_filename, education_pdf_filename = generate_documents(trial_details)
            st.success("Generated PDF files!")
        else:
            st.error("Something went wrong while generating pdf documents")

def get_download_link(file_bytes, file_name):
    b64 = base64.b64encode(file_bytes).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Download {file_name}</a>'

if "consent_pdf_filename" in locals():
    consent_pdf_bytes = open(consent_pdf_filename, "rb").read()
    st.markdown(get_download_link(consent_pdf_bytes, "Consent-Form.pdf"), unsafe_allow_html=True)

if "education_pdf_filename" in locals():
    education_pdf_bytes = open(education_pdf_filename, "rb").read()
    st.markdown(get_download_link(education_pdf_bytes, "Education-Materials.pdf"), unsafe_allow_html=True)

#######################################################

def load_trial_data(query):
    return st.session_state.trial_details

def load_patient_data(query):
    return st.session_state.patient_data

patient_data_retrieval_tool = Tool(
    name="search",
    func=load_patient_data,
    description="useful for when you need to answer questions about patient's personal health data including medical history and current conditions"
)

trial_data_tool = Tool(
    name="search",
    func=load_trial_data,
    description="useful for when you need to answer questions about clinical trials"
)

#######################################################

llm = ChatNVIDIA(model=llm_model, nvidia_api_key=nvapi_key, max_tokens=1024, temperature=0.2)

tools = [trial_data_tool, patient_data_retrieval_tool]

agent_kwargs = {
    "system_message": system_message,
    "handle_parsing_errors": True
}

agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True,
    agent_kwargs=agent_kwargs,
)

if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent.run(prompt, callbacks=[st_callback])
        st.write(response)