import pytest
from celery.app.task import Task
from database.repositories.taskRepository import TaskRepository
from grbl.grblController import GrblController
from pytest_mock.plugin import MockerFixture
from typing import TextIO
from worker.tasks import executeTask


def test_execute_tasks(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def reset_commands_count():
        nonlocal commands_count
        commands_count = 0

    def increment_commands_count(command):
        nonlocal commands_count
        commands_count += 1

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch.object(TaskRepository, 'get_next_task')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

    queued_tasks = 2
    mock_ask_for_pending_tasks = mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        side_effect=[True, True, False]
    )

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, 'connect')
    mock_start_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(
        GrblController,
        'restartCommandsCount',
        side_effect=reset_commands_count
    )
    mock_stream_line = mocker.patch.object(
        GrblController,
        'sendCommand',
        side_effect=increment_commands_count
    )
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mock_get_grbl_buffer_fill = mocker.patch.object(
        GrblController,
        'getBufferFill',
        return_value=0
    )
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblController, 'alarm', return_value=False)
    mocker.patch.object(GrblController, 'failed', return_value=False)

    # Mock FS methods
    mocker.patch('worker.tasks.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocked_update_state = mocker.patch.object(Task, 'update_state')

    # Call method under test
    response = executeTask(
        admin_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert response is True
    assert mock_start_connect.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == queued_tasks + 1
    assert mock_get_next_task.call_count == queued_tasks
    assert mock_get_grbl_buffer_fill.call_count == 4 * queued_tasks
    assert mock_stream_line.call_count == 3 * queued_tasks
    mocked_update_state.assert_called()
    assert mock_update_task_status.call_count == 2 * queued_tasks
    assert mock_start_disconnect.call_count == 1


def test_no_tasks_to_execute(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch.object(TaskRepository, 'get_next_task')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
    mock_ask_for_pending_tasks = mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        return_value=False
    )

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')
    mock_stream_line = mocker.patch.object(GrblController, 'sendCommand')

    # Call method under test
    response = executeTask(
        admin_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert response is True
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == 1
    assert mock_get_next_task.call_count == 0
    assert mock_stream_line.call_count == 0
    assert mock_update_task_status.call_count == 0


def test_task_in_progress_exception(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=True)

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask(
            admin_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )
    assert str(error.value) == 'There is a task currently in progress, please wait until finished'


def test_task_missing_arguments():
    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask()
    assert str(error.value) == (
        "executeTask() missing 4 required positional arguments: "
        "'admin_id', 'base_path', 'serial_port', and 'serial_baudrate'"
    )


def test_execute_tasks_file_error(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch.object(TaskRepository, 'get_next_task')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
    mock_ask_for_pending_tasks = mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        return_value=True
    )

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, 'connect')
    mock_start_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')

    # Mock FS methods
    mocker.patch('worker.tasks.getFilePath')
    mocker.patch(
        'builtins.open',
        # The 'logging' module uses the 'open' method internally
        side_effect=[TextIO(), Exception('mocked-error')]
    )

    # Call method under test
    with pytest.raises(Exception):
        executeTask(
            admin_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    assert mock_start_connect.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == 1
    assert mock_get_next_task.call_count == 1
    assert mock_start_disconnect.call_count == 1
    assert mock_update_task_status.call_count == 0


def test_execute_tasks_waits_for_buffer(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def reset_commands_count():
        nonlocal commands_count
        commands_count = 0

    def increment_commands_count(command):
        nonlocal commands_count
        commands_count += 1

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_next_task')
    mocker.patch.object(TaskRepository, 'update_task_status')
    mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        side_effect=[True, False]
    )

    # Mock GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(
        GrblController,
        'restartCommandsCount',
        side_effect=reset_commands_count
    )
    mock_stream_line = mocker.patch.object(
        GrblController,
        'sendCommand',
        side_effect=increment_commands_count
    )
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mock_get_grbl_buffer_fill = mocker.patch.object(
        GrblController,
        'getBufferFill',
        side_effect=[100, 100, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
    )
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblController, 'alarm', return_value=False)
    mocker.patch.object(GrblController, 'failed', return_value=False)

    # Mock FS methods
    mocker.patch('worker.tasks.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocker.patch.object(Task, 'update_state')

    # Call method under test
    executeTask(
        admin_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert mock_get_grbl_buffer_fill.call_count == 6
    assert mock_stream_line.call_count == 3


@pytest.mark.parametrize(
    'is_alarm,is_error',
    [
        (True, False),
        (False, True)
    ]
)
def test_execute_tasks_grbl_error(mocker: MockerFixture, is_alarm, is_error):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_next_task')
    mocker.patch.object(TaskRepository, 'update_task_status')
    mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        side_effect=[True, False]
    )

    # Mock GRBL error methods
    mocker.patch.object(GrblController, 'alarm', return_value=is_alarm)
    mocker.patch.object(GrblController, 'failed', return_value=is_error)

    # Mock other GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mock_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblController, 'restartCommandsCount')
    mocker.patch.object(GrblController, 'sendCommand')
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mocker.patch.object(GrblController, 'getBufferFill', return_value=0)
    mocker.patch.object(GrblController, 'getCommandsCount', return_value=0)

    # Mock FS methods
    mocker.patch('worker.tasks.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocker.patch.object(Task, 'update_state')

    # Call method under test
    with pytest.raises(Exception) as error:
        executeTask(
            admin_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    expected = 'An alarm was triggered' if is_alarm else 'There was an error when executing line'
    assert mock_disconnect.call_count == 1
    assert expected in str(error.value)
