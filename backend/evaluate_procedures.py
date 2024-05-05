import anthropic
import json
from tqdm import tqdm
import os

api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key is None:
    raise ValueError("The ANTHROPIC_API_KEY environment variable is not set")

client = anthropic.Anthropic(api_key=api_key)

evaluations = []

def evaluate_procedures(procedure):
    evaluations = []
    first_step_message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=2000,
        temperature=0,
        system="Extract one or two of the most significant attack behaviors detected in the text. Always include as much technical detail from the text that would be helpful for threat hunting and would help with detection rule generation. Output your response as a JSON object only, with the keys \"techniques\", \"description\". Make sure to include as much detail as possible for each procedure to assist with Sigma rule generation. Use only the information provided in your response. Write the procedure in active voice.\n\n<RESPONSE TEMPLATE>\n{\n    \"procedures\":\n    {\n        \"techniques\": string (e.g., \"Acquire Infrastructure: Domains (T1583.001), Masquerading: Match Legitimate Name or Location (T1036.005)\")\n        \"description\": string (e.g., \"The threat actor ITG05 staged payloads for their operations on the freely available hosting provider firstcloudit[.]com. The payloads included the malware MASEPIE, OCEANMAP, and STEELHOOK, which are designed to exfiltrate files, execute arbitrary commands, and steal browser data from the victim's machine. If no procedures are detected return an empty JSON object.\"\n    },\n    {\n        \"techniques\": string,\n        \"description\": string\n    },\n}\n</RESPONSE TEMPLATE>",
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": procedure}]
        }]
    )

    try:
        json_step1_response = json.loads(first_step_message.content[0].text)
        print('Step 1 Response: {}'.format(json_step1_response))
        if 'procedures' in json_step1_response and json_step1_response['procedures']:
            procedures_to_evaluate = json_step1_response['procedures']
        else:
            print("No procedures detected. Skipping evaluation.")
            return
    except json.JSONDecodeError:
        print("Error parsing JSON from Step 1 response. Skipping evaluation.")
        return

    for procedure_object in procedures_to_evaluate:
        print(f"Procedure Object: {procedure_object}")
        print(f"Evaluating: {procedure_object['description']}")
        second_step_message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0,
            system="For the provided attack procedure, conduct the following quality checks. Your output should be entirely in JSON. Evaluate and score the procedure based on the criteria provided, using a scale of 1 to 10:\n1. Does the procedure include enough context for a detection engineer to write an effective Sigma rule?\n2. Does the procedure address how the threat actor used a specific technique so that it can be emulated in a lab environment?\n3. Does the procedure include context-specific details that differentiate it from benign activities, minimizing false positives?\n4. Is the log data needed to detect the described procedure readily accessible and commonly collected in typical security environments?\n5. If the procedure mentions named malware, does it also describe in detail how the malware performs the technique?\n\nCalculate the average score across all these procedure based on these quality checks. Your response will only include a JSON object with the keys \"quality_score\" and \"analysis\". The analysis should be less than 4 sentences. Use the following template for your response:\n\n<RESPONSE TEMPLATE>\n{\n    \"technique\": {TECHNIQUE}\n    \"description\": {PROCEDURE},\n    \"quality_score\": {AVERAGE SCORE (in double quotes)},\n    \"analysis\": {EXPLANATION}\n}\n</RESPONSE TEMPLATE>\n",
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": json.dumps(procedure_object)}]
            }]
        )

        try:
            response_json = json.loads(second_step_message.content[0].text)
            evaluations.append(response_json)
        except json.JSONDecodeError:
            print("Error parsing JSON response for a procedure.")
 
    return json.dumps(evaluations)