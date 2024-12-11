from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
import os
import tempfile
import shutil
import re
import uuid
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')


class Output(BaseModel):
    html_code: str = Field(description="Give me the html code for the title")
    css_code: str = Field(description="Give me the css code for the title")

    def clean_code(self):
        self.html_code = re.sub(r'\\n|\\t', '', self.html_code)
        self.css_code = re.sub(r'\\n|\\t', '', self.css_code)


@app.get("/app/code/{prompt}")
def get_code(prompt):
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    structured_llm = model.with_structured_output(Output)
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that creates HTML and CSS files."),
        ("user", "{prompt}\n\nNote: The CSS file name should always be 'index.css', and it should be linked in the HTML file.")
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
        'file':filename
    }


@app.get('/app/file/{filename}')
def download_link(filename):
    return FileResponse(f'project/{filename}.zip', media_type='application/zip', filename=f'project/{filename}.zip') 