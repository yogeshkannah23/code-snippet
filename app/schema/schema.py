import re

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    prompt: str = Field(..., examples=['Create a login form with email and password fields.'])


class Output(BaseModel):
    html_code: str = Field(description="Give me the html code for the title")
    css_code: str = Field(description="Give me the css code for the title")

    def clean_code(self):
        self.html_code = re.sub(r'\\n|\\t', '', self.html_code)
        self.css_code = re.sub(r'\\n|\\t', '', self.css_code)


class BackendOutput(BaseModel):
    main_file: str = Field(description="Give me the main.py code for the title")
    requirements_file: str = Field(description="Give me the requirements.txt file for the application")

    def clean_code(self):
        self.main_file = re.sub(r'\\n|\\t', '', self.main_file)
        self.requirements_file = re.sub(r'\\n|\\t', '', self.requirements_file)
