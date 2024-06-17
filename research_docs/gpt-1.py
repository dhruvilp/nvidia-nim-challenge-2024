##############################################################################################################################
# fetch clinicalTrial data -> parse into structured data -> generate consent form -> generate edu material -> output both
##############################################################################################################################

#init model
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import requests
from dotenv import load_dotenv
import markdown2
import pdfkit

load_dotenv()

nvapi_key = os.getenv("NVIDIA_API_KEY")

llm = ChatNVIDIA(model="mistralai/mixtral-8x22b-instruct-v0.1", nvidia_api_key=nvapi_key, max_tokens=1024, temperature=0.2)
#max_tokens, temperature, top_p, stop, frequency_penalty, presence_penalty, seed

# prompt templates

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

# extract trial data
def fetch_trial_data(trial_id):
    url = f"https://clinicaltrials.gov/api/query/full_studies?expr={trial_id}&fmt=json"
    response = requests.get(url)
    data = response.json()
    # Extract relevant information
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

# generate documents
def generate_documents(trial_id):
    trial_data = fetch_trial_data(trial_id)

    consent_form_chain = consent_form_prompt | llm | StrOutputParser()
    consent_form_result = consent_form_chain.invoke({"trial_data": trial_data})

    education_content_chain = education_content_prompt | llm | StrOutputParser()
    education_content_result = education_content_chain.invoke({"trial_data": trial_data})

    return consent_form_result, education_content_result

# generate pdfs

def save_markdown_to_pdf(markdown_text, filename):
    # Convert markdown to HTML
    html_text = markdown2.markdown(markdown_text)

    # Convert HTML to PDF
    pdfkit.from_string(html_text, filename)

trial_id = "NCT04195633"
consent_form_result, education_content_result = generate_documents(trial_id)

print("\n====================================================================================================== \n")
print("Consent Form Data :\n", consent_form_result)
print("\n====================================================================================================== \n")
print("Education Material Data :\n", education_content_result)

save_markdown_to_pdf(consent_form_result, "consent_form.pdf")
save_markdown_to_pdf(education_content_result, "education_content.pdf")

print("Saved data to pdf files!")
