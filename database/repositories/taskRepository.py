from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.task import Task, TASK_PENDING_APPROVAL_STATUS, TASK_IN_PROGRESS_STATUS, TASK_APPROVED_STATUS, TASK_REJECTED_STATUS, \
TASK_ON_HOLD_STATUS, TASK_CANCELLED_STATUS, TASK_EMPTY_NOTE
from datetime import datetime

class TaskRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_task(
        self,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = TASK_EMPTY_NOTE
    ):
        try:
            new_task = Task(
                user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note
            )
            self.session.add(new_task)
            self.session.commit()
            return new_task
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error creating the task in the DB: {e}')

    def _get_filtered_tasks(self, user_id: int, status: str):
        query = self.session.query(Task)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if status != 'all':
            query = query.filter_by(status=status)
        return query.order_by(Task.priority.asc()).all()

    def get_all_tasks_from_user(self, user_id: int, status: str = 'all'):
        try:
            tasks = self._get_filtered_tasks(user_id, status)
            for task in tasks:
                print(f'## Task: {task.name}')
                print(f'Owner: {task.user.name}')
                print(f'File: {task.file.file_name}')
                print(f'Tool: {task.tool.name}')
                print(f'Material: {task.material.name}')
                print(f'Admin: {"" if not task.admin else task.admin.name}')
            return tasks
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving tasks from the DB: {e}')

    def get_all_tasks(self, status: str = 'all'):
        try:
            tasks = self._get_filtered_tasks(user_id=None, status=status)
            for task in tasks:
                print(f'## Task: {task.name}')
                print(f'Owner: {task.user.name}')
                print(f'File: {task.file.file_name}')
                print(f'Tool: {task.tool.name}')
                print(f'Material: {task.material.name}')
                print(f'Admin: {"" if not task.admin else task.admin.name}')
            return tasks
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving tasks from the DB: {e}')

    def get_next_task(self):
        try:
            task = self.session.query(Task).filter_by(status=TASK_ON_HOLD_STATUS).order_by(Task.priority.desc()).first()
            if task:
                print(f'## Task: {task.name}')
                print(f'Owner: {task.user.name}')
                print(f'File: {task.file.file_name}, {task.file.file_path}')
                print(f'Tool: {task.tool.name}')
                print(f'Material: {task.material.name}')
                print(f'Admin: {"" if not task.admin else task.admin.name}')
            return task
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving tasks from the DB: {e}')

    def update_task(
        self,
        id: int,
        user_id: int,
        file_id: int = None,
        tool_id: int = None,
        material_id: int = None,
        name: str = None,
        note: str = None,
        priority: int = None,
    ):
        try:
            task = self.session.query(Task).get(id)
            if not task or task.user_id != user_id:
                raise Exception(f'Task with ID {id} was not found for this user')

            task.file_id = file_id or task.file_id
            task.tool_id = tool_id or task.tool_id
            task.material_id = material_id or task.material_id
            task.name = name or task.name
            task.note = note or task.note
            task.priority = priority or task.priority

            self.session.commit()
            return task
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error updating task with ID {id} in DB: {e}')

    def update_task_status(
        self,
        id: int,
        status: str,
        admin_id: int = None,
        cancellation_reason: str = "",
    ):
        try:
            task = self.session.query(Task).get(id)
            if not task:
                raise Exception(f'Task with ID {id} was not found for this user')

            approved = task.status == TASK_PENDING_APPROVAL_STATUS and status == TASK_APPROVED_STATUS
            rejected = task.status == TASK_PENDING_APPROVAL_STATUS and status == TASK_REJECTED_STATUS

            task.status = status
            task.status_updated_at = datetime.now()

            if approved or rejected:
                task.admin_id = admin_id

            if status == TASK_PENDING_APPROVAL_STATUS:
                task.admin_id = None
                task.status_updated_at = None

            if status == TASK_CANCELLED_STATUS or rejected:
                task.cancellation_reason = cancellation_reason

            self.session.commit()
            return task
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error updating the task status in the DB: {e}')

    def remove_task(self, id: int):
        try:
            task = self.session.query(Task).get(id)
            if not task:
                raise Exception(f'Task with ID {id} was not found')

            self.session.delete(task)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error removing the task from the DB: {e}')

    def are_there_tasks_with_status(self, status: str) -> bool:
        tasks = self.session.query(Task).filter_by(status=status).all()
        return bool(tasks)

    def are_there_pending_tasks(self) -> bool:
        return self.are_there_tasks_with_status(TASK_ON_HOLD_STATUS)

    def are_there_tasks_in_progress(self) -> bool:
        return self.are_there_tasks_with_status(TASK_IN_PROGRESS_STATUS)

    def close_session(self):
        self.session.close()
