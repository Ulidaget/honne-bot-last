import json
import os
import subprocess
import boto3
from datetime import datetime
import re
from collections import defaultdict
import streamlit as st
from moviepy.editor import VideoFileClip
import requests
import time
import uuid  # Para generar un ID único

# Define the knowledge base ID
knowledge_base_id = "7VAQT5TQYM"

# Initialize Bedrock runtime clients
bedrock_runtime = boto3.client('bedrock-runtime', 'us-east-1')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', 'us-east-1')

def get_contexts_old(query, kbId, numberOfResults=5):
    """
    Retrieves contexts for a given query from the specified knowledge base.

    Args:
        query (str): The natural language query.
        kbId (str): The knowledge base ID.
        numberOfResults (int): Number of results to retrieve (default is 5).

    Returns:
        list: A list of contexts related to the query.
    """
    # Retrieve contexts for the query from the knowledge base
    results = bedrock_agent_runtime.retrieve(
        retrievalQuery={'text': query},
        knowledgeBaseId=kbId,
        retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': numberOfResults}}
    )
    
    # Create a list to store the contexts
    contexts = [retrievedResult['content']['text'] for retrievedResult in results['retrievalResults']]
    
    return contexts

def get_contexts(query, kbId, numberOfResults=5):
    """
    Retrieves contexts for a given query from the specified knowledge base.

    Args:
        query (str): The natural language query.
        kbId (str): The knowledge base ID.
        numberOfResults (int): Number of results to retrieve (default is 5).

    Returns:
        list: A list of tuples containing contexts and their sources related to the query.
    """
    results = bedrock_agent_runtime.retrieve(
        retrievalQuery={'text': query},
        knowledgeBaseId=kbId,
        retrievalConfiguration={'vectorSearchConfiguration': {'numberOfResults': numberOfResults}}
    )
    
    contexts = [(retrievedResult['content']['text'], retrievedResult['location']['s3Location']['uri']) 
                for retrievedResult in results['retrievalResults']]
    
    return contexts

# def answer_query_old(user_input):
#     """
#     Answers a user query by retrieving context from Amazon Bedrock KnowledgeBases and calling an LLM.

#     Args:
#         user_input (str): The natural language question.

#     Returns:
#         str: The answer to the question based on context from the Knowledge Bases.
#     """
#     # Retrieve contexts for the user input from Bedrock knowledge bases
#     userContexts = get_contexts_old(user_input, knowledge_base_id)

#     # # Configure the prompt for the LLM
#     # prompt_data = """
#     # You are an AWS Solutions Architect and your responsibility is to answer user questions based on provided context.
    
#     # Here is the context to reference:
#     # <context>
#     # {context_str}
#     # </context>

#     # Referencing the context, answer the user question.
#     # <question>
#     # {query_str}
#     # </question>
#     # """
    
#      # Configure the prompt for the LLM
#     prompt_data = """
#     You are an virtual assistant and your responsibility is to answer user questions based on provided context.
    
#     Here is the context to reference:
#     <context>
#     {context_str}
#     </context>

#     Referencing the context, answer the user question.
#     <question>
#     {query_str}
#     </question>
#     """
#     formatted_prompt_data = prompt_data.format(context_str=userContexts, query_str=user_input)

#     prompt = {
#         "anthropic_version": "bedrock-2023-05-31",
#         "max_tokens": 4096,
#         "temperature": 0.5,
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": formatted_prompt_data}
#                 ]
#             }
#         ]
#     }
    
#     json_prompt = json.dumps(prompt)
#     response = bedrock_runtime.invoke_model(body=json_prompt, modelId="anthropic.claude-3-sonnet-20240229-v1:0",
#                                             accept="application/json", contentType="application/json")
#     response_body = json.loads(response.get('body').read())
#     # print(response_body)
#     answer = response_body['content'][0]['text']
    
#     return answer

# def answer_query(user_input):
#     """
#     Answers a user query by retrieving context from Amazon Bedrock KnowledgeBases and calling an LLM.

#     Args:
#         user_input (str): The natural language question.

#     Returns:
#         dict: A dictionary containing the answer and the original context information.
#     """
#     userContexts = get_contexts(user_input, knowledge_base_id)

#     context_str = "\n".join([f"Context {i+1}: {context[0]}" for i, context in enumerate(userContexts)])
#     sources = [context[1] for context in userContexts]

