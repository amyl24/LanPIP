from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import os
import anthropic
from llamaapi import LlamaAPI
from openai import OpenAI
from PIL import Image
import requests

# Initialize
api_key = "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"
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI(api_key="sk-e0f6e484e9c7437cbaf34ff062631b6d", base_url="https://api.deepseek.com")


def cus_prompt_generator(user_input):
## message: generator
    messages = [
        {"role": "system", "content": "Based on the user's input, extract important information about the user. Make the profile concise and accurate."
                                      "Look at learner's self description, find learning goals, and preferences. Use the information provided to tailor the content, "
                                      "structure, and difficulty of the prompts accordingly. Put 'N/A' if the component is not included in user's input"
                                      "Here are relevant components:"
                                      "1. **Learner Profile Assessment:**"
                                      "- Determine the learner’s age group and any relevant background information they provide."
                                      "- Identify the learner’s knowledge level on the subject (beginner, intermediate, advanced) based on their self-description."
                                      "2. **Learning Goals and Interests:**"
                                      "- Extract specific learning goals, topics of interest, or areas the learner wants to improve in."
                                      "- Consider any mentioned preferences for learning styles or types of activities (e.g., visual learning, interactive tasks)."
                                      "3. **Incorporate Adaptivity:**"
                                      "- If possible, suggest a simple mechanism for adjusting the difficulty or focus of the "
                                      "prompts based on hypothetical feedback or learner performance."
                                      "4. **Feedback and Resources:**"
                                      "- Recommend resources or strategies for the learner to use if they encounter difficulties with the prompts."
                                      "- Suggest a format for feedback that aligns with the learner’s preferences and goals, aiming to support their learning process effectively."},
        {"role": "user", "content": user_input}
    ]
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    return completion.choices[0].message.content

def reasoning_check(user_input):
    message = [{"role": "system", "content": "Based on the user's input, extract user's basic request about writing and then determine whether this request needs long terms of reasoning and logical thinking or not."
                                             "If this request needs long terms of reasoning, output 'reasoning'.Otherwise, output'Non-reasoning'."},
               {"role":"user", "content": user_input}]
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=message,
        stream=False
    )
    reason = completion.choices[0].message.content
    if "reasoning" in reason:
        return 1
    else:
        return 0

def conclu(prompt):
    system_prompt = (
        f'Here is an output from analysis: {prompt}'
        'Extract final conclusion part of the output'
        'Here are some keywords that can help determine the conclusion part of the output: final conclusion, final thought,conclusion '
        'Only output the final conclusion part'
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0,
        stream=False
    )
    conclusion = response.choices[0].message.content.strip()
    return conclusion

def f1(prompt):
    # print(question)
    system_prompt = (
        f'You are an educator help student complete this sentence with a few words: {prompt}'
        'Offer a detailed and comprehensive background how to complete the sentence,'
        'including definitions of key terms, historical context, relevant theories, and illustrative examples. '
        'Present your explanations with clarity, accuracy, and structure, ensuring they are accessible to a diverse audience.'
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0,
        stream=False
    )
    generation_1 = response.choices[0].message.content.strip()
    # print("=== f1 output ===")
    # print(generation_1)
    return generation_1

def validity(prompt,generation_1):
    system_prompt = (f'''The incomplete sentence is: {prompt}. The background information of the incomplete sentence i:{generation_1}
    Explain why: Should or shouldn't there be only one possible and objective answer to this question? In other words, is answer proven by science or facts?
    After a detailed and deliberate analysis, output the final thoughts concluded from the analysis.''')
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0,
        stream=False
    )
    validity = response.choices[0].message.content.strip()
    # print("=== validity ===")
    # print(validity)
    return validity

def f2(prompt, generation_1):
    system_prompt = (f'''

        Incomplete sentence: {prompt}.

        Raw draft: {generation_1}.

        You are a critical professor to address all deficiencies of this raw draft.

        Step 1: Carefully read and interpret the inquiry. Identify the core elements of the prompt to ensure clarity about what is being asked.
        Step 2: Break down the task step by step, considering different academic angles and potential social nuances. Reflect on any relevant details or social complexities related to confusion or ambiguity that might influence the answer.
        Step 3: Synthesize your observations and reasoning into a coherent argument. Address possible counterpoints or alternative perspectives to strengthen your position.
        Step 4: Integrate your findings and reasoning into a clear, concise final answer. Make sure it directly addresses the question and encompasses all relevant aspects of ambiguity or unfairness.''')
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0,
        stream=False
    )
    generation_2 = response.choices[0].message.content.strip()
    # print("=== f2 output ===")
    # print(generation_2)
    return generation_2

def f3(prompt, generation_1, generation_2):
    system_prompt = (f'''Given the following incomplete sentence: {prompt}. 
                        Here is the content from backgrounding educator: {generation_1}.
                        And these are comments from critical professor: {generation_2}. 

                    You are an meta-reviewer. Your task is consider both instructions to complete the sentence, following the steps below.

                    Step 1: Identify the facts that more than half of the answers agree upon.
                    Step 2: Identify the facts that conflict among the answers.
                    Step 3: Resolve the conflicting facts.
                    Step 4: Identify unique facts mentioned only in one answer.
                    Step 5: Combine the facts from Steps 1, 3, and 4.
                    Step 6: Complete the sentence with an objective tone.
                    After the 6 steps above, output the final conclusion according to the analysis from the 6 steps''')

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0,
        stream=False
    )
    generation_3 = response.choices[0].message.content.strip()
    # print("=== f3 output ===")
    # print(generation_3)
    return generation_3

def validity_only(prompt):
    system_prompt = (f'''The user's input is: {prompt}. 
    Explain why: Should or shouldn't there be only one possible and objective answer to this question? In other words, is answer proven by science or facts?
    After a detailed and deliberate analysis, output the final thoughts concluded from the analysis.''')
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0,
        stream=False
    )
    validity = response.choices[0].message.content.strip()
    # print("=== validity ===")
    # print(validity)
    return validity