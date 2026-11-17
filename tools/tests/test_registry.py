from refmeta.formats import all_formats


def test_registry_loads():
    for fid, fmt in all_formats().items():
        assert fmt.id == fid and callable(fmt.read)
