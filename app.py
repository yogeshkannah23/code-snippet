from fastapi import FastAPI
from fastapi.responses import FileResponse
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import tempfile
import shutil
import re
import uuid
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Prompt(BaseModel):
    prompt: str
    is_enhanced: bool = True


class EnhancePrompt(BaseModel):
    enhanced_prompt: str = Field(description="Give me the enhanced prompt for the given input") # noqa


class Output(BaseModel):
    html_code: str = Field(description="Give me the html code for the title")
    css_code: str = Field(description="Give me the css code for the title")

    def clean_code(self):
        self.html_code = re.sub(r'\\n|\\t', '', self.html_code)
        self.css_code = re.sub(r'\\n|\\t', '', self.css_code)


@app.post("/app/code")
def get_code(request: Prompt):
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    prompt = request.prompt
    is_enhanced_prompt = request.is_enhanced
    if not is_enhanced_prompt:
        prompt = enhance_user_propmpt(prompt, model)
    structured_llm = model.with_structured_output(Output)
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that creates HTML and CSS files."), # noqa
        ("user", "{prompt}\n\nNote: The CSS file name should always be 'index.css', and it should be linked in the HTML file.") # noqa
    ])
    formatted_prompt = chat_prompt.format(prompt=prompt)
    output = structured_llm.invoke(formatted_prompt)
    generated_uuid = uuid.uuid4()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_html = os.path.join(temp_dir, 'index.html')
        temp_css = os.path.join(temp_dir, 'index.css')
        with open(temp_html, "w") as f:
            f.write(output.html_code)
        with open(temp_css, "w") as f:
            f.write(output.css_code)
        filename = f'code-{str(generated_uuid)[:10]}'
        shutil.make_archive(f'project/{filename}', 'zip', temp_dir)
    return {
        'status': 200,
        'message': 'Success',
        'file': filename
    }


@app.get('/app/file/{filename}')
def download_link(filename):
    return FileResponse(f'project/{filename}.zip',
                        media_type='application/zip',
                        filename=f'project/{filename}.zip')


def enhance_user_propmpt(prompt, model):
    structured_llm = model.bind_tools([EnhancePrompt])
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant designed to understand user prompts and enhance them to deliver optimal results in web development. If the user does not specify colors or styles, reference popular website themes and use them as inspiration to craft a refined and effective prompt."), # noqa
        ("user", "{prompt}\n\nNote: If the user asks for a game-selling site without mentioning styles or colors, use popular websites like Epic Games or Steam as references.") # noqa
    ])
    formatted_prompt = chat_prompt.format(prompt=prompt)
    output = structured_llm.invoke(formatted_prompt)
    enhanced_prompt = output.tool_calls[0]['args']['enhanced_prompt']
    return enhanced_prompt
