import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from database.models.task import Task
from views.TasksView import TasksView

class TestTaskCard:
    task = Task(
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name='Example task'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(TasksView, 'refreshLayout')

        # Patch the DB methods
        mocker.patch('views.TasksView.get_all_files_from_user', return_value=[])
        mocker.patch('views.TasksView.get_all_tools', return_value=[])
        mocker.patch('views.TasksView.get_all_materials', return_value=[])

        self.parent = TasksView()
        self.task.id = 1
        self.card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_task_card_init(self):
        assert self.card.task == self.task
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_update_task(self, mocker, dialogResponse, expected_updated):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch('components.cards.TaskCard.update_task')

        # Call the updateTask method
        self.card.updateTask()

        # Validate DB calls
        assert mock_update_task.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_task_params = {
                'id': 1,
                'user_id': 1,
                'file_id': 2,
                'tool_id': 3,
                'material_id': 4,
                'name': 'Updated task',
                'note': 'Just a simple description',
                'priority': 0,
            }
            mock_update_task.assert_called_with(*update_task_params.values())

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_task_card_remove_task(self, mocker, msgBoxResponse, expectedMethodCalls):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_task = mocker.patch('components.cards.TaskCard.remove_task')

        # Call the removeTask method
        self.card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == expectedMethodCalls
