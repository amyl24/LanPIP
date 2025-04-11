from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import os
import anthropic
from llamaapi import LlamaAPI
from openai import OpenAI
from PIL import Image
import requests
from bots import reasoning, vocab
import json
import re

# Initialize
api_key = "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"
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI(api_key="sk-e0f6e484e9c7437cbaf34ff062631b6d", base_url="https://api.deepseek.com")



with open('aggregated_meta_prompt.json','r' ) as file:
    data = json.load(file)

def stage_classification(user_input):
    message = [{"role": "system",
                "content": '''Analyze the user's input to identify their current stage in the writing process and only output the name of stages. If the user's input does not clearly match any of these stages, output 'NOT APPLIED'.
                        Based on the user's response, look for keywords and phrases that indicate their current stage:
                        Pre-task (Task assignment):
                        Keywords: "need a topic," "don't know what to write about," "looking for a prompt," "need a writing task"
                        If the user's input suggests they need a writing task or prompt, provide them with a suitable topic or task to start the writing process.
                        Pre-task (Topic introduction):
                        Keywords: "need more information," "don't have enough background," "want to learn more about the topic," "need ideas"
                        If the user's input indicates a need for topic introduction, guide them through activities to activate background knowledge, generate interest, and brainstorm ideas.
                        Pre-task (Language input):
                        Keywords: "don't know the right words," "need help with vocabulary," "struggling with grammar," "need phrases for the topic"
                        If the user's input suggests a need for language input, provide them with key vocabulary, phrases, grammatical structures, and language reference materials relevant to the writing task.
                        Task cycle (Drafting):
                        Keywords: "started writing," "working on my draft," "need help organizing my ideas," "not sure if I'm on the right track"
                        If the user's input indicates they are in the drafting stage, offer guidance on content organization, purpose, and audience. Encourage them to focus on communicating meaning and provide tools to support the drafting process.
                        Post-task (Reflection):
                        Keywords: "finished my draft," "want to reflect on my writing," "need to evaluate my work," "not sure what I did well or need to improve"
                        If the user's input suggests they have completed a draft and are ready for reflection, guide them through self-assessment and reflection activities to identify strengths and areas for improvement.
                        Post-task (Language-focused activities):
                        Keywords: "need to fix my grammar," "want to improve my vocabulary," "need help with sentence structure," "made some mistakes in my writing"
                        If the user's input indicates a need for language-focused activities, provide targeted grammar exercises, vocabulary practice, or sentence-level writing tasks to address specific linguistic challenges identified in their writing.
                        '''},
               {"role": "user", "content": user_input}]
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=message,
        stream=False
    )
    stage = completion.choices[0].message.content
    if "Pre-task (Task assignment)" and "Pre-task (Topic introduction)" in stage:
        return 0
    elif "Pre-task (Language input)" in stage:
        return 1
    elif "Task cycle (Drafting)" in stage:
        return 2
    else:
        return 3

def writing_extractor(user_input):
    system_message = ('''User has inputted his writing or writing draft and his following request. Please extract the writing or draft itself from user's input.
                        Only output the writing or draft itself.''')
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":user_input},
                 {"role":"system","content":system_message}],
        stream=False
    )
    return completion.choices[0].message.content

def chat_assessment_with_model_generator(prompt, cus_prompt):
    system_message = ("Ask for input if user did not enter a writing."
                      f"Then, Evaluate student writing based on ETS Rubrics and provide a score. "
                      "If it is integrated writing, grade the writing with following rubrics"
                      "Score 5: Successfully selects and coherently presents important information from the lecture in relation to the reading. The response is well-organized with only occasional language errors that do not hinder accuracy or clarity."
                      "Score 4: Good at selecting and presenting important lecture information in relation to the reading but may have minor inaccuracies or imprecisions. Minor language errors are more frequent but do not significantly affect clarity."
                      "Score 3: Contains some important information from the lecture and some relevant connections to the reading but may be vague, imprecise, or contain one major omission. Frequent errors may obscure meanings or connections."
                      "Score 2: Contains relevant information from the lecture but has significant language difficulties or inaccuracies in conveying important ideas or connections. Errors likely obscure key points for readers unfamiliar with the topics."
                      "Score 1: Provides little to no meaningful content from the lecture, with very low language level making it difficult to derive meaning."
                      "Score 0: Merely copies sentences from the reading, off-topic, written in a foreign language, consists of keystroke characters, or is blank."
                      "If it is academic discussion,grade the writing with following rubrics"
                      "Score 5: Relevant and clearly expressed contribution with consistent facility in language use, showcasing relevant explanations, effective syntactic variety, precise word choice, and almost no errors."
                      "Score 4: Relevant contribution that is easily understood, displaying adequate elaboration, syntactic variety, appropriate word choice, and few lexical or grammatical errors."
                      "Score 3: Mostly relevant and understandable contribution with some facility in language use. Some parts may be missing, unclear, or irrelevant, with noticeable lexical and grammatical errors."
                      "Score 2: Attempt to contribute with limited language use making ideas hard to follow, limited syntactic and vocabulary range, and an accumulation of structural and lexical errors."
                      "Score 1: Ineffective attempt with severely limited language use preventing expression of ideas. Few coherent ideas, with any coherent language mostly borrowed."
                      "Score 0: Blank, off-topic, not in English, entirely copied, unconnected to the prompt, or consists of arbitrary keystrokes."
                      "Only output the score of the writing.")

    if cus_prompt is None:
        system_message = system_message
    else:
        cus_prompt = str(cus_prompt)
        system_message = 'User information: ' + cus_prompt + 'Task for you: ' + system_message

    try:
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        score = chat_completion.choices[0].message.content.strip()
        return score
    except Exception as e:
        return f"An error occurred with GPT-4: {e}"

