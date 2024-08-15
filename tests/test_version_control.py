from kit_vcs.utils import *
from kit_vcs.version_control import VersionControl


@pytest.fixture
def mock_drive_manager(mocker: MockerFixture):
    mock_drive = mocker.patch('kit_vcs.version_control.DriveManager')
    return mock_drive.return_value


@pytest.fixture
def version_control(mock_drive_manager):
    return VersionControl(username="test_user", workspace_path=Utils.parse_from_str_to_os_path("/mock/workspace"))


@pytest.fixture
def dir_exists_mock(mocker: MockerFixture):
    mock_exists = mocker.patch('kit_vcs.utils.path.isdir', return_value=True)
    mock_exists.patch('kit_vcs.utils.Utils.check_repository_exists', lambda x: x)
    return mock_exists


def test_init(version_control: VersionControl, mock_drive_manager):
    assert version_control.username == "test_user"
    assert version_control.workspace_path == Utils.parse_from_str_to_os_path("/mock/workspace")
    assert version_control.repo_path == path.abspath(path.join(version_control.workspace_path, '.kit'))
    assert version_control.index_path == Utils.parse_from_str_to_os_path('.kit/INDEX')

    mock_drive_manager.get_head.assert_called_once()
    mock_drive_manager.get_seed.assert_called_once()
    mock_drive_manager.get_last_commit_id.assert_called_once_with(mock_drive_manager.get_head())


def test_init_repo_already_exists(version_control: VersionControl, mock_drive_manager):
    mock_drive_manager.is_exist.return_value = True

    with pytest.raises(errors.AlreadyExistError):
        version_control.init()


def test_init_new_repo(version_control: VersionControl, mock_drive_manager, mocker: MockerFixture):
    mock_drive_manager.is_exist.return_value = False
    mock_commit = mocker.patch.object(version_control, 'commit', autospec=True)

    version_control.init()

    mock_drive_manager.initialize_directories.assert_called_once()
    mock_commit.assert_called_once_with("initial commit")
    mock_drive_manager.write.assert_any_call(path.join('.kit', 'HEAD'), version_control.head)
    mock_drive_manager.write.assert_any_call(path.join('.kit', version_control.head), version_control.current_id)


