import tempfile
from pathlib import Path
from ckpt.core import snapshot, store, manifest


def test_save_and_restore():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)

        # Create project files
        (p / "top.v").write_text("module top(); endmodule")
        (p / "constraints.xdc").write_text("set_property PACKAGE_PIN A1 [get_ports clk]")

        # Snapshot + save
        entries = snapshot.take(root=tmp)
        oid, stats = store.write(entries, root=tmp)
        m = manifest.create(oid, "initial save", entries, stats)
        manifest.save(m, root=tmp)

        # Modify a file
        (p / "top.v").write_text("module top(); // BROKEN endmodule")

        # Restore
        loaded = manifest.load_by_id(oid[:7], root=tmp)
        assert loaded is not None
        store.restore(loaded, root=tmp)

        # Verify restored content
        restored = (p / "top.v").read_text()
        assert "BROKEN" not in restored
        assert "module top();" in restored


def test_list_manifests():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "top.v").write_text("v1")

        entries = snapshot.take(root=tmp)
        oid, stats = store.write(entries, root=tmp)
        m = manifest.create(oid, "first checkpoint", entries, stats)
        manifest.save(m, root=tmp)

        all_m = manifest.load_all(root=tmp)
        assert len(all_m) == 1
        assert all_m[0].message == "first checkpoint"
