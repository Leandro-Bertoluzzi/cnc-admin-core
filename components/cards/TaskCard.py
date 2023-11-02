from PyQt5.QtWidgets import QPushButton, QMessageBox
from celery.result import AsyncResult
from components.cards.Card import Card
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import Globals
from utils.database import update_task, remove_task
from database.models.task import TASK_DEFAULT_PRIORITY, TASK_IN_PROGRESS_STATUS

class TaskCard(Card):
    def __init__(self, task, files=[], tools=[], materials=[], parent=None):
        super(TaskCard, self).__init__(parent)

        self.task = task
        self.files = files
        self.tools = tools
        self.materials = materials

        description = f'Tarea {task.id}: {task.name}\nEstado: {task.status}'
        editTaskBtn = QPushButton("Editar")
        editTaskBtn.clicked.connect(self.updateTask)
        removeTaskBtn = QPushButton("Borrar")
        removeTaskBtn.clicked.connect(self.removeTask)

        if task.status == TASK_IN_PROGRESS_STATUS:
            task_id = Globals.get_current_task_id()
            celery_task = AsyncResult(task_id)
            progress = celery_task.info.get('progress')
            total = celery_task.info.get('total_lines')
            percentage = celery_task.info.get('percentage')
            description = f'Tarea {task.id}: {task.name}\nEstado: {task.status}\nProgreso: {progress}/{total} ({percentage}%)'

        self.setDescription(description)
        self.addButton(editTaskBtn)
        self.addButton(removeTaskBtn)

    def updateTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials, taskInfo=self.task)
        if taskDialog.exec():
            file_id, tool_id, material_id, name, note = taskDialog.getInputs()
            update_task(
                self.task.id,
                self.task.user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note,
                TASK_DEFAULT_PRIORITY
            )
            self.parent().refreshLayout()

    def removeTask(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar la tarea?')
        confirmation.setWindowTitle('Eliminar tarea')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            remove_task(self.task.id)
            self.parent().refreshLayout()