def test_add(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_commit_tree_hash = mock_drive_manager.get_commit_tree_hash.return_value

    version_control.add('test_path')

    mock_drive_manager.calculate_index_data.assert_called_once_with(
        'test_path', mock_commit_tree_hash, version_control.seed)
    mock_drive_manager.write_index_data.assert_called_once()
    mock_drive_manager.delete_if_empty.assert_called_once_with(Utils.parse_from_str_to_os_path('.kit/INDEX'))


def test_rm(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_commit_tree_hash = mock_drive_manager.get_commit_tree_hash.return_value

    version_control.rm('test_path')

    mock_drive_manager.calculate_index_data.assert_called_once_with(
        'test_path', mock_commit_tree_hash, version_control.seed, False)
    mock_drive_manager.write_index_data.assert_called_once()
    mock_drive_manager.delete_if_empty.assert_called_once_with(Utils.parse_from_str_to_os_path('.kit/INDEX'))


def test_index_success(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = True
    mock_drive_manager.read.return_value = "file1.txt,hash1,+\nfile2.txt,hash2,~\n"

    result = list(version_control.index())

    assert result == ["file1.txt,hash1,+", "file2.txt,hash2,~"]


def test_index_no_index_file(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = False

    result = list(version_control.index())

    assert result == []


def test_commit_no_changes(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = False

    with pytest.raises(errors.NothingToCommitError):
        version_control.commit("description")


def test_commits_list(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.read.side_effect = [
        "test_user\n2024-08-06T12:00:00\ninitial commit\n\nNone",
        "test_user\n2024-08-06T12:00:00\nsecond commit\n\ncommit1"
    ]

    mock_drive_manager.get_files_in_dir.return_value = ['commit1']
    version_control.current_id = "commit1"

    assert list(version_control.commits_list()) == [("commit1", "test_user", "2024-08-06T12:00:00", "initial commit")]


def test_create_branch(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = False

    version_control.create_branch("new_branch")

    mock_drive_manager.write.assert_called_once_with(Utils.parse_from_str_to_os_path('.kit/refs/heads/new_branch'),
                                                     version_control.current_id)


def test_create_branch_already_exists(version_control: VersionControl, mock_drive_manager,
                                      dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = True

    with pytest.raises(errors.AlreadyExistError):
        version_control.create_branch("existing_branch")


def test_branches_list(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.get_files_in_dir.return_value = ['branch1', 'branch2']

    assert list(version_control.branches_list()) == ['branch1', 'branch2']


def test_remove_branch(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = True
    mock_drive_manager.read.return_value = "commit_hash"
    version_control.head = "refs/heads/branch_to_remove"

    version_control.remove_branch("branch_to_remove")

    mock_drive_manager.write.assert_called_once_with(Utils.parse_from_str_to_os_path('.kit/HEAD'),
                                                     version_control.current_id)
    mock_drive_manager.remove.assert_called_once_with(
        Utils.parse_from_str_to_os_path('.kit/refs/heads/branch_to_remove'))


def test_create_tag(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = False

    version_control.create_tag("new_tag", "tag_description")

    mock_drive_manager.write.assert_called_once()


def test_create_tag_already_exists(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = True

    with pytest.raises(errors.AlreadyExistError):
        version_control.create_tag("existing_tag")


def test_tags_list(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.get_files_in_dir.return_value = ['tag1', 'tag2']
    mock_drive_manager.read.side_effect = ["tag_data1", "tag_data2"]

    assert list(version_control.tags_list()) == ['tag1\ntag_data1', 'tag2\ntag_data2']


def test_remove_tag(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = True

    version_control.remove_tag("tag_to_remove")

    mock_drive_manager.remove.assert_called_once_with(Utils.parse_from_str_to_os_path('.kit/refs/tags/tag_to_remove'))


def test_current_branch(version_control: VersionControl, mock_drive_manager, dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = False
    version_control.head = 'refs/heads/main'

    assert version_control.current_branch() == 'main'


def test_current_branch_not_on_branch(version_control: VersionControl, mock_drive_manager,
                                      dir_exists_mock: MockerFixture):
    mock_drive_manager.is_exist.return_value = True

    with pytest.raises(errors.NotOnBranchError):
        version_control.current_branch()


def test_get_branch_head_success(version_control: VersionControl, dir_exists_mock: MockerFixture, mock_drive_manager):
    mock_read = mock_drive_manager.read
    mock_drive_manager.is_exist.return_value = True

    version_control.get_branch_head("main")

    mock_read.assert_called_once_with(Utils.parse_from_str_to_os_path('.kit/refs/heads/main'))


def test_get_branch_head_fail(version_control: VersionControl, dir_exists_mock: MockerFixture, mock_drive_manager):
    mock_drive_manager.is_exist.return_value = False

    with pytest.raises(errors.NotFoundError):
        version_control.get_branch_head("main")


def test_commits_diff(version_control: VersionControl, mock_drive_manager, mocker: MockerFixture):
    mock_drive_manager.commit_to_tree_path.side_effect = ["path/to/tree1", "path/to/tree2"]
    mock_exists = mocker.patch('kit_vcs.utils.path.isdir', return_value=True)
    mock_exists.patch('kit_vcs.utils.Utils.check_repository_exists', lambda x: x)

    mock_tree_diff = ["file1.txt\n", "file2.txt\n"]

    mock_get_tree_diff = mocker.patch('kit_vcs.utils.Utils.get_tree_diff', return_value=mock_tree_diff)

    result = list(version_control.commits_diff("commit1_hash", "commit2_hash"))

    mock_get_tree_diff.assert_called_once_with("path/to/tree1", "path/to/tree2")

    assert result == mock_tree_diff


def test_files_diff(version_control: VersionControl, mock_drive_manager, mocker: MockerFixture):
    mock_exists = mocker.patch('kit_vcs.utils.path.isdir', return_value=True)
    mock_exists.patch('kit_vcs.utils.Utils.check_repository_exists', lambda x: x)

    mock_drive_manager.commit_to_tree_path.side_effect = ["path/to/tree1", "path/to/tree2"]
    mock_drive_manager.read.side_effect = ["file1_hash", "file2_hash"]
    mock_files_diff = ["line1\n", "line2\n"]

    mocker.patch.object(mock_drive_manager, 'get_files_diff', return_value=mock_files_diff)

    result = list(version_control.files_diff("commit1_hash", "commit2_hash", "test_file.txt"))

    assert result == mock_files_diff
