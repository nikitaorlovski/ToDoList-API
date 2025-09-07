import bcrypt
from markupsafe import Markup, escape
from sqladmin import Admin, ModelView
from wtforms import PasswordField

from db.database import engine
from db.models.task import TaskORM
from db.models.user import UserOrm


# удобное представление задачи (покажется в списках/деталях)
def _task_repr(t: TaskORM) -> str:
    return f"{t.id}: {t.title}"


TaskORM.__repr__ = _task_repr  # опционально


class UserAdmin(ModelView, model=UserOrm):
    # включим страницу "Details"
    can_view_details = True

    # что показывать в списке пользователей
    column_list = [
        UserOrm.id,
        UserOrm.name,
        UserOrm.email,
        "hashed_password_short",
        "tasks_count",
    ]

    # что показывать в деталях пользователя
    column_details_list = [
        UserOrm.id,
        UserOrm.name,
        UserOrm.email,
        "hashed_password_full",
        "tasks_list",
    ]

    column_labels = {
        "hashed_password_short": "Password hash (short)",
        "hashed_password_full": "Password hash",
        "tasks_count": "Tasks count",
        "tasks_list": "Tasks",
    }

    # формы: пароль вводим только при создании, хеш и задачи из форм убираем
    form_create_rules = ("name", "email", "password")
    form_edit_rules = ("name", "email")
    form_excluded_columns = [UserOrm.hashed_password, UserOrm.tasks]
    form_extra_fields = {"password": PasswordField("Password")}

    # ----- форматтеры для колонок / деталей -----
    @staticmethod
    def _hash_short(model: UserOrm) -> str:
        if not model.hashed_password:
            return ""
        h = model.hashed_password.decode()  # bcrypt — ascii
        return h[:32] + "…" if len(h) > 32 else h

    @staticmethod
    def _hash_full(model: UserOrm) -> str:
        return model.hashed_password.decode() if model.hashed_password else ""

    @staticmethod
    def _tasks_count(model: UserOrm) -> int:
        return len(model.tasks or [])

    @staticmethod
    def _tasks_list(model: UserOrm) -> Markup:
        if not model.tasks:
            return Markup("<em>No tasks</em>")
        items = "".join(f"<li>{escape(t.title)}</li>" for t in model.tasks)
        return Markup(f"<ul>{items}</ul>")

    column_formatters = {
        "hashed_password_short": lambda m, a: UserAdmin._hash_short(m),
        "tasks_count": lambda m, a: UserAdmin._tasks_count(m),
    }
    column_formatters_detail = {
        "hashed_password_full": lambda m, a: UserAdmin._hash_full(m),
        "tasks_list": lambda m, a: UserAdmin._tasks_list(m),
    }

    # при сохранении создаём/обновляем хеш, если ввели пароль
    def on_model_change(self, form, model, is_created):
        pwd = getattr(form, "password", None)
        if pwd and pwd.data:
            model.hashed_password = bcrypt.hashpw(
                pwd.data.encode("utf-8"), bcrypt.gensalt()
            )
        return super().on_model_change(form, model, is_created)


class TaskAdmin(ModelView, model=TaskORM):
    can_view_details = True
    column_list = [TaskORM.id, TaskORM.title, TaskORM.author_id]
    column_details_list = [
        TaskORM.id,
        TaskORM.title,
        TaskORM.description,
        TaskORM.author_id,
    ]


def init_admin(app):
    admin = Admin(app, engine)
    admin.add_view(UserAdmin)
    admin.add_view(TaskAdmin)
    return admin
