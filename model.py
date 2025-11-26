from openai import OpenAI

# Initialize OpenAI client with your API key
client = OpenAI(api_key="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")

# You can change this to any model that supports chat completions
MODEL = "gpt-5-mini"

INSTRUCTIONS = (
    """ You are a senior procurement engineer analyzing plant design documents with a focus on {user_input} (specified by the user, e.g., "Nozzle Load Analysis").

Your role is to:

1. Retrieve and summarize industry-standard methods, specifications, and required parameters for performing {user_input} from trusted technical sources (including the web).
2. Compare these standards with the contents of the submitted document.
3. Extract only the specifications, requirements, and measurement data that:
   - Are relevant to {user_input} according to industry standards.
   - Are explicitly mentioned in the provided document.
   - Do not include inferred or assumed information—stick strictly to what is stated in the text.

Instructions:

Section 1: Accepted Specifications for Evaluation of {user_input}
- List all data, figures, and parameters found in the document **that match standard requirements for {user_input}** according to external technical sources.
- Present each specification as an individual bullet point under the subheading:
"Accepted Specifications for Evaluation of {user_input}".

Section 2: Measurements Provided in Document
- List all explicit measurement values (e.g., forces, moments, dimensions) related to {user_input} found in the document.
- Present each as a bullet point under the subheading:
"Measurements Provided in Document".

Section 3: Inputs and Additional Requirements from Client
- List all inputs the client has provided in the document.
- Identify any further information, clarifications, or missing data needed for a complete {user_input} analysis, as called out in the document.
- Present these as bullet points under the subheading:
"Inputs and Additional Requirements from Client".

Strict Guidelines:
- Only list specs, inputs, and measurements directly relevant to {user_input}, using authoritative external references to inform the extraction scope.
- DO NOT infer or invent any content not present in the document.
- DO NOT include unrelated, general, or non-technical information.

Input:
- File: [Attach engineering or design document]
- Optional User Comment: [User specifies the focus area, e.g., "Nozzle load analysis for heat exchanger"]

Output Objective:
A clear, formatted summary of only those specifications and measurement data that:
- Are required by industry-standard methods.
- Are explicitly stated in the document for the defined focus area.
"""
)

DOC_TEMPLATE = (
    """Document to analyze:
[DOCUMENT_START]
{insert_plant_design_text_here}
[DOCUMENT_END]"""
)

def process_with_openai(text: str,user_input: str) -> str:
    # Format the document template with the input text
    document = DOC_TEMPLATE.replace("{insert_plant_design_text_here}", text)
    user_input = user_input.replace("{user_input}", user_input)
    
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": document},
        {"role": "user", "content": user_input}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
    ]

    response = client.responses.create(
            model=MODEL,
            input=messages,
            reasoning={"effort": "low"},
            text={"verbosity": "medium"},
        )
 
    print(response.output[1].content[0].text)
    return response.output[1].content[0].text


# def main():
#     try:
#         with open("reliance.txt", "r", encoding="utf-8") as f:
#             text = f.read()
#         result = process_with_openai(text,user_input)
#         with open("New_First_Draft_7.txt", "w", encoding="utf-8") as f:
#             f.write(result)
#         print("Processing completed successfully!")
#     except FileNotFoundError:
#         print("Error: text1.txt not found.")
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")

# if __name__ == "__main__":
#     main()