def topic_classify(prompt):
    system_message = ('''Please analyze the user's input to identify the topic of the user's input and only output the keyword of the topic. If the user's input can not be concluded into a topic, output'NOT APPLIED'.
                    based on the user's input, look for keywords that indicate their topic. For example, if the user's input contains words like: travel plan, desitination, then the topic of the input may be 'travel'.''')
    chat_completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    return chat_completion.choices[0].message.content.strip()

def final_generator_pre(user_input, cus_prompt,v_or_v_c,topic):
    stage = "Pre-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
    system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing. 
    The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
    Output the topic of the writing before instruction: {topic}.{aggregated_meta_prompt}.Regarding validity of the raw generation and the original question, here are some important comments: {v_or_v_c}
    You need to point out logical or scientific-unproven problems of user_input in the output if there is any according to the comments''')
    chat_completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input},
        ],
        stream=False
    )
    return chat_completion.choices[0].message.content.strip()

def final_generator_pre_2(user_input, cus_prompt,topic):
    stage = "Pre-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
    system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing. 
    The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
    Output the topic of the writing before instruction: {topic}.{aggregated_meta_prompt}.''')
    chat_completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input},
        ],
        stream=False
    )
    return chat_completion.choices[0].message.content.strip()

def final_generator_vocab(user_input, cus_prompt, v_or_v_c,word_info,topic):
    stage = "Pre-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
        system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing by providing word information: {word_info}. 
                        The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
                         Output the topic of the writing before instruction: {topic}.{aggregated_meta_prompt}.Regarding validity of the raw generation and the original question, here are some important comments: {v_or_v_c}
                         You need to point out logical or scientific-unproven problems of user_input in the output if there is any according to the comments''')
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            stream=False
        )
        return chat_completion.choices[0].message.content.strip()

def final_generator_vocab_2(user_input, cus_prompt,word_info,topic):
    stage = "Pre-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
        system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing by providing word information: {word_info}. 
                        The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
                         Output the topic of the writing before instruction: {topic}.{aggregated_meta_prompt}.''')
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            stream=False
        )
        return chat_completion.choices[0].message.content.strip()

def final_generator_during(user_input, cus_prompt, v_or_v_c, assessment, topic):
    writing = writing_extractor(user_input)
    stage = "During-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
        system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing. 
                The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
                Here is the draft from user:{writing}
                Output the topic of the writing before instruction: {topic}.
                Output the score of the writing{assessment}.
                 {aggregated_meta_prompt}.
               Regarding validity of the raw generation and the original question, here are some important comments: {v_or_v_c}
               You need to point out logical or scientific-unproven problems of user_input in the output if there is any according to the comments''')
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            stream=False
        )
        return chat_completion.choices[0].message.content.strip()

def final_generator_during_2(user_input, cus_prompt, assessment, topic):
    writing = writing_extractor(user_input)
    stage = "During-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
        system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing. 
                The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
                Here is the draft from user:{writing}
                Output the topic of the writing before instruction: {topic}.
                Output the score of the writing{assessment}.
                 {aggregated_meta_prompt}.''')
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            stream=False
        )
        return chat_completion.choices[0].message.content.strip()

def final_generator_post(user_input, cus_prompt, v_or_v_c, assessment, topic):
    writing = writing_extractor(user_input)
    stage = "Post-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
        system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing. 
                    The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
                    Here is the writing:{writing}
                    Output the topic of the writing before instruction:{topic}.
                    Output the score of the writing{assessment}.
                    {aggregated_meta_prompt}.
                    Regarding validity of the raw generation and the original question, here are some important comments: {v_or_v_c}
                    You need to point out logical or scientific-unproven problems of user_input in the output if there is any according to the comments''')
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            stream=False
        )
        return chat_completion.choices[0].message.content.strip()

def final_generator_post_2(user_input, cus_prompt, assessment, topic):
    writing = writing_extractor(user_input)
    stage = "Post-Task Stage"
    aggregated_meta_prompt = None
    for stage_data in data["aggregated_meta_prompt"]:
        if stage_data["stage"] == stage:
            aggregated_meta_prompt = stage_data[f"{stage}_prompt"]
            return aggregated_meta_prompt
        system_message = (f'''You are an encouraging teacher and you are about to give some writing advice or instruction according to user's request or writing. 
                    The user profile is {cus_prompt}.Please consider user's information and give advice based on the user profile.
                    Here is the writing:{writing}
                    Output the topic of the writing before instruction:{topic}.
                    Output the score of the writing{assessment}.
                    {aggregated_meta_prompt}.''')
        chat_completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input},
            ],
            stream=False
        )
        return chat_completion.choices[0].message.content.strip()

def final_generator(user_input,word_info):
    system_message = ('You are a professional writing tutor with multi-dimensional analysis capabilities. Process user input following this workflow: '
                      '**Step 1: Input Preprocessing**'
                      '1. Detect if input contains draft writing:'
                      '- If detecting "<Writing Start>" markers or continuous text >100 words:'
                      '- Analyze user input and output the writing text only'
                      '- Preserve additional guidance requests'
                      '**Step 2: Meta-Cognitive Analysis**'
                      '2. [Stage Diagnosis] Analyze user input and determine which stage is user input in :'
                          '- Scan keywords for writing stage priority:'
                          '1. Pre-task (Task assignment): "need topic/do not know what to write'
                          "2. Pre-task (Topic intro): need info/background"
                          "3. Pre-task (Language input): vocab/grammar/phrase."
                          "4. Task cycle (Drafting): started writing/organizing ideas"
                          "5. Post-task (Reflection): finished draft/evaluate"
                          '6. Post-task (Language focus): fix grammar/improve vocab in writing'
                      '3. [Topic Anchoring] :based on the user input, look for keywords that indicate their topic and then identify the topic of user input'
                      '- Extract 3 core topic keywords (TF-IDF weighted)'
                      '- Mark "NOT APPLIED" if no clear topic'
                      '**Step 4: Dynamic Response Generation**'
                      'Select response mode based on analysis:'
                      'A. **Writing Assessment Mode** (Only apply when during-task and Post-task stage and when draft detected):'
                      '1. Identify writing type (Academic Discussion/Integrated)'
                      '2. Apply ETS rubrics:'
                      '- Integrated: Check lecture integration & language accuracy'
                      '- Academic: Evaluate argument relevance & language complexity'
                      '3. Output integer score 1-5 (0 for special cases)'
                      'B. **Stage Guidance Mode** (according to different stages):'
                      '- **Pre-Task**:'
                      '1. Build topic context (using extracted keywords)'
                      '2. Provide tiered language support (basic→advanced)'
                      '3. Output 3 heuristic writing tasks'
                      f'4. When comes to language support problems, using word information as background knowledge:{word_info}'
                      '- **During-Task**:'
                      '1. Apply ABT analysis (Action-Background-Twist)'
                      '2. Provide visual mindmap framework'
                      '3. Embed dynamic grammar checks'
                      '- **Post-Task**:'
                      '1. Generate dual-asessment matrix (content/language)'
                      '2. Create error pattern heatmap'
                      '3. Design progressive improvement plan'
                      'C.  Cognitive Demand Assessment'
                            'Some critical message you need to consider when responding to user request, which is validity comment and critical instructions'
                            '4. validity comment:'
                            '- According to user input determine whether the response is proven by science or facts'
                            '- reconsider the response'
                            '5. [Answer Nature] critical instruction:'
                            'judge whether the response follows logical reasoning by 3 steps'
                            '1. being an educator to complete sentence of user input. Offer a detailed and comprehensive background how to complete the sentence。Present your explanations with clarity, accuracy, and structure, ensuring they are accessible to a diverse audience.'
                            '2. You are a critical professor to address all deficiencies of this raw draft(output from step 1).Carefully read and interpret the inquiry.Break down the task step by step. Synthesize your observations and reasoning into a coherent argument.Integrate your findings and reasoning into a clear, concise final answer.'
                            '3. According to the content from educator(step1) and comments from critical professor(step2), You are an meta-reviewer and your task is consider both instructions to complete the sentence. follow the steps. '
                                'Step 1: Identify the facts that more than half of the answers agree upon.'
                                'Step 2: Identify the facts that conflict among the answers.'
                                'Step 3: Resolve the conflicting facts.'
                                'Step 4: Identify unique facts mentioned only in one answer.'
                                'Step 5: Combine the facts from Steps 1, 3, and 4.'
                                'Step 6: Complete the sentence with an objective tone.'
                      '**step 5: final response generation**'
                      'Generate the final response following the steps below:'
                      '1.confirm the stage of the user input in [stage diagnosis]'
                      '2.determine the topic of the user input in [topic anchoring]'
                      '3.organize the response according to the stage in stage guidance mode and apply writing assessment mode when in during stage and post stage.'
                      '4. always considering cognitive demand assessment while generate the final response.'
                      '5. Only output the response after organizing in the final step. '
                      )
    chat_completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input},
        ],
        stream=False
    )
    return chat_completion.choices[0].message.content.strip()




