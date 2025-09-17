from sqladmin import Admin, ModelView
from wtforms import PasswordField
from wtforms.validators import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqladmin.authentication import AuthenticationBackend
from core.security import hash_password, validate_password
from db.database import engine, new_session
from db.models.task import TaskORM
from db.models.user import UserOrm
from repositories.user_repository import UserRepository


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        async with new_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_email(username)

        if not user or not validate_password(user.hashed_password, password):
            return False

        if not user.is_admin:
            return False

        request.session.update({"user_id": user.id})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request):

        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        async with new_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(user_id)

        if not user or not user.is_admin:
            request.session.clear()
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        return True

class UserAdmin(ModelView, model=UserOrm):
    column_list = [UserOrm.id, UserOrm.name, UserOrm.email, UserOrm.is_admin]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_details_exclude_list = ["hashed_password"]
    column_labels = {"hashed_password": "Пароль", "name": "Имя", "tasks": "Задачи", "is_admin": "Админ?"}
    form_overrides = {"hashed_password": PasswordField}
    form_args = {
        "hashed_password": {
            "validators": [Optional()],
            "render_kw": {
                "autocomplete": "new-password",
                "required": False,
            },
        }
    }

    async def on_model_change(
            self,
            data: dict,
            model: UserOrm,
            is_created: bool,
            request: Request,
    ) -> None:
        raw = data.get("hashed_password")
        if not is_created and (raw is None or raw == ""):
            data["hashed_password"] = model.hashed_password
            return

        if isinstance(raw, str):
            data["hashed_password"] = hash_password(raw)

class TasksAdmin(ModelView, model=TaskORM):
    column_list = [c.name for c in TaskORM.__table__.columns]
    name = "Задача"
    name_plural = "Задачи"
    icon = "fa-solid fa-tasks"
    column_labels = {"title": "Название", "description": "Описание", "status": "Статус", "priority": "Приоритет","term_date":"Срок выполнения", "author": "Автор"}

def init_admin(app):
    authentication_backend = AdminAuth(secret_key="...")
    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)
    admin.add_view(TasksAdmin)