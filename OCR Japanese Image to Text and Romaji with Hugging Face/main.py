import streamlit as st
from transformers import pipeline
import cutlet
from PIL import Image

pipe = pipeline("image-to-text", model="kha-white/manga-ocr-base", device=0)


# Sidebar for uploading images
with st.sidebar:
    uploaded_images = st.file_uploader(
    "Japanese image", accept_multiple_files=True, type = ["jpg","png"]
)
    
CSS_style = """
<style>
    div[data-testid="stSidebarUserContent"]
    {
        display: flex;
        text-align:center;
        justify-content: center;
        align-items: center;
    }
    div[data-testid="stFullScreenFrame"]
    {
        display: flex;
        text-align:center;
        margin-left: -40%; /* Move left by 10% */
        justify-content: center;
        align-items: center;
    }
    div[data-testid="stMarkdown"] div[data-testid="stMarkdownContainer"]
    {
        display: flex;
        text-align:center;
        margin-left: -40%; /* Move left by 10% */
        justify-content: center;
        align-items: center;
</style>
"""


st.markdown(CSS_style,True)

for image in uploaded_images:
    pil_image = Image.open(image)
    result = pipe(pil_image)
    text = result[0]["generated_text"]
    src_text = text.replace(" ", "")
    katsu = cutlet.Cutlet()

    romaji = katsu.romaji(src_text)

    with st.container():
        st.image(image,caption = image.name)
        st.write("日文原文:{}".format(src_text))
        st.write("羅馬拼音:{}".format(romaji))
        
