from utils import *


def test_file_hash_same_files(tmp_path):
    local_path_1 = tmp_path / "test.txt"
    local_path_1.write_bytes(b"Hello, World!")
    assert Utils.get_file_hash(str(local_path_1), xxh3_128(seed=123)).hexdigest() == Utils.get_file_hash(
        str(local_path_1), xxh3_128(seed=123)).hexdigest()


def test_file_hash_same_content(tmp_path):
    local_path_1 = tmp_path / "test.txt"
    local_path_1.write_bytes(b"Hello, World!")

    local_path_2 = tmp_path / "test1.txt"
    local_path_2.write_bytes(b"Hello, World!")
    assert Utils.get_file_hash(str(local_path_1), xxh3_128(seed=123)).hexdigest() != Utils.get_file_hash(
        str(local_path_2), xxh3_128(seed=123)).hexdigest()


def test_file_hash_same_names(tmpdir):
    tmpdir1 = tmpdir.mkdir("test1")
    tmpdir2 = tmpdir.mkdir("test2")
    local_path_1 = tmpdir1.join("test.txt")
    local_path_1.write(b"hello")
    local_path_2 = tmpdir2.join("test.txt")
    local_path_2.write(b"hello")

    assert Utils.get_file_hash(str(local_path_1), xxh3_128()).hexdigest() != Utils.get_file_hash(str(local_path_2),
                                                                                                 xxh3_128()).hexdigest()


def test_file_hash_not_a_file(tmpdir):
    with pytest.raises(AssertionError) as e_info:
        Utils.get_file_hash(tmpdir, xxh3_128())
        assert True
