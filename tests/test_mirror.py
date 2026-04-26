from pathlib import Path

from mdmirror.mirror import output_is_inside_input, to_output_path


def test_doc_gets_double_extension(tmp_path: Path) -> None:
    src = tmp_path / "in" / "a" / "report.docx"
    src.parent.mkdir(parents=True)
    src.touch()
    out = to_output_path(src, tmp_path / "in", tmp_path / "out")
    assert out == tmp_path / "out" / "a" / "report.docx.md"


def test_md_passes_through(tmp_path: Path) -> None:
    src = tmp_path / "in" / "README.md"
    src.parent.mkdir(parents=True)
    src.touch()
    out = to_output_path(src, tmp_path / "in", tmp_path / "out")
    assert out == tmp_path / "out" / "README.md"


def test_collision_avoided(tmp_path: Path) -> None:
    in_root = tmp_path / "in"
    in_root.mkdir()
    (in_root / "x.docx").touch()
    (in_root / "x.pdf").touch()

    a = to_output_path(in_root / "x.docx", in_root, tmp_path / "out")
    b = to_output_path(in_root / "x.pdf", in_root, tmp_path / "out")
    assert a != b


def test_output_inside_input_detected(tmp_path: Path) -> None:
    in_root = tmp_path / "in"
    in_root.mkdir()
    out_root = in_root / "ghost"
    assert output_is_inside_input(in_root, out_root)
    assert not output_is_inside_input(in_root, tmp_path / "elsewhere")
