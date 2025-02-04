import os
import uuid
import tempfile
import shutil
from typing import List, Dict
from bs4 import BeautifulSoup

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.schema.schema import Output, BackendOutput


class CodeService:
    def __init__(self) -> None:
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=1.0)

    def generate_code_and_zip(self, prompt: str) -> dict:
        structured_llm = self.model.with_structured_output(Output)

        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that creates HTML and CSS files."),
            ("user",
             "{prompt}\n\nNote: The CSS file name should always be 'index.css', and it should be linked in the HTML file.")
        ])

        formatted_prompt = chat_prompt.format(prompt=prompt)

        output = structured_llm.invoke(formatted_prompt)
        generated_uuid = uuid.uuid4()
        backend_code = self.generate_backend_from_html(output.html_code)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_html = os.path.join(temp_dir, 'index.html')
            temp_css = os.path.join(temp_dir, 'index.css')
            backend_folder = os.path.join(temp_dir, 'backend')
            os.makedirs(backend_folder, exist_ok=True)

            with open(temp_html, "w") as f:
                f.write(output.html_code)
            with open(temp_css, "w") as f:
                f.write(output.css_code)

            for filename, content in backend_code.items():
                backend_file_path = os.path.join(backend_folder, filename)
                os.makedirs(os.path.dirname(backend_file_path), exist_ok=True)
                with open(backend_file_path, "w") as f:
                    f.write(content)

            filename = f'code-{str(generated_uuid)[:10]}'
            zip_path = f'project/{filename}'
            shutil.make_archive(zip_path, 'zip', temp_dir)

        return {
            "file": filename
        }

    @staticmethod
    def extract_fields_from_html(html_code: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html_code, 'html.parser')
        fields = []
        for input_tag in soup.find_all('input'):
            name = input_tag.get('name')
            input_type = input_tag.get('type', 'text')
            if name:
                fields.append({'name': name, 'type': input_type})
        return fields

    def generate_crud_endpoints(self, fields: List[Dict[str, str]]) -> BackendOutput:
        structured_llm = self.model.with_structured_output(BackendOutput)

        prompt = f"""
            Given the following fields extracted from an HTML form:
            {fields}
            Suggest a REST API structure with CRUD operations using FastAPI.
            Include model definitions, endpoints, and methods.
            The Answer should be in str format. No preambles or comments.
            It should be more realistic with real time scenarios.
            It should be concise and solve the hard problems.
            
            Note : The requirements.txt file will have contain the necessary libraries to run the API.
        """

        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an API designer."),
            ("user", "{prompt}")
        ])
        formatted_prompt = chat_prompt.format(prompt=prompt)
        response = structured_llm.invoke(formatted_prompt)

        return response

    @staticmethod
    def create_fastapi_backend(crud_code: BackendOutput) -> Dict:
        backend_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(backend_dir, "app"), exist_ok=True)
        os.path.join(backend_dir, "app", "main.py")
        os.path.join(backend_dir, "requirements.txt")
        backend_files = {"app/main.py": crud_code.main_file, "requirements.txt": crud_code.requirements_file}
        return backend_files

    def generate_backend_from_html(self, html_code: str) -> Dict:
        fields = self.extract_fields_from_html(html_code)
        crud_code = self.generate_crud_endpoints(fields)
        backend_file = self.create_fastapi_backend(crud_code)
        return backend_file
