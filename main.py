import base64
import hashlib
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image
from io import BytesIO
from datetime import datetime
from pix2text import Pix2Text, merge_line_texts  
from streamlit_paste_button import paste_image_button as pbutton

st.set_page_config(layout="wide")
with st.expander("📕Guideline"):
	st.markdown("""
    #### 📌 NOTE:
    부득이한 경우가 아니라면 사용 중 **❌절대 새로고침을 하지 마세요❌**! 모든 저장 결과가 초기화됩니다.
             
    #### ❓How to Use? :
    0. **이미지 캡처 단축키**: (Window) `Window` + `Shift` + `S` / (Mac) `Shift` + `⌘`+ `4` 
    1. **이미지 입력**: 이미지 캡처 후, 다운 받을 필요 없이 `🖼️ Paste LaTex & English image` 버튼을 누르면 클립보드에 있는 이미지가 자동으로 불러와집니다.
    2. **텍스트 편집**: `LaTex Rendering` 아래가 인식된 텍스트를 LaTex 형식으로 다시 렌더링한 결과이므로, 이 내용을 참고해서 잘못 인식된 부분을 수정합니다.
    3. **문제별 결과 저장**: 편집된 내용을 확인한 후, 화면 오른쪽 Answer List에서 각 문제마다 있는 텍스트 영역에 해당 문제의 답을 입력한 후 `Save` 버튼을 누릅니다.
    4. **최종 결과 저장**: 화면 오른쪽 맨 아래의 `Save All as HTML` 버튼을 클릭한 후, 왼쪽 사이드바를 열면 HTML 파일로 다운로드할 수 있습니다.

    #### 📌 TIP:
    - 이미지 인식 모델의 실행은 사용자 환경에 영향을 받기 때문에, 저사양 환경에서는 이미지 입력 후 OCR Results 출력까지 시간(약 5-10초)이 소요되는 것이 정상입니다.
    - 이미지 인식 결과는 캡처한 이미지의 화질에 유의한 영향을 받습니다. 가능하면 이미지를 화면에 큰 사이즈로 띄워둔 상태에서 고품질로 캡처한 후 붙여넣으면 인식 성능이 향상됩니다.
    - 수식은 LaTeX 형식으로 표시됩니다.
    - 한번에 전체 화면의 캡처가 어렵다면, 절반씩 나눠서 캡처하는 방식을 고려해 보세요. (첫 번째 캡처 결과를 복사해서 갖고 있으면 됩니다.) 이렇게 하면 긴 이미지도 고품질로 인식하기가 쉬워집니다!
    - 문제의 선지에 1, 2, 3, 4 등의 인덱스를 수동으로 추가하면 ChatGPT의 정답률(?)이 비교적 향상됩니다.
    """)

left_column, right_column = st.columns(2)
p2t = Pix2Text()

def replace_radio_buttons_with_numbers(text):
    symbols = [' O ', 'o ', '® ', '回 ', 'D ', 
               'o\n', 'O\n', '®\n', '回\n', 'D\n']
    idx = 1
    for symbol in symbols:
        while symbol in text:
            text = text.replace(symbol, f"\n{idx}. ", 1)
            idx = idx % 4 + 1 
    return text

def perform_ocr(_image):
    outs = p2t.recognize(_image)
    #print("OCR Output:", outs)  
    #ocr_text = merge_line_texts(outs, auto_line_break=True)
    #print("merge_line_texts Output:", ocr_text)  
    #ocr_text = replace_radio_buttons_with_numbers(ocr_text)
    return outs

def generate_image_hash(image):
    with BytesIO() as buffer:
        image.save(buffer, format="PNG") 
        return hashlib.md5(buffer.getvalue()).hexdigest()

with left_column:
    st.header("Question OCR")
    paste_result = pbutton(
        text_color="#000000",
        label="🖼️ Paste LaTex & English image",
        background_color="#F0F2F6",
        hover_background_color="#BCCBDA",
        errors="raise",
    )

    if paste_result.image_data is not None:
        st.success("Image input")
        st.image(paste_result.image_data)
        image = paste_result.image_data
        image_hash = generate_image_hash(image)
        prompt_text = "Given the following multiple-choice question on the topic of physics, please read and understand the question and the four options provided. Then, identify and explain the single most correct answer out of the four options. Your explanation should include the reasoning behind why this option is correct and why the other options are not suitable.\n\n"

        if 'last_image_hash' not in st.session_state or st.session_state['last_image_hash'] != image_hash:
            try:
                ocr_text = perform_ocr(image)
            except Exception as e:
                st.error(f"Error while OCR: {e}")
                st.session_state['ocr_text'] = ""
                ocr_text = ""

            add_prompt = st.checkbox('Add Prompt', value=True)
            if add_prompt:
                if not ocr_text.startswith(prompt_text):
                    ocr_text = prompt_text + ocr_text
            else:
                if ocr_text.startswith(prompt_text):
                    ocr_text = ocr_text[len(prompt_text):]

            st.session_state['ocr_text'] = ocr_text
            st.session_state['last_image_hash'] = image_hash
            if ocr_text:
                st.success("OCR Result")

        else:
            add_prompt = st.checkbox('Add Prompt', value=True)
            current_text = st.session_state.get('ocr_text', '')
            if add_prompt and not current_text.startswith(prompt_text):
                st.session_state['ocr_text'] = prompt_text + current_text
            elif not add_prompt and current_text.startswith(prompt_text):
                st.session_state['ocr_text'] = current_text[len(prompt_text):]
        
        editable_ocr_text = st.text_area("Output Text", value=st.session_state.get('ocr_text', ''), height=250)

        if editable_ocr_text != st.session_state.get('ocr_text', ''):
            st.session_state['ocr_text'] = editable_ocr_text

        st.success("LaTex Rendering")
        st.markdown(st.session_state.get('ocr_text', ''))

with right_column:
    st.header("Answer List")

    if 'list_items' not in st.session_state:
        st.session_state.list_items = [{} for _ in range(10)]

    for index in range(10):
        st.subheader(f"Question {index+1}")
        text_input = st.text_input(f"Answer:", key=f"input_{index}")
        button_cols = st.columns(2)

        save_button, delete_button = button_cols[0], button_cols[1]

        with save_button:
            if st.button("✅Save", key=f"save_{index}"):
                st.session_state.list_items[index] = {"text": text_input, "ocr": st.session_state['ocr_text']}

        with delete_button:
            if st.button("❌Delete", key=f"delete_{index}"):
                st.session_state.list_items[index] = {}

        if st.session_state.list_items[index]:
            st.json(st.session_state.list_items[index])

    st.subheader("❗Solve All?")
    save_button_cols = st.columns(1)
    save_all_markdown_button = save_button_cols[0]


with save_all_markdown_button:
    if st.button("🕒Save All as HTML"):
        html_text = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Saved Answers</title>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script>
                window.MathJax = {
                    tex: {
                        inlineMath: [['$', '$'], ['\\(', '\\)']]
                    },
                    svg: {
                        fontCache: 'global'
                    }
                };
            </script>
            <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        </head>
        <body>
        <h2>Saved Answers and OCR Text</h2>
        """
        for i, item in enumerate(st.session_state.list_items):
            question_number = i + 1
            answer = item.get('text', 'N/A')
            ocr_text = item.get('ocr', 'N/A').replace('\n', '<br/>')

            html_text += f"<h3>Question {question_number}</h3>"
            html_text += f"<p><strong>Answer:</strong> {answer}</p>"
            html_text += f"<p><strong>Question:</strong> {ocr_text}</p>"

        html_text += "</body></html>"

        b64_html = base64.b64encode(html_text.encode()).decode()
        current_date = datetime.now().strftime("beta-%m-%d")
        filename = f"{current_date}.html"
        href = f'<a href="data:text/html;base64,{b64_html}" download="{filename}">🕒 Download HTML file</a>'
        
        st.sidebar.markdown(href, unsafe_allow_html=True)
        st.sidebar.markdown(html_text, unsafe_allow_html=True)