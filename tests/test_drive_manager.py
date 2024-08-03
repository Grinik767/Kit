from pytest_mock import MockerFixture

from utils import *
import platform
from drive_manager import DriveManager


@pytest.fixture
def drive_manager(mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.makedirs')
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('lzma.open', mocker.mock_open())
    mocker.patch('drive_manager.DriveManager.get_index_hashes', return_value={})
    return DriveManager(workspace_path=Utils.parse_from_str_to_os_path('/fake/workspace'))


def test_save_file(drive_manager: DriveManager, mocker: MockerFixture):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data=b'test data'))
    mock_lzma_open = mocker.patch('lzma.open', mocker.mock_open())

    drive_manager.save_file(Utils.parse_from_str_to_os_path('local/path'), 'a1b2c3d4e5f6')

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/local/path'), 'rb')
    mock_lzma_open.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'), 'wb')


def test_load_file(drive_manager: DriveManager, mocker: MockerFixture):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_lzma_open = mocker.patch('lzma.open', mocker.mock_open(read_data=b'test data'))

    drive_manager.load_file('a1b2c3d4e5f6', Utils.parse_from_str_to_os_path('output/path'))

    mock_lzma_open.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'), 'rb')
    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('output/path'), 'wb')


def test_write(drive_manager: DriveManager, mocker: MockerFixture):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    drive_manager.write(Utils.parse_from_str_to_os_path('local/path'), 'data')

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/local/path'), 'w')
    mock_open().write.assert_called_once_with('data')


def test_read(drive_manager: DriveManager, mocker: MockerFixture):
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='data'))

    result = drive_manager.read(Utils.parse_from_str_to_os_path('local/path'))

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/local/path'), 'r')
    assert result == 'data'


def test_write_commit_data(drive_manager: DriveManager, mocker: MockerFixture):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    drive_manager.write_commit_data('a1b2c3d4e5f6', 'username', '2024-01-01', 'description', 'tree', 'parent')

    mock_open.assert_called_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'), 'w')
    mock_open().write.assert_called_once_with('username\n2024-01-01\ndescription\ntree\nparent')


def test_initialize_directories(drive_manager: DriveManager, mocker: MockerFixture):
    mock_makedirs = mocker.patch('os.makedirs')
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_subprocess = mocker.patch('subprocess.run')

    drive_manager.initialize_directories()

    expected_calls = [
        mocker.call(Utils.parse_from_str_to_os_path('/fake/workspace/.kit'), exist_ok=True),
        mocker.call(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects'), exist_ok=True),
        mocker.call(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/refs'), exist_ok=True),
        mocker.call(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/refs/heads'), exist_ok=True),
        mocker.call(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/refs/tags'), exist_ok=True),
    ]
    mock_makedirs.assert_has_calls(expected_calls, any_order=True)
    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/INDEX'), 'w')
    if platform.system() == "Windows":
        mock_subprocess.assert_called_once_with(
            ['attrib', '+H', Utils.parse_from_str_to_os_path('/fake/workspace/.kit')], check=True)


'''def test_get_index_hashes(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='filepath,filehash,+\n'))

    result = drive_manager.get_index_hashes()

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/INDEX'), 'r')
    assert result == {'filepath': ('filehash', True)}
'''


def test_get_head(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='commit_id'))

    result = drive_manager.get_head()

    mock_open.assert_called_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/HEAD'), 'r')
    assert result == 'commit_id'
