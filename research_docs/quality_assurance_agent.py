from openai import OpenAI

class QualityAssuranceAgent(Agent):
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )

    def review_content(self, content, trial_data):
        # Define the prompt for quality checking
        prompt = f"""
        You are a medical expert tasked with reviewing the quality of a generated informed consent document and patient education materials. The content should be accurate, relevant, and free from hallucinations or false information. It should adhere to ethical guidelines for clinical trials.

        Below is the information about the clinical trial:
        {trial_data}

        Here is the generated content for review:
        {content}

        Please analyze the content and provide feedback on its quality, highlighting any inaccuracies, irrelevances, or violations of ethical guidelines. Return the corrections in a structured format, including examples of original text that need to be corrected, and the corrected text. Also, ensure that the content adheres to the following ethical guidelines:

        1. **Respect for Persons**: Participants should be treated as autonomous agents, and those with diminished autonomy are entitled to protection. Ensure that informed consent is obtained, and participants are provided with sufficient information to make an informed decision.
        2. **Beneficence**: The study should do no harm and maximize possible benefits while minimizing possible harms. Ensure the risks and benefits are clearly communicated to participants.
        3. **Justice**: The benefits and burdens of research should be distributed fairly. Ensure that the selection of participants is equitable and that the trial does not exploit vulnerable populations.
        4. **Confidentiality**: Ensure that participants' privacy is protected and their data is kept confidential.
        5. **Informed Consent**: Provide a clear explanation of the study, its purpose, procedures, risks, benefits, and the rights of participants, ensuring they understand and voluntarily agree to participate.

        Suggest necessary corrections in the following format:
        - **Issue**: Describe the issue with the content.
        - **Original Text**: Provide the original text that needs correction.
        - **Corrected Text**: Provide the corrected text.
        """

        completion = self.client.chat.completions.create(
            model="writer/palmyra-med-70b-32k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=True
        )

        reviewed_content = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                reviewed_content += chunk.choices[0].delta.content
        return reviewed_content

# Example usage
api_key = "your_api_key_here"
qa_agent = QualityAssuranceAgent(api_key)
generated_content = "This is an example generated content for a clinical trial."
trial_data = "Trial Name: XYZ Study\nObjective: To study the effects of ABC on DEF.\nParticipants: Adults aged 18-65 with condition GHI.\nProcedures: Blood tests, questionnaires, and interviews."
final_content = qa_agent.review_content(generated_content, trial_data)
print(final_content)
