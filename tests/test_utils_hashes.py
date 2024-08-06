from utils import *


def test_file_hash_same_files(tmp_path):
    local_path_1 = tmp_path / "test.txt"
    local_path_1.write_bytes(b"Hello, World!")
    assert Utils.get_file_hash(str(local_path_1), xxh3_128(seed=123)).hexdigest() == Utils.get_file_hash(
        str(local_path_1), xxh3_128(seed=123)).hexdigest()


def test_file_hash_same_names(tmp_path):
    local_path_1 = tmp_path / "test.txt"
    local_path_1.write_bytes(b"Hello, World!")
    hash1 = Utils.get_file_hash(str(local_path_1), xxh3_128(seed=123)).hexdigest()
    local_path_1.write_bytes(b"Hello!")
    assert Utils.get_file_hash(str(local_path_1), xxh3_128(seed=123)).hexdigest() != hash1


def test_file_hash_same_content(tmpdir):
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
        Utils.get_file_hash(str(tmpdir), xxh3_128())


def test_dir_hash_same_dirs(tmpdir):
    tmpdir1 = tmpdir.mkdir("test1")
    tmpdir1.join("test.txt").write(b"hello")
    assert Utils.get_dir_hash(str(tmpdir1), xxh3_128()).hexdigest() == Utils.get_dir_hash(str(tmpdir1),
                                                                                          xxh3_128()).hexdigest()


def test_dir_hash_same_names(tmpdir):
    tmpdir1 = tmpdir.mkdir("test1")
    tmpdir1.join("test.txt").write(b"hello")
    hash1 = Utils.get_dir_hash(str(tmpdir), xxh3_128()).hexdigest()
    tmpdir1.join("test.txt").write(b"hello1")
    assert hash1 != Utils.get_dir_hash(str(tmpdir1), xxh3_128()).hexdigest()


def test_dir_hash_same_content(tmpdir):
    tmpdir1 = tmpdir.mkdir("test1")
    tmpdir2 = tmpdir.mkdir("test2")
    tmpdir1.join("test.txt").write(b"hello")
    tmpdir2.join("test.txt").write(b"hello")

    assert Utils.get_dir_hash(str(tmpdir1), xxh3_128()).hexdigest() != Utils.get_dir_hash(str(tmpdir2),
                                                                                          xxh3_128()).hexdigest()


def test_dir_hash_not_a_dir(tmp_path):
    with pytest.raises(AssertionError) as e_info:
        Utils.get_dir_hash(str(tmp_path / "test.txt"), xxh3_128())
