from pytest_mock import MockerFixture
from utils import *
import platform
from drive_manager import DriveManager


@pytest.fixture
def drive_manager(mocker: MockerFixture):
    mocker.patch("os.makedirs")
    return DriveManager(workspace_path=Utils.parse_from_str_to_os_path('/fake/workspace'))


@pytest.fixture
def calculate_index_mock(mocker: MockerFixture):
    mock_isdir = mocker.patch('os.path.isdir')
    mock_exists = mocker.patch('os.path.exists')
    mock_open_fn = mocker.patch('builtins.open', mocker.mock_open())
    mock_hash = mocker.patch('utils.Utils.get_file_hash', return_value=mocker.Mock(hexdigest=lambda: 'filehash'))
    mock_walk = mocker.patch('os.walk')
    return mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk


@pytest.fixture
def save_tree_mock(mocker: MockerFixture):
    mock_makedirs = mocker.patch('os.makedirs')
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    mock_copy_tree = mocker.patch('drive_manager.copy_tree')
    return mock_makedirs, mock_exists, mock_copy_tree


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


def test_get_index_hashes(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='filepath,filehash,+\n'))

    result = drive_manager.get_index_hashes()

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/INDEX'), 'r')
    assert result == {'filepath': ('filehash', True)}


def test_get_head_success(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='commit_id'))

    result = drive_manager.get_head()

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/HEAD'), 'r')
    assert result == 'commit_id'


def test_get_head_no_path(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=False)
    assert drive_manager.get_head() is None


def test_get_seed_success(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='42'))

    result = drive_manager.get_seed()

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/SEED'), 'r')
    assert result == 42


def test_get_seed_no_path(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=False)
    assert drive_manager.get_seed() is None


def test_get_last_commit_id_success(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('builtins.open', mocker.mock_open(read_data='branch_path'))

    result = drive_manager.get_last_commit_id('commit_id')
    assert result == 'branch_path'


def test_get_last_commit_id_path_exists(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    assert drive_manager.get_last_commit_id('commit_id') == 'commit_id'


def test_get_last_commit_id_head_none(drive_manager: DriveManager):
    assert drive_manager.get_last_commit_id(None) is None


def test_get_commit_tree_hash_success(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=True)
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='user\n2024-01-01\ndescription\ntree\nparent'))

    result = drive_manager.get_commit_tree_hash('a1b2c3d4e5f6')

    mock_open.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'), 'r')
    assert result == 'tree'


