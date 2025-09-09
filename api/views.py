from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.auth import auth_header, base_url, get_token_from_cookie

router = APIRouter(tags=["Views"])
PROJECT_ROOT  = Path(__file__).resolve().parents[1]     # .../ToDoListAPI
TEMPLATES_DIR = PROJECT_ROOT / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def login_form(request: Request):
    if get_token_from_cookie(request):
        return RedirectResponse(url="/tasks", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base_url(request)}/api/login",
                data={"email": email, "password": password},
            )
    except (httpx.TimeoutException, httpx.HTTPError):
        detail = "Сервис аутентификации недоступен. Попробуйте позже."
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": detail}, status_code=503
        )

    if resp.status_code == 200:
        data = resp.json()
        token = f"{data['token_type']} {data['access_token']}"

        redirect = RedirectResponse(url="/tasks", status_code=303)
        redirect.set_cookie(
            "access_token",
            token,
            httponly=True,
            max_age=60 * 60 * 24,
            samesite="lax",
            secure=True,
        )
        return redirect

    try:
        detail = resp.json().get("detail", "Ошибка авторизации")
    except Exception:
        detail = "Ошибка авторизации"
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": detail}, status_code=400
    )


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    if get_token_from_cookie(request):
        return RedirectResponse(url="/tasks", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base_url(request)}/api/registration",
                json={"name": name, "email": email, "password": password},
            )
    except (httpx.TimeoutException, httpx.HTTPError):
        detail = "Сервис регистрации недоступен. Попробуйте позже."
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": detail, "name": name, "email": email},
            status_code=503,
        )

    if resp.status_code == 200:
        data = resp.json()
        token = f"{data['token_type']} {data['access_token']}"
        redirect = RedirectResponse(url="/tasks", status_code=303)
        redirect.set_cookie(
            "access_token",
            token,
            httponly=True,
            max_age=60 * 60 * 24,
            samesite="lax",
            secure=True,
            path="/",
        )
        return redirect

    try:
        detail = resp.json().get("detail", "Ошибка регистрации")
    except Exception:
        detail = "Ошибка регистрации"

    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": detail, "name": name, "email": email},
        status_code=resp.status_code if resp.status_code >= 400 else 400,
    )


@router.post("/logout")
async def logout():
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    page: int = 1,
    limit: int = 20,
    filter: str = "all",
    q: str | None = None,
):
    token = get_token_from_cookie(request)
    if not token:
        return RedirectResponse(url="/", status_code=303)

    items: list[dict] = []
    meta = {"page": page, "pages": 1, "total": 0, "limit": limit}
    stats = {"total": 0, "completed": 0, "active": 0}

    api_base = f"{base_url(request)}/api/todos"
    page_url = f"{api_base}/{page}/{limit}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(page_url, headers=auth_header(token))
    except (httpx.TimeoutException, httpx.HTTPError):
        return templates.TemplateResponse(
            "tasks.html",
            {
                "request": request,
                "tasks": [],
                "q": q or "",
                "filter": filter,
                "meta": meta,
                "stats": stats,
            },
            status_code=503,
        )

    if r.status_code == 401:
        redirect = RedirectResponse(url="/", status_code=303)
        redirect.delete_cookie("access_token")
        return redirect

    if r.status_code == 200:
        data = r.json()
        items = data.get("items", [])
        meta = {
            "page": data.get("page", page),
            "pages": data.get("pages", 1),
            "total": data.get("total", len(items)),
            "limit": data.get("limit", limit),
        }

        stats["total"] = int(meta["total"]) if meta["total"] is not None else 0

        if stats["total"] > 0:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    all_url = f"{api_base}/1/{stats['total']}"
                    r_all = await client.get(all_url, headers=auth_header(token))
                if r_all.status_code == 200:
                    all_items = r_all.json().get("items", [])
                    stats["completed"] = sum(
                        1 for t in all_items if t.get("status") == "completed"
                    )
                    stats["active"] = sum(
                        1 for t in all_items if t.get("status") == "active"
                    )
            except (httpx.TimeoutException, httpx.HTTPError):
                pass

    elif r.status_code == 404:
        last_page = max(1, meta["pages"])
        return RedirectResponse(
            url=f"/tasks?page={last_page}&limit={limit}&filter={filter}&q={q or ''}",
            status_code=303,
        )
    else:
        return templates.TemplateResponse(
            "tasks.html",
            {
                "request": request,
                "tasks": [],
                "q": q or "",
                "filter": filter,
                "meta": meta,
                "stats": stats,
            },
            status_code=r.status_code,
        )

    filtered = items
    if q:
        ql = q.lower()
        filtered = [
            t
            for t in filtered
            if ql
            in (t.get("title", "").lower() + " " + (t.get("description") or "").lower())
        ]

    if filter == "active":
        filtered = [t for t in filtered if t.get("status") == "active"]
    elif filter == "done":
        filtered = [t for t in filtered if t.get("status") == "completed"]

    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "tasks": filtered,
            "q": q or "",
            "filter": filter,
            "meta": meta,
            "stats": stats,
        },
    )
