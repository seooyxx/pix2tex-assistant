import base64
import hashlib
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image
from io import BytesIO
from pix2text import Pix2Text, merge_line_texts  
from streamlit_paste_button import paste_image_button as pbutton

st.set_page_config(layout="wide")
left_column, right_column = st.columns(2)
p2t = Pix2Text()

def replace_radio_buttons_with_numbers(text):
    symbols = ['O ', '® ', '回 ', 'D ', 'O\n', '®\n', '回\n', 'D\n']
    idx = 1
    for symbol in symbols:
        while symbol in text:
            text = text.replace(symbol, f"\n{idx}. ", 1)
            idx = idx % 4 + 1 
    return text

def perform_ocr(_image):
    outs = p2t.recognize(_image)
    print("OCR Output:", outs)  
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
        label="🖼️ Paste mixed images with both text and formulas",
        background_color="#F0F2F6",
        hover_background_color="#BCCBDA",
        errors="raise",
    )

    if paste_result.image_data is not None:
        st.success("Image input")
        st.image(paste_result.image_data)
        image = paste_result.image_data
        image_hash = generate_image_hash(image)

        if 'last_image_hash' not in st.session_state or st.session_state['last_image_hash'] != image_hash:
            try:
                ocr_text = perform_ocr(image)
                st.session_state['ocr_text'] = ocr_text
                st.session_state['last_image_hash'] = image_hash
                st.success("OCR Result")
            except Exception as e:
                st.error(f"Error while OCR: {e}")
                st.session_state['ocr_text'] = ""
        
        editable_ocr_text = st.text_area("Output Text", value=st.session_state.get('ocr_text', ''), height=150)

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
            if st.button("Save", key=f"save_{index}"):
                st.session_state.list_items[index] = {"text": text_input, "ocr": st.session_state['ocr_text']}

        with delete_button:
            if st.button("Delete", key=f"delete_{index}"):
                st.session_state.list_items[index] = {}

        if st.session_state.list_items[index]:
            st.json(st.session_state.list_items[index])

    st.subheader("Save")
    save_button_cols = st.columns(1)
    save_all_markdown_button = save_button_cols[0]


with save_all_markdown_button:
    if st.button("Save All as HTML"):
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
        href = f'<a href="data:text/html;base64,{b64_html}" download="all_data.html">Download HTML file</a>'
        
        st.sidebar.markdown(href, unsafe_allow_html=True)
        st.sidebar.markdown(html_text, unsafe_allow_html=True)