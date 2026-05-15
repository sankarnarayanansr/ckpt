import tempfile
from pathlib import Path
from ckpt.core.snapshot import take, sha256_stream


def test_snapshot_basic():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "top.v").write_text("module top(); endmodule")
        (p / "constraints.xdc").write_text("set_property PACKAGE_PIN A1 [get_ports clk]")

        entries = take(root=tmp)
        assert len(entries) == 2
        paths = [e["path"] for e in entries]
        assert "top.v" in paths
        assert "constraints.xdc" in paths


def test_dedup_same_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        content = b"same content"
        (p / "a.v").write_bytes(content)
        (p / "b.v").write_bytes(content)

        entries = take(root=tmp)
        hashes = [e["hash"] for e in entries]
        assert hashes[0] == hashes[1]  # same hash for identical files


def test_ignore_ckpt_dir():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "top.v").write_text("module top(); endmodule")
        (p / ".ckpt").mkdir()
        (p / ".ckpt" / "HEAD").write_text("abc123")

        entries = take(root=tmp)
        paths = [e["path"] for e in entries]
        assert not any(".ckpt" in path for path in paths)
