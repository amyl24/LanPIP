import os
import json
import copy
import requests
import webbrowser
import streamlit as st
from llamaapi import LlamaAPI
from openai import OpenAI
from faker import Faker
from dataclasses import dataclass
from st_audiorec import st_audiorec
from streamlit.components.v1 import html
from PIL import Image
from io import BytesIO
import sys

sys.path.append('./test')
from streamlit.components.v1 import html
from bots import reasoning, TBLT, vocab,image
from typing import Union
from pydub import AudioSegment
from pydub.utils import which
from supabase import create_client, Client

url = "https://fvctjijwxnafbqalacaj.supabase.co"  # 你的 Supabase 项目 URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ2Y3RqaWp3eG5hZmJxYWxhY2FqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDQzOTAxNSwiZXhwIjoyMDYwMDE1MDE1fQ.op4AzFCnCIIWeMwYj9XIBcLVX7dtURg3aEfPR31X2Qc"  # 你的 Supabase API 密钥

supabase: Client = create_client(url, key)


@dataclass
class Message:
    actor: str
    # payload: str | int | bytes
    payload: Union[str, int, bytes]

###网页设计
def redirect_to_google():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Responsive Links</title>
    </head>
    <body>
    <div style="border: none; padding: 20px; width: 100%; margin: 20px auto; background-color: #e6e3e3; border-radius: 10px; box-sizing: border-box; overflow: auto;">
        <span style="color: red; font-weight: bold;font-size: 20px;">Thank you for using! Please help us fill out the survey of the function you experienced!</span>
        <div style="margin-top: 20px;"> <!-- Add this div with margin-top for spacing -->
            <a href="https://forms.gle/e4t1h6MpmpJ6cJs38" target="_blank" style="color: black; text-decoration: underline; display: block; margin-bottom: 10px; font-size: 16px;">Speaking AI Evaluation</a>
            <a href="https://forms.gle/V7SkmVxo4NoV1Ner9" target="_blank" style="color: black; text-decoration: underline; display: block; margin-bottom: 10px; font-size: 16px;">Vocabulary AI Evaluation</a>
            <a href="https://forms.gle/LpNbnFNWDb8EbrXA7" target="_blank" style="color: black; text-decoration: underline; display: block; margin-bottom: 10px; font-size: 16px;">Writing Assistant AI Evaluation</a>
            <a href="https://forms.gle/Aww8CbudzM52MpPX6" target="_blank" style="color: black; text-decoration: underline; display: block; margin-bottom: 10px; font-size: 16px;">Writing Assessment AI Evaluation</a>
            <a href="https://forms.gle/Xkr9RtoMQkuxgEVBA" target="_blank" style="color: black; text-decoration: underline; display: block; margin-bottom: 10px; font-size: 16px;">TBLT system on itinerary</a>
        </div>
    </div>
    </body>
    </html>
    """
    st.markdown(html_content, unsafe_allow_html=True)


fake = Faker()

##生成随机文本
def generate_response():
    output = fake.text()
    return output
    

##st.session_state:存储和访问跨组件共享的变量
if 'login' not in st.session_state or st.session_state['login'] != True:
    st.title("LanPIP - Login Page")
    st.markdown("Please contact Faceia at fh2450@tc.columbia.edu if you encounter any trouble logging in.")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button('Login'):
        if (username in ['wuzh1','wuzh2','zhwy1','zhwy2','hely1','hely2','guyt1','guyt2','chjz2','chjz2','wamj1','wamj2','suj1','suj2','zhm1','zhm2','yayb1','yayb2','yay1','yay2',
                         'lirh1','lirh2','lizx1','lizx2','liyl1','liyl2','qikt1','qikt2','xihy1','xihy2','lilf1','lilf2','dukp1','dukp2','yalh1','yalh2','yawq1','yawq2','ked1','ked2',
                         'huj1','huj2','jiqm1','jiqm2','luxy1','luxy2','chzy1','chzy2','lijm1','lijm2','chl1','chl2','zhzy1','zhzy2','gahr1','gahr2','maxt1','maxt2','qkt1','qkt2',
                         'luzq1','lvyj1','lvyj2','shs1','shs2','zhjw1','zhjw2','admin', '2264019668@qq.com','2363620110@qq.com', 'kmb2287@tc.columbia.edu', 'ziyue789@gmail.com',
                         'yf2696@tc.columbia.edu', 'jh4751@tc.columbia.edu', 'lrk2150@tc.columbia.edu',
                         'rl3370@tc.columbia.edu', 'htn2113@tc.columbia.edu', 'sms2491@tc.columbia.edu',
                         'qw2421@tc.columbia.edu', 'yy3341@tc.columbia.edu', 'cy2707@tc.columbia.edu',
                         'az2744@tc.columbia.edu', 'lz2911@tc.columbia.edu', 'andressa.kohler@hotmail.com',
                         'kouki.ota@gmail.com', 'ana.mpol@hotmail.com', 'nataliestiebler@outlook.com', 'tatsuro_desu_yo@hotmail.com',
                         'xl3304@tc.columbia.edu']
                and password == '1'):
            st.session_state['username'] = username
            st.session_state['login'] = True

            # create a temporary dir to store the audio files
            data_base = "./temp"
            path = os.path.join(data_base, username)
            if os.path.exists(path):
                for file in os.listdir(path):
                    os.remove(os.path.join(path, file))
            else:
                os.makedirs(path)
            st.session_state['path'] = path

            st.experimental_rerun()
    redirect_to_google()


if 'login' in st.session_state and st.session_state['login'] == True:
    st.title('LanPIP')
    with st.sidebar:
        st.header('This application is currently implemented with:')
        st.write('- Writing Assistance ✍️')
        st.write('- Vocabulary Building 📚')
        st.write('- Writing Assessment/feedback 📝')
        st.write('------------------------------')
        uploaded_file = st.file_uploader("Upload only", type=['png', 'jpg', 'jpeg'],
                                         key="file_uploader")
        system_choice = st.radio("Select system", options=["system1", "system2","system3"])


    user_input = st.chat_input('Enter `exit` to end this conversation.')
    st.info("If you are stuck or want to start a new conversation, please try to refresh the page and log in again.")

    if 'reset_uploader' not in st.session_state:
        st.session_state['reset_uploader'] = False





    ##基础设定
    if 'message' not in st.session_state:
        st.session_state['stage'] = 0  # 0
        st.session_state['model_type'] = 'deepseek-chat'  # 0
        st.session_state['history'] = []
        st.session_state['message'] = [Message(actor='ai', payload='Welcome to the TBLT writing class! Please enter your personal information and intends.😊')]
        st.session_state['cus_prompt'] = ''
        st.session_state['input_history'] = []
        st.session_state["upload"] = False
        st.session_state['step'] = 0
        st.session_state['topic'] = ''

        # for message in st.session_state['message']:
        #     if type(message.payload) == str:
        #         st.chat_message(message.actor).write(message.payload)
        #     else:
        #         st.chat_message(message.actor).audio(message.payload)

    if 'system' not in st.session_state:
        st.session_state['system'] = None

        # 检查是否选择了不同的系统，并保存系统切换后的消息
    if system_choice != st.session_state['system']:
        # 仅在系统选择变化时更新
        st.session_state['system'] = system_choice

        # 保持当前消息，不重置
        st.session_state['message'] = st.session_state.get('message', [])
        for message in st.session_state['message']:
            if type(message.payload) == str:
                st.chat_message(message.actor).write(message.payload)
            else:
                st.chat_message(message.actor).audio(message.payload)
    if user_input:
        for message in st.session_state['message']:
            if type(message.payload) == str:
                st.chat_message(message.actor).write(message.payload)
            else:
                st.chat_message(message.actor).audio(message.payload)
        if user_input.lower() == 'exit':
            st.session_state['stage'] = 0  # 0
            st.session_state['model_type'] = 'deepseek-chat'  # 0
            st.session_state['input_history'] = []
            st.session_state['topic'] = ''
            st.session_state["upload"] = False
            bot_response = ('All records have been deleted. If you need anything else, please let me know! 😊')
            data = {
                    "username":st.session_state['username'] ,
                    "system":st.session_state['system'] ,
                    "content": st.session_state['history']
                }
            response = supabase.table("lanpip-chatdata").insert(data).execute()
            st.balloons()
            redirect_to_google()

        if st.session_state['step'] == 0:
            st.chat_message('user').write(user_input)
            st.session_state['message'].append(Message(actor='user', payload=user_input))
            cus_prompt = reasoning.cus_prompt_generator(user_input)
            with st.expander("Show Your Customized Prompt"):
                st.write(f'{cus_prompt}')
            st.session_state['cus_prompt'] = cus_prompt
            st.session_state['history'].extend(["cus_prompt:", cus_prompt])
            ai_message = Message(actor='ai', payload='Please enter your request or writing😊')
            st.chat_message('ai').write(ai_message.payload)
            st.session_state['message'].append(ai_message)
            st.session_state['step'] = 1
            # for message in st.session_state['message']:
            #     if type(message.payload) == str:
            #         st.chat_message(message.actor).write(message.payload)
            #     else:
            #         st.chat_message(message.actor).audio(message.payload)


        elif st.session_state['step'] == 1 and st.session_state['system'] == 'system1' :
            st.chat_message('user').write(user_input)
            st.session_state['message'].append(Message(actor='user', payload=user_input))
            cus_prompt = st.session_state['cus_prompt']
            with st.expander("Show Your Customized Prompt"):
                st.write(f'{cus_prompt}')
            if st.session_state['stage'] != 3:
                stage = TBLT.stage_classification(user_input)
                st.session_state['stage'] = stage
            elif st.session_state['stage'] == 3:
                stage = st.session_state['stage']
            reason = reasoning.reasoning_check(user_input)
            if st.session_state['topic'] == '':
                topic = TBLT.topic_classify(user_input)
                st.session_state['topic'] = topic
            else:
                topic = st.session_state['topic']



            if stage == 0 and reason == 1:
                generation_1 = reasoning.f1(user_input)
                generation_2 = reasoning.f2(user_input, generation_1)
                c_ = reasoning.f3(user_input, generation_1, generation_2)
                c = reasoning.conclu(c_)
                v_ = reasoning.validity(user_input, generation_1)
                v = reasoning.conclu(v_)
                v_c = c + v
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre(history_string,cus_prompt,v_c,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre(history_string,cus_prompt,v_c,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            elif stage == 0 and reason == 0:
                v_ = reasoning.validity_only(user_input)
                v = reasoning.conclu(v_)
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre(history_string,cus_prompt,v,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre(history_string, cus_prompt,v,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            elif stage == 1 and reason == 0:
                v_ = reasoning.validity_only(user_input)
                v = reasoning.conclu(v_)
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    with st.expander("Related WordNet Information"):
                        word_list = vocab.vocab_fetch_processor(user_input)
                        wordnet_info = vocab.wordnet_interpreter_processor(word_list)
                        st.write(f'{wordnet_info}')
                    vocabulary = vocab.vocab_chat_with_model_generator(user_input,
                                                                     st.session_state['cus_prompt'], word_list,
                                                                     wordnet_info)
                    bot_response = TBLT.final_generator_vocab(history_string, cus_prompt, v,vocabulary,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    with st.expander("Related WordNet Information"):
                        word_list = vocab.vocab_fetch_processor(user_input)
                        wordnet_info = vocab.wordnet_interpreter_processor(word_list)
                        st.write(f'{wordnet_info}')
                    vocabulary = vocab.vocab_chat_with_model_generator(user_input,
                                                                     st.session_state['cus_prompt'], word_list,
                                                                     wordnet_info)
                    bot_response = TBLT.final_generator_vocab(history_string,cus_prompt, v,vocabulary,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            elif stage == 2 and reason == 0:
                v_ = reasoning.validity_only(user_input)
                v = reasoning.conclu(v_)
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_during(history_string, cus_prompt,v,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage']=3
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_during(history_string, cus_prompt,v,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage']=3
            elif stage == 2 and reason == 1:
                generation_1 = reasoning.f1(user_input)
                generation_2 = reasoning.f2(user_input, generation_1)
                c_ = reasoning.f3(user_input, generation_1, generation_2)
                c = reasoning.conclu(c_)
                v_ = reasoning.validity(user_input, generation_1)
                v = reasoning.conclu(v_)
                v_c = c + v
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_during(history_string, cus_prompt,v_c,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage']=3
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_during(history_string, cus_prompt,v_c,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:        
                        st.session_state['stage']=3
            elif stage == 3 and reason == 1:
                generation_1 = reasoning.f1(user_input)
                generation_2 = reasoning.f2(user_input, generation_1)
                c_ = reasoning.f3(user_input, generation_1, generation_2)
                c = reasoning.conclu(c_)
                v_ = reasoning.validity(user_input, generation_1)
                v = reasoning.conclu(v_)
                v_c = c + v
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_post(history_string, cus_prompt,v_c,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_post(history_string, cus_prompt,v_c,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            else:
                v_ = reasoning.validity_only(user_input)
                v = reasoning.conclu(v_)
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_post(history_string, cus_prompt,v,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string,cus_prompt)
                    bot_response = TBLT.final_generator_post(history_string, cus_prompt,v,assessment,topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])

            st.chat_message('ai').write(bot_response)
            st.session_state['message'].append(Message(actor='ai', payload=bot_response))
            # for message in st.session_state['message']:
            #     if type(message.payload) == str:
            #         st.chat_message(message.actor).write(message.payload)
            #     else:
            #         st.chat_message(message.actor).audio(message.payload)

        elif st.session_state['step'] == 1 and st.session_state['system'] == 'system2':
            st.chat_message('user').write(user_input)
            st.session_state['message'].append(Message(actor='user', payload=user_input))
            cus_prompt = st.session_state['cus_prompt']
            with st.expander("Show Your Customized Prompt"):
                st.write(f'{cus_prompt}')
            if st.session_state['stage'] != 3:
                stage = TBLT.stage_classification(user_input)
                st.session_state['stage'] = stage
            elif st.session_state['stage'] == 3:
                stage = st.session_state['stage']
            reason = reasoning.reasoning_check(user_input)
            if st.session_state['topic'] == '':
                topic = TBLT.topic_classify(user_input)
                st.session_state['topic'] = topic
            else:
                topic = st.session_state['topic']

            if stage == 0 and reason == 1:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre_2(history_string, cus_prompt, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre_2(history_string, cus_prompt, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            elif stage == 0 and reason == 0:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre_2(history_string, cus_prompt, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    bot_response = TBLT.final_generator_pre_2(history_string, cus_prompt, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            elif stage == 1 and reason == 0:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    with st.expander("Related WordNet Information"):
                        word_list = vocab.vocab_fetch_processor(user_input)
                        wordnet_info = vocab.wordnet_interpreter_processor(word_list)
                        st.write(f'{wordnet_info}')
                    vocabulary = vocab.vocab_chat_with_model_generator(user_input,
                                                                       st.session_state['cus_prompt'], word_list,
                                                                       wordnet_info)
                    bot_response = TBLT.final_generator_vocab_2(history_string, cus_prompt, vocabulary, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    with st.expander("Related WordNet Information"):
                        word_list = vocab.vocab_fetch_processor(user_input)
                        wordnet_info = vocab.wordnet_interpreter_processor(word_list)
                        st.write(f'{wordnet_info}')
                    vocabulary = vocab.vocab_chat_with_model_generator(user_input,
                                                                       st.session_state['cus_prompt'], word_list,
                                                                       wordnet_info)
                    bot_response = TBLT.final_generator_vocab_2(history_string, cus_prompt, vocabulary, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            elif stage == 2 and reason == 0:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_during_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage'] = 3
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_during_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage'] = 3
            elif stage == 2 and reason == 1:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_during_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage'] = 3
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_during_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                    if "Score 4" or "Score 5" in assessment:
                        st.session_state['stage'] = 3
            elif stage == 3 and reason == 1:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_post_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_post_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            else:
                if uploaded_file is not None and user_input.lower() == "uploaded":
                    file_path = image.compress_image(uploaded_file, st.session_state['path'])
                    gen_txt = image.orc_processor(file_path)
                    st.session_state['history'].append(gen_txt)
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_post_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
                else:
                    st.session_state['history'].extend(["USER:", user_input])
                    history_string = " ".join(st.session_state['history'])
                    assessment = TBLT.chat_assessment_with_model_generator(history_string, cus_prompt)
                    bot_response = TBLT.final_generator_post_2(history_string, cus_prompt, assessment, topic)
                    st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])

            st.chat_message('ai').write(bot_response)
            st.session_state['message'].append(Message(actor='ai', payload=bot_response))


        elif st.session_state['step'] == 1 and st.session_state['system'] == 'system3':
            st.chat_message('user').write(user_input)
            st.session_state['message'].append(Message(actor='user', payload=user_input))
            cus_prompt = st.session_state['cus_prompt']
            with st.expander("Show Your Customized Prompt"):
                st.write(f'{cus_prompt}')
            topic = TBLT.topic_classify(user_input)
            st.session_state['topic'] = topic

            if uploaded_file is not None and user_input.lower() == "uploaded":
                file_path = image.compress_image(uploaded_file, st.session_state['path'])
                gen_txt = image.orc_processor(file_path)
                st.session_state['history'].append(gen_txt)
                history_string = " ".join(st.session_state['history'])
                with st.expander("Related WordNet Information"):
                    word_list = vocab.vocab_fetch_processor(user_input,topic)
                    wordnet_info = vocab.wordnet_interpreter_processor(word_list)
                    st.write(f'{wordnet_info}')
                bot_response = TBLT.final_generator(history_string,wordnet_info)
                st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])
            else:
                st.session_state['history'].extend(["USER:", user_input])
                history_string = " ".join(st.session_state['history'])
                with st.expander("Related WordNet Information"):
                    word_list = vocab.vocab_fetch_processor(user_input,topic)
                    wordnet_info = vocab.wordnet_interpreter_processor(word_list)
                    st.write(f'{wordnet_info}')
                bot_response = TBLT.final_generator(history_string,wordnet_info)
                st.session_state['history'].extend(["BOT_RESPONSE:", bot_response])

            st.chat_message('ai').write(bot_response)
            st.session_state['message'].append(Message(actor='ai', payload=bot_response))
            # for message in st.session_state['message']:
            #     if type(message.payload) == str:
            #         st.chat_message(message.actor).write(message.payload)
            #     else:
            #         st.chat_message(message.actor).audio(message.payload)












