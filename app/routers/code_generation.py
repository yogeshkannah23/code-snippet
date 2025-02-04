from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schema.schema import Prompt
from app.service.code_service import CodeService

router = APIRouter()

@router.post("/app/code")
def get_code(request: Prompt):
    service = CodeService()
    return service.generate_code_and_zip(request.prompt)


@router.get('/app/file/{filename}')
def download_link(filename):
    return FileResponse(f'project/{filename}.zip', media_type='application/zip', filename=f'project/{filename}.zip')