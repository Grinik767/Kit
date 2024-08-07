from kit_vcs.utils import *


def test_check_repository_exists_success(mocker: MockerFixture):
    mocker.patch('kit_vcs.utils.path.isdir', return_value=True)
    Utils.workspace_path = '/mock/workspace'
    method = mocker.MagicMock()

    decorated_method = Utils.check_repository_exists(method)
    decorated_method(Utils)
    method.assert_called_once()


def test_check_repository_exists_fail(mocker: MockerFixture):
    mocker.patch('kit_vcs.utils.path.isdir', return_value=False)
    Utils.workspace_path = '/mock/workspace'
    method = mocker.MagicMock()

    decorated_method = Utils.check_repository_exists(method)
    with pytest.raises(errors.RepositoryExistError):
        decorated_method(Utils)


def test_get_tree_diff(mocker: MockerFixture):
    mocker.patch('kit_vcs.utils.Utils._Utils__compare_trees',
                 return_value=({'added_file'}, {'removed_file'}, {'changed_file'}))
    diff = Utils.get_tree_diff('/path/to/tree1', '/path/to/tree2')
    assert diff == ['+;added_file', '~;changed_file', '-;removed_file']


def test_get_file_hash(tmp_path, mocker: MockerFixture):
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("content")
    file_path = str(test_file)
    workspace_path = str(tmp_path)
    seed = 0
    mocker.patch('kit_vcs.utils.path.isfile', return_value=True)

    hash_value = Utils.get_file_hash(file_path, workspace_path, seed)
    expected_hash = xxh3_128(path.relpath(file_path, start=workspace_path), seed=seed)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            expected_hash.update(chunk)

    assert hash_value.hexdigest() == expected_hash.hexdigest()


def test_get_string_hash():
    test_string = "test"
    seed = 0
    hash_value = Utils.get_string_hash(test_string, seed)
    expected_hash = xxh3_128(test_string, seed=seed)
    assert hash_value.hexdigest() == expected_hash.hexdigest()


def test_get_tree_hash(tmp_path, mocker: MockerFixture):
    index_file = tmp_path / "INDEX"
    index_file.write_text("file1.txt,hash1,+\nfile2.txt,hash2,~")
    workspace_path = str(tmp_path)
    seed = 0
    mocker.patch('kit_vcs.utils.path.isfile', return_value=True)

    hash_value = Utils.get_tree_hash(workspace_path, seed)
    expected_hash = xxh3_128('kit', seed=seed)
    with open(index_file, 'r') as f:
        for line in f:
            local_path, file_hash, diff_type = line.split(',')
            expected_hash.update(file_hash.strip())

    assert hash_value.hexdigest() == expected_hash.hexdigest()


def test_bool_to_sign():
    assert Utils.bool_to_sign(True) == "+"
    assert Utils.bool_to_sign(False) == "-"


def test_sign_to_bool():
    assert Utils.sign_to_bool("+") is True
    assert Utils.sign_to_bool("-") is False


def test_parse_from_str_to_os_path():
    assert Utils.parse_from_str_to_os_path("a/b/c") == path.join("a", "b", "c")


def test_check_for_dot_path(mocker: MockerFixture):
    mocker.patch('kit_vcs.utils.path.isfile', return_value=True)
    assert Utils.check_for_dot_path("a\\.b\\c.txt") is True
    assert Utils.check_for_dot_path("a\\b\\c.txt") is False

    mocker.patch('kit_vcs.utils.path.isfile', return_value=False)
    assert Utils.check_for_dot_path("a\\.b\\c") is True
    assert Utils.check_for_dot_path("a\\b\\c") is False