def test_get_commit_tree_hash_no_path(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('os.path.exists', return_value=False)

    assert drive_manager.get_commit_tree_hash('a1b2c3d4e5f6') is None


def test_is_exist(drive_manager: DriveManager, mocker: MockerFixture):
    mock_exists = mocker.patch('os.path.exists', return_value=True)

    result = drive_manager.is_exist(Utils.parse_from_str_to_os_path('local/path'))

    mock_exists.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/local/path'))
    assert result is True


def test_delete_if_empty_file(drive_manager, mocker):
    mock_exist = mocker.patch('drive_manager.path.exists', return_value=True)
    mock_getsize = mocker.patch('drive_manager.path.getsize', return_value=0)
    mock_remove = mocker.patch('drive_manager.remove')

    drive_manager.delete_if_empty_file(Utils.parse_from_str_to_os_path('local/path'))
    full_path = Utils.parse_from_str_to_os_path('/fake/workspace/local/path')

    mock_exist.assert_called_once_with(full_path)
    mock_getsize.assert_called_once_with(full_path)
    mock_remove.assert_called_once_with(full_path)


def test_get_files_in_dir(drive_manager: DriveManager, mocker: MockerFixture):
    mock_walk = mocker.patch('drive_manager.walk',
                             return_value=[(Utils.parse_from_str_to_os_path('/fake/workspace/local_path'), [],
                                            ['file1', 'file2'])])

    result = list(drive_manager.get_files_in_dir('local_path'))

    mock_walk.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/local_path'))
    assert result == ['file1', 'file2']


def test_remove(drive_manager: DriveManager, mocker: MockerFixture):
    mock_remove = mocker.patch('os.remove')
    drive_manager.remove(Utils.parse_from_str_to_os_path('local/path'))
    mock_remove.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/local/path'))


def test_save_tree_add(drive_manager: DriveManager, save_tree_mock: (MockerFixture, MockerFixture, MockerFixture),
                       mocker: MockerFixture):
    mock_makedirs, mock_exists, mock_copy_tree = save_tree_mock
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    drive_manager.index_hashes = {'filepath/file': ('filehash', True)}
    drive_manager.save_tree('a1b2c3d4e5f6', 'p1e2v3h4a5s6')

    mock_makedirs.assert_called_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6/filepath'), exist_ok=True)
    mock_exists.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/p1/e2v3h4a5s6'))
    mock_copy_tree.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/p1/e2v3h4a5s6'),
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'))
    mock_open.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6/filepath/file'), 'w')


def test_save_tree_remove(drive_manager: DriveManager, save_tree_mock: (MockerFixture, MockerFixture, MockerFixture),
                          mocker: MockerFixture):
    mock_makedirs, mock_exists, mock_copy_tree = save_tree_mock
    mock_remove = mocker.patch('drive_manager.remove')

    drive_manager.index_hashes = {'filepath/file': ('filehash', False)}
    drive_manager.save_tree('a1b2c3d4e5f6', 'p1e2v3h4a5s6')

    mock_makedirs.assert_called_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6/filepath'), exist_ok=True)
    mock_exists.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/p1/e2v3h4a5s6'))
    mock_copy_tree.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/p1/e2v3h4a5s6'),
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'))
    mock_remove.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6/filepath/file'))


def test_save_files_from_index(drive_manager: DriveManager, mocker: MockerFixture):
    mock_save_file = mocker.patch.object(drive_manager, 'save_file')

    drive_manager.index_hashes = {'filepath': ('filehash', True)}
    drive_manager.save_files_from_index()

    mock_save_file.assert_called_once_with('filepath', 'filehash')


def test_calculate_index_data_file_not_in_prev_tree(drive_manager: DriveManager,
                                                    calculate_index_mock: (
                                                            MockerFixture, MockerFixture, MockerFixture, MockerFixture,
                                                            MockerFixture)):
    mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk = calculate_index_mock
    mock_isdir.return_value = False
    mock_exists.return_value = False

    filepath = Utils.parse_from_str_to_os_path('local/path')
    drive_manager.calculate_index_data(filepath, 'p1e2v3h4a5s6', 42)

    mock_hash.assert_called_once_with(Utils.parse_from_str_to_os_path('fake/workspace/local/path'),
                                      drive_manager.workspace_path, 42)
    assert drive_manager.index_hashes == {filepath: ('filehash', True)}


def test_calculate_index_data_file_differs_in_prev_tree(drive_manager: DriveManager,
                                                        calculate_index_mock: (
                                                                MockerFixture, MockerFixture, MockerFixture,
                                                                MockerFixture, MockerFixture)):
    mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk = calculate_index_mock
    mock_isdir.return_value = False
    mock_exists.side_effect = [True, False]
    mock_open_fn.return_value.read.return_value = 'different_hash'

    filepath = Utils.parse_from_str_to_os_path('local/path')
    drive_manager.calculate_index_data(filepath, 'p1e2v3h4a5s6', 42)

    mock_hash.assert_called_once_with(Utils.parse_from_str_to_os_path('fake/workspace/local/path'),
                                      drive_manager.workspace_path, 42)
    assert drive_manager.index_hashes == {filepath: ('filehash', True)}


def test_calculate_index_data_file_same_in_prev_tree(drive_manager: DriveManager,
                                                     calculate_index_mock: (
                                                             MockerFixture, MockerFixture, MockerFixture,
                                                             MockerFixture, MockerFixture)):
    mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk = calculate_index_mock
    mock_isdir.return_value = False
    mock_exists.side_effect = [True, True]
    mock_open_fn.return_value.read.return_value = 'filehash'

    filepath = Utils.parse_from_str_to_os_path('local/path')
    drive_manager.calculate_index_data(filepath, 'p1e2v3h4a5s6', 42)

    mock_hash.assert_called_once_with(Utils.parse_from_str_to_os_path('fake/workspace/local/path'),
                                      drive_manager.workspace_path, 42)
    assert drive_manager.index_hashes == {}


def test_calculate_index_data_remove_file(drive_manager: DriveManager,
                                          calculate_index_mock: (
                                                  MockerFixture, MockerFixture, MockerFixture,
                                                  MockerFixture, MockerFixture)):
    mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk = calculate_index_mock
    mock_isdir.return_value = False
    mock_exists.side_effect = [True, True]
    mock_open_fn.return_value.read.return_value = 'filehash'

    filepath = Utils.parse_from_str_to_os_path('local/path')
    drive_manager.index_hashes[filepath] = ('filehash', True)
    drive_manager.calculate_index_data(filepath, 'p1e2v3h4a5s6', 42, is_add=False)

    mock_hash.assert_called_once_with(Utils.parse_from_str_to_os_path('fake/workspace/local/path'),
                                      drive_manager.workspace_path, 42)
    assert drive_manager.index_hashes == {filepath: ('filehash', False)}


def test_calculate_index_data_remove_nonexistent_file(drive_manager: DriveManager,
                                                      calculate_index_mock: (
                                                              MockerFixture, MockerFixture, MockerFixture,
                                                              MockerFixture, MockerFixture)):
    mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk = calculate_index_mock
    mock_isdir.return_value = False
    mock_exists.return_value = False

    filepath = Utils.parse_from_str_to_os_path('local/path')
    drive_manager.index_hashes[filepath] = ('filehash', True)
    drive_manager.calculate_index_data(filepath, 'p1e2v3h4a5s6', 42, is_add=False)

    assert filepath not in drive_manager.index_hashes


def test_calculate_index_data_same_as_prev_but_dif_in_index(drive_manager: DriveManager,
                                                            calculate_index_mock: (
                                                                    MockerFixture, MockerFixture, MockerFixture,
                                                                    MockerFixture, MockerFixture)):
    mock_isdir, mock_exists, mock_open_fn, mock_hash, mock_walk = calculate_index_mock
    mock_isdir.return_value = False
    mock_exists.side_effect = [True, True]
    mock_open_fn.return_value.read.return_value = 'filehash'

    filepath = Utils.parse_from_str_to_os_path('local/path')
    drive_manager.index_hashes[filepath] = ('dif_filehash', True)
    drive_manager.calculate_index_data(filepath, 'p1e2v3h4a5s6', 42, is_add=True)

    mock_hash.assert_called_once_with(Utils.parse_from_str_to_os_path('fake/workspace/local/path'),
                                      drive_manager.workspace_path, 42)
    assert filepath not in drive_manager.index_hashes


def test_write_index_data(drive_manager: DriveManager, mocker: MockerFixture):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    drive_manager.index_hashes = {'filepath': ('filehash', True)}
    drive_manager.write_index_data()

    mock_open.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/INDEX'), 'w')
    mock_open().write.assert_called_once_with('filepath,filehash,+\n')


def test_rm_index_files(drive_manager: DriveManager, mocker: MockerFixture):
    mock_exists = mocker.patch('drive_manager.path.exists', return_value=True)
    mock_remove = mocker.patch('drive_manager.remove')

    drive_manager.index_hashes = {'filepath': ('filehash', False)}
    drive_manager.rm_index_files()
    filepath = Utils.parse_from_str_to_os_path('/fake/workspace/filepath')

    mock_exists.assert_called_once_with(filepath)
    mock_remove.assert_called_once_with(filepath)


def test_load_tree_files_success(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('drive_manager.walk', return_value=[
        (Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'), [], ['file'])])
    mocker.patch('drive_manager.makedirs')
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data='filehash'))
    mock_load_file = mocker.patch.object(drive_manager, 'load_file')

    drive_manager.load_tree_files('a1b2c3d4e5f6')

    mock_open.assert_called_once_with(
        Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6/file'), 'r')
    mock_load_file.assert_called_once_with('filehash', Utils.parse_from_str_to_os_path(
        'fake/workspace/./file'))


def test_load_tree_files_no_tree_hash(drive_manager: DriveManager, mocker: MockerFixture):
    drive_manager.load_tree_files('')
    mock_walk = mocker.patch('drive_manager.walk', return_value=[])
    mock_walk.assert_not_called()


def test_delete_tree_files_success(drive_manager: DriveManager, mocker: MockerFixture):
    mocker.patch('drive_manager.walk',
                 return_value=[(Utils.parse_from_str_to_os_path('/fake/workspace/.kit/objects/a1/b2c3d4e5f6'), ['dir'],
                                ['file'])])
    mocker.patch('drive_manager.path.exists', return_value=True)
    mock_remove = mocker.patch('drive_manager.remove')
    mock_rmdir = mocker.patch('drive_manager.rmdir')

    drive_manager.delete_tree_files('a1b2c3d4e5f6')

    mock_remove.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/file'))
    mock_rmdir.assert_called_once_with(Utils.parse_from_str_to_os_path('/fake/workspace/dir'))


def test_delete_tree_files_no_tree_hash(drive_manager: DriveManager, mocker: MockerFixture):
    drive_manager.delete_tree_files('')
    mock_walk = mocker.patch('drive_manager.walk', return_value=[])
    mock_walk.assert_not_called()
