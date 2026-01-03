"""
Test to verify Slicer save() and load() methods work correctly.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from am.config import BuildParameters
from am.slicer import Slicer


def test_slicer_save_load():
    print("Testing Slicer save() and load() methods...\n")

    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 1. Create a Slicer instance
        print("1. Creating Slicer instance...")
        build_params = BuildParameters()
        slicer = Slicer(
            build_parameters=build_params,
            out_path=tmpdir_path,
            planar=True
        )
        print(f"   ✓ Created slicer with out_path: {slicer.out_path}")

        # 2. Save to default location (out_path/slicer.json)
        print("\n2. Saving to default location...")
        saved_path = slicer.save()
        print(f"   ✓ Saved to: {saved_path}")
        assert saved_path == tmpdir_path / "slicer.json"
        assert saved_path.exists()

        # 3. Verify the JSON content
        print("\n3. Verifying JSON content...")
        with open(saved_path, "r") as f:
            data = json.load(f)
        print(f"   Keys in JSON: {list(data.keys())}")
        assert "build_parameters" in data
        assert "out_path" in data
        assert "planar" in data
        assert data["planar"] == True
        assert "mesh" not in data  # Should be excluded
        assert "sections" not in data  # Should be excluded
        print("   ✓ JSON content is correct")

        # 4. Load from JSON
        print("\n4. Loading from JSON...")
        loaded_slicer = Slicer.load(saved_path)
        print(f"   ✓ Loaded slicer")
        print(f"   out_path: {loaded_slicer.out_path}")
        print(f"   planar: {loaded_slicer.planar}")
        print(f"   zfill: {loaded_slicer.zfill}")

        # 5. Verify loaded values match original
        print("\n5. Verifying loaded values...")
        assert loaded_slicer.out_path == slicer.out_path
        assert loaded_slicer.planar == slicer.planar
        assert loaded_slicer.zfill == slicer.zfill
        assert loaded_slicer.mesh is None  # Excluded fields should be None/empty
        assert loaded_slicer.sections == []
        print("   ✓ All values match")

        # 6. Test custom save path
        print("\n6. Testing custom save path...")
        custom_path = tmpdir_path / "custom_config.json"
        slicer.save(custom_path)
        assert custom_path.exists()
        print(f"   ✓ Saved to custom path: {custom_path}")

        # 7. Load from custom path
        print("\n7. Loading from custom path...")
        loaded_from_custom = Slicer.load(custom_path)
        assert loaded_from_custom.out_path == slicer.out_path
        print("   ✓ Loaded from custom path successfully")

        # 8. Test that BuildParameters are properly serialized/deserialized
        print("\n8. Testing BuildParameters serialization...")
        assert loaded_slicer.build_parameters.layer_height is not None
        print(f"   layer_height: {loaded_slicer.build_parameters.layer_height}")
        print("   ✓ BuildParameters preserved")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_slicer_save_load()
