"""Check that the installer only includes the reviewed disk in its storage plan."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build/branding/product/usr/libexec/anypc-setup"))
import backend


class InstallationPlanTests(unittest.TestCase):
    disk = backend.Disk("/dev/vdb", "Test disk", 40 * 1024**3, "serial", "252:16", "", "2")

    def plan(self, mode="automatic"):
        return backend.validate_plan(self.disk, mode, 2048, 1024, "setuptest", "example-test",
                                     "ro", "Europe/Bucharest", "ro")

    def test_disk_scope_and_credentials(self):
        for mode in ("automatic", "custom"):
            for uefi in (True, False):
                ks = backend.kickstart(self.plan(mode), "$6$test$hash", uefi)
                self.assertIn("ignoredisk --only-use=vdb\n", ks)
                self.assertIn("clearpart --all --initlabel --disklabel=gpt --drives=vdb\n", ks)
                self.assertNotIn("example-test", ks)
                self.assertNotIn("zerombr", ks)
                for line in ks.splitlines():
                    if line.startswith("part "):
                        self.assertTrue(line.endswith("--ondisk=vdb"))

    def test_excludes_live_media_and_active_partitions(self):
        for child in ({"type": "part", "mountpoints": ["/run/install/repo"]},
                      {"type": "part", "fstype": "iso9660"}, {"type": "crypt"}):
            self.assertTrue(backend.occupied({"type": "disk", "children": [child]}))

    def test_disk_change_aborts_before_install(self):
        import tempfile
        from dataclasses import replace
        with tempfile.TemporaryDirectory() as work, patch.object(backend, "RUN_DIR", Path(work)), \
                patch.object(backend, "discover_disks", return_value=[replace(self.disk, sequence="3")]), \
                patch.object(backend.subprocess, "check_output", return_value="$6$test$hash"), \
                patch.object(backend.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "disk changed"):
                backend._deploy(self.plan(), lambda phase: None)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