#     prompt_data = """
#     You are a virtual assistant and your responsibility is to answer user questions based on provided context.
    
#     Here is the context to reference:
#     <context>
#     {context_str}
#     </context>

#     Referencing the context, answer the user question. Use citation numbers in square brackets [1], [2], etc. to cite your sources within the text. The citation numbers should reflect the order in which you use them in your answer, not the order they appear in the context. Do not include the full URLs in the main text.
#     <question>
#     {query_str}
#     </question>

#     After your answer, include a "References" section listing only the reference numbers you used in your answer, without the URLs. For example:

#     References:
#     [1], [2], [3]
#     """
#     formatted_prompt_data = prompt_data.format(context_str=context_str, query_str=user_input)

#     prompt = {
#         "anthropic_version": "bedrock-2023-05-31",
#         "max_tokens": 4096,
#         "temperature": 0.5,
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": formatted_prompt_data}
#                 ]
#             }
#         ]
#     }
    
#     json_prompt = json.dumps(prompt)
#     response = bedrock_runtime.invoke_model(body=json_prompt, modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
#                                             accept="application/json", contentType="application/json")
#     response_body = json.loads(response.get('body').read())
#     answer = response_body['content'][0]['text']
    
#     return {"answer": answer, "sources": sources}

def format_answer(response):
    """
    Formats the answer to ensure references are properly numbered and displayed.

    Args:
        response (dict): A dictionary containing the answer and source information.

    Returns:
        str: The formatted answer with proper References section, including correctly numbered references.
    """
    answer = response["answer"]
    sources = response["sources"]
    
    # Split the answer into main content and references
    parts = re.split(r'\n(?:References|Referencias):\s*\n', answer, flags=re.IGNORECASE)
    
    if len(parts) == 2:
        main_content, _ = parts
        
        # Find all reference numbers used in the main content
        used_refs = re.findall(r'\[(\d+)\]', main_content)
        
        # Create a mapping of old reference numbers to new ones
        ref_map = {old: str(i+1) for i, old in enumerate(dict.fromkeys(used_refs))}
        
        # Replace old reference numbers with new ones in the main content
        for old, new in ref_map.items():
            main_content = main_content.replace(f'[{old}]', f'[{new}]')
        
        # Create the new references section
        new_references = []
        for i, ref_num in enumerate(ref_map.values()):
            if i < len(sources):
                new_references.append(f"[{ref_num}] {sources[i]}\n")
        
        formatted_references_str = '\n'.join(new_references)
        
        if formatted_references_str:
            return f"{main_content.strip()}\n\nReferencias:\n\n{formatted_references_str}"
        else:
            return main_content.strip()  # Return only main content if no references were used
    else:
        return answer  # Return as is if no References section is found

def answer_query(user_input, conversation_history):
    """
    Answers a user query while maintaining conversation context
    """
    userContexts = get_contexts(user_input, knowledge_base_id)
    context_str = "\n".join([f"Context {i+1}: {context[0]}" for i, context in enumerate(userContexts)])
    sources = [context[1] for context in userContexts]

    # Create a conversation history string
    history_str = ""
    for msg in conversation_history:
        role = "Human" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    prompt_data = """
    You are a virtual assistant and your responsibility is to answer user questions based on provided context and previous conversation history.
    
    Previous conversation history:
    {history_str}
    
    Here is the reference context:
    <context>
    {context_str}
    </context>

    Using both the conversation history and reference context, answer the user's question. 
    Make sure to maintain consistency with previous responses and reference relevant parts of the conversation history when appropriate.
    Use citation numbers in square brackets [1], [2], etc. to cite your sources within the text.

    <question>
    {query_str}
    </question>

    After your answer, include a "References" section listing only the reference numbers you used in your answer.
    """
    
    formatted_prompt_data = prompt_data.format(
        history_str=history_str,
        context_str=context_str, 
        query_str=user_input
    )

    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": formatted_prompt_data}
                ]
            }
        ]
    }
    
    json_prompt = json.dumps(prompt)
    response = bedrock_runtime.invoke_model(
        body=json_prompt, 
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        accept="application/json", 
        contentType="application/json"
    )
    response_body = json.loads(response.get('body').read())
    answer = response_body['content'][0]['text']
    
    return {"answer": answer, "sources": sources}

