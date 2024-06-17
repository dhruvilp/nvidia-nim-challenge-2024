prompt_template = """
You are a medical writer tasked with generating documents for a clinical trial. 

Below is the information about the clinical trial:
{trial_data}

Based on ONLY AND ONLY above clinical trial information, please generate the following in markdown format:

 1. **Informed Consent Document**:
    - Provide a clear and concise description of the trial.
    - Explain the purpose of the trial.
    - List the potential risks and benefits.
    - Describe the procedures involved.
    - Outline the rights of the participants.
    - Include contact information for further questions.
    - Ensure adherence to the following ethical guidelines:
        1. **Respect for Persons**: Participants should be treated with dignity and their decisions respected. Individuals with limited ability to make decisions should receive fair protection. Ensure that informed consent is obtained, and participants are provided with sufficient information to make an informed decision.
        2. **Beneficence**: The study should do no harm and maximize possible benefits while minimizing possible harms. Ensure the risks and benefits are clearly communicated to participants.
        3. **Justice**: The benefits and burdens of research should be distributed fairly. Ensure that the selection of participants is equitable and that the trial does not exploit vulnerable populations.
        4. **Confidentiality**: Ensure that participants' privacy is protected and their data is kept confidential.
        5. **Informed Consent**: Provide a clear explanation of the study, its purpose, procedures, risks, benefits, and the rights of participants, ensuring they understand and voluntarily agree to participate.


2. **Patient Education Materials**:
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


consent_prompt_template = """
Generate an informed consent document for the following clinical trial:
Trial Name: {trial_name}
Description: {trial_description}
Objectives: {trial_objectives}
Risks: {trial_risks}
Benefits: {trial_benefits}
Procedures: {trial_procedures}
Confidentiality: {trial_confidentiality}
"""

education_prompt_template = """
Create a patient education material for the following clinical trial:
Trial Name: {trial_name}
Description: {trial_description}
Objectives: {trial_objectives}
Key Points: {trial_key_points}
Frequently Asked Questions: {trial_faqs}
Contact Information: {trial_contact_info}
"""