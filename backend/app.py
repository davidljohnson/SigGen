from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.document_loaders import TextLoader
from langchain import hub
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain.vectorstores.chroma import Chroma
from bs4 import BeautifulSoup
import requests
import re
import os
from evaluate_procedures import evaluate_procedures

app = Flask(__name__)
CORS(app)

# Load all Sigma rule documents
def load_documents_from_directory(directory):
    print("Loading documents from directory:", directory)
    documents = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
    print("Total documents loaded:", len(documents))
    return documents

def initialize_sigma_rules_components():
    print("Initializing Sigma rules components")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    sigma_rules_directory = '/app/all_sigma_rules'
    sigma_rules_docs = load_documents_from_directory(sigma_rules_directory)
    embedding = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma.from_documents(documents=sigma_rules_docs, embedding=embedding)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    prompt_chain = hub.pull("rlm/rag-prompt")
    llm = ChatOpenAI(model_name="gpt-4-1106-preview", api_key=api_key)
    return retriever, prompt_chain, llm

retriever, prompt_chain, llm = initialize_sigma_rules_components()

def format_docs(docs):
    formatted_docs = "\n\n".join(doc.page_content for doc in docs)
    print("Formatted documents for context:\n", formatted_docs)
    return formatted_docs

def is_url(procedure):
    url_pattern = re.compile(r"https?://[^\s]+")
    return url_pattern.match(procedure) is not None

def clean_website(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p')
    extracted_text = ' '.join([p.get_text() for p in paragraphs])
    print("Extracted text:\n", extracted_text)
    return evaluate_procedures(extracted_text)

sigma_rule_creation_instructions = """
<INSTRUCTIONS>
You are a cybersecurity expert creating precise and technically accurate Sigma rules, focusing on specific threat behaviors while avoiding false positives from generic activities. You will be shown a set of good Sigma rules as examples, but you have access to your entire cyber security knowledge to answer the question. You will then be asked to create a Sigma rule based on a provided set of logs or a description of an attack. Always format your output as a Sigma rule. Before starting, always make sure the provided details are specific enough to create a good Sigma rule, otherwise, say there there is not enough information. Use the additional {EVALUATION CRITERIA} to ensure the Sigma rules meet quality standards.

As you make the Sigma rule, always abide by the following instructions:
1) Make sure the rule contains event IDs when available.
2) Account for variants in the names of tools (esp. when searching the filesystem).
3) Account for potentially deceptive threat actor behavior.
4) Ensure rule is useful for real-world threat hunting.
5) Use placeholders such as <unique-id>, <author-name>, <references> and <current-date> in their respective fields
6) Assume I have only access to Windows Event logs and Windows Security logs.
</INSTRUCTIONS>

<EVALUATION CRITERIA> 
1) Does the rule address a specific, known threat or vulnerability? 
2) Can the rule be applied across different environments without modification? 
3) Have you minimized the potential for false positives and negatives? 
4) Is the rule compatible with the log sources it targets? 
5) Will this rule significantly contribute to an organization's security posture? Aim for clarity, precision, and applicability to ensure the rule adds value to security monitoring efforts.
</EVALUATION CRITERIA>
"""   

def create_prompt(input):
    context_docs = input["context"]
    question = input["question"]
    formatted_context = format_docs(context_docs)
    final_prompt = f"<Instructions>\n{sigma_rule_creation_instructions}\n<\Instructions>\n\n<Examples>\n{formatted_context}\n<\Examples>\n\n<Question>\n{question}\n<\Question>"
    print("Final prompt sent to the language model:\n", final_prompt)
    input["context"] = final_prompt
    input["question"] = question
    return input

@app.route('/api/extract_procedures', methods=['POST'])
def extract_procedures():
    print('Received request for extracting procedure.')
    data = request.json
    procedure = data.get('procedures')
    if not procedure:
        return jsonify({"error": "Procedure description is required."}), 400
    
    if is_url(procedure):
        try:
            print("Fetching URL content...")
            headers = {'User-Agent': 'Mozilla/5.0',}
            response = requests.get(procedure, headers=headers)
            response.raise_for_status()
            page_content = response.text
            print("Fetched URL content.")
            print("Extracting procedures...")
            cleaned_content = clean_website(page_content)
            procedures = evaluate_procedures(cleaned_content)
            print("Extracted procedures:", procedures)
            return jsonify({"procedures": procedures}), 200
        except requests.RequestException as e:
            print("Error fetching URL:", e)
            return jsonify({"error": f"Failed to fetch URL content: {e}"}), 500
    else:
        print("Evaluating text for procedures...")
        procedures = evaluate_procedures(procedure)
        print("Extracted procedures:", procedures)
        return jsonify({"procedures": procedures}), 200

@app.route('/api/sigma_rule', methods=['POST'])
def handle_sigma_rule_request():
    print('Received request for Sigma rule creation.')
    data = request.json
    procedure = data.get('procedure')

    rag_chain = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    ).assign(answer=create_prompt | prompt_chain | llm | StrOutputParser())

    try:
        sigma_rule = rag_chain.invoke(f"Create a Sigma rule that detects the following attack procedure: {procedure}")['answer']
        sigma_rule = sigma_rule.replace("yaml", "")
        sigma_rule = sigma_rule.replace("```\n", "")
        sigma_rule = sigma_rule.replace("```", "")
        print("Sigma rule:", sigma_rule)
        return jsonify({"sigma_rule": sigma_rule}), 200
    except Exception as e:
        print("error: ", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5050)