def answer_query_old(user_input, conversation_history):
    """
    Legacy version with conversation history support
    """
    userContexts = get_contexts_old(user_input, knowledge_base_id)
    
    history_str = ""
    for msg in conversation_history:
        role = "Human" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"

    prompt_data = """
    You are a virtual assistant and your responsibility is to answer user questions based on provided context and previous conversation history.
    
    Previous conversation history:
    {history_str}
    
    Here is the context to reference:
    <context>
    {context_str}
    </context>

    Using both the conversation history and reference context, answer the user's question.
    Make sure to maintain consistency with previous responses.
    
    <question>
    {query_str}
    </question>
    """
    
    formatted_prompt_data = prompt_data.format(
        history_str=history_str,
        context_str=userContexts, 
        query_str=user_input
    )

    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": formatted_prompt_data}
                ]
            }
        ]
    }
    
    json_prompt = json.dumps(prompt)
    response = bedrock_runtime.invoke_model(
        body=json_prompt, 
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        accept="application/json", 
        contentType="application/json"
    )
    response_body = json.loads(response.get('body').read())
    answer = response_body['content'][0]['text']
    
    return answer

def process_invoice_with_claude(image_base64):
    sent_prompt = """Please exctract data from this invoice and format this data in JSON document.
    Please use camel case format for the keys in the JSON document.
    Please namethe keys and values in its original language.
    For example, if there is a customer name and the docuemnt is written in spanish, this value should be called nombreCliente and not customerName.
    For any detected address field, please combine any multi-line address into a single line separated by comas."""
    
    request_body ={
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.5,
        "top_p":0.5,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": sent_prompt
                    },
                    {
                        "type":"image",
                        "source":{
                            "type":"base64",
                            "media_type":"image/jpeg",
                            "data": image_base64
                        },
                    },
                ]
            }
        ]
        
    }
    response = bedrock_runtime.invoke_model(
        body=json.dumps(request_body), 
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
   
    )
    response_body = json.loads(response.get('body').read())
    input_tokens = response_body["usage"]["input_tokens"]
    output_tokens = response_body["usage"]["output_tokens"]
    
    print(f' - Numero de tokens de entrada: {input_tokens}')
    print(f' - Numero de tokens de salida: {output_tokens}')
    answer = response_body['content'][0]['text']
    # answer = response_body.get("content",[])

    return answer

def convert_video_to_audio_and_upload(video_path, bucket_name):
    # Extraer el audio del video usando moviepy
    audio_path = "temp_audio.wav"
    with VideoFileClip(video_path) as video:
        video.audio.write_audiofile(audio_path)

    # Subir el archivo de audio a S3
    s3_client = boto3.client('s3')
    s3_client.upload_file(audio_path, bucket_name, "temp_audio.wav")
    audio_s3_uri = f"s3://{bucket_name}/temp_audio.wav"
    return audio_s3_uri

def transcribe_audio(audio_s3_uri):
    # Configuración de cliente para AWS Transcribe
    transcribe = boto3.client('transcribe',region_name='us-east-1')
    
    # Generar un nombre único para el trabajo de transcripción
    job_name = f"transcription-job-{uuid.uuid4()}"
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': audio_s3_uri},
        MediaFormat='wav',
        LanguageCode='es-ES'
    )

    # Esperar a que termine el trabajo
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(5)  # Esperar 5 segundos antes de chequear nuevamente

    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        # Obtener el texto transcrito
        response = requests.get(status['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        transcript = response.json()['results']['transcripts'][0]['transcript']
        return transcript
    return None

def extract_keywords_with_claude(text):
    prompt = """Extrae las palabras clave del siguiente texto en español, formateadas como una lista:
    {text}"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 250,
        "temperature": 0.5,
        "top_p": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt.format(text=text)}]
            }
        ]
    }
    
    response = bedrock_runtime.invoke_model(
        body=json.dumps(request_body), 
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
    )
    response_body = json.loads(response.get('body').read())
    keywords = response_body['content'][0]['text']
    return keywords

def summarize_text_with_claude(text):
    prompt = """Por favor, genera un resumen conciso del siguiente texto en español:
    {text}"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.5,
        "top_p": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt.format(text=text)}]
            }
        ]
    }

    response = bedrock_runtime.invoke_model(
        body=json.dumps(request_body),
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
    )
    response_body = json.loads(response.get('body').read())
    summary = response_body['content'][0]['text']
    return summary

