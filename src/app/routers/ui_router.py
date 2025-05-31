from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
# Assuming templates is initialized in main.py and we can import it,
# or initialize it here too. For now, assume it's passed or imported.
# from src.app.main import templates # This creates a circular import if main imports ui_router
from fastapi.templating import Jinja2Templates


router = APIRouter(
    tags=["UI"],
    include_in_openapi=False # Don't include UI routes in OpenAPI schema
)

# It's better to initialize templates once. If main.py initializes it,
# ui_router.py should ideally get it from there (e.g. via dependency or app state).
# For simplicity in this step, re-initializing. This should be refactored.
# A common pattern is to have a core.templating module.
templates = Jinja2Templates(directory="src/app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

# Add a root redirect to /ui/login for convenience
@router.get("/", response_class=HTMLResponse)
async def ui_root_redirect_to_login(request: Request):
    # This is a simple redirect using HTML meta refresh, or use RedirectResponse
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard/dashboard.html", {"request": request})

@router.get("/users", response_class=HTMLResponse)
async def user_list_page(request: Request):
    return templates.TemplateResponse("users/user_list.html", {"request": request})

@router.get("/users/create", response_class=HTMLResponse)
async def user_create_page(request: Request):
    return templates.TemplateResponse("users/user_create.html", {"request": request})

@router.get("/lifecycle/onboard", response_class=HTMLResponse)
async def lifecycle_onboard_page(request: Request):
    return templates.TemplateResponse("lifecycle/onboard_form.html", {"request": request})

@router.get("/lifecycle/privilege", response_class=HTMLResponse)
async def lifecycle_privilege_page(request: Request):
    return templates.TemplateResponse("lifecycle/privilege_form.html", {"request": request})

@router.get("/lifecycle/offboard", response_class=HTMLResponse)
async def lifecycle_offboard_page(request: Request):
    return templates.TemplateResponse("lifecycle/offboard_form.html", {"request": request})

@router.get("/lifecycle/review", response_class=HTMLResponse)
async def lifecycle_review_page(request: Request):
    return templates.TemplateResponse("lifecycle/access_review.html", {"request": request})
