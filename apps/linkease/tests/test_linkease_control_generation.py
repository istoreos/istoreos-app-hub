import subprocess
import textwrap
import unittest


class LinkEaseControlGenerationTest(unittest.TestCase):
    def test_package_local_control_extension_preserves_generated_fields(self):
        makefile = textwrap.dedent(
            r"""
            PKG_NAME:=linkease-common-bin
            VERSION:=1.7.6~8664-r1
            EXTRA_DEPENDS:=libc

            define BuildPackage
            define Package/$(1)/CONTROL
            Package: $(1)
            Version: $$(VERSION)
            $$(if $$(EXTRA_DEPENDS),Depends: $$(EXTRA_DEPENDS)
            )Architecture: all
            endef
            control: export CONTROL=$$(Package/$(1)/CONTROL)
            control:
	@printf '%s\n' "$$$$CONTROL"
            endef

            $(eval $(call BuildPackage,$(PKG_NAME)))

            LINKEASE_COMMON_BIN_GENERATED_CONTROL := $(Package/$(PKG_NAME)/CONTROL)
            define Package/$(PKG_NAME)/CONTROL
            $(LINKEASE_COMMON_BIN_GENERATED_CONTROL)
            Replaces: linkease (<< 1.7.6~)
            endef
            """
        )

        result = subprocess.run(
            ["make", "--no-print-directory", "-f", "/dev/stdin", "control"],
            input=makefile,
            text=True,
            check=True,
            capture_output=True,
        )

        self.assertEqual(
            [
                "Package: linkease-common-bin",
                "Version: 1.7.6~8664-r1",
                "Depends: libc",
                "Architecture: all",
                "Replaces: linkease (<< 1.7.6~)",
            ],
            [line.strip() for line in result.stdout.splitlines()],
        )

    def test_extra_depends_preserves_version_relation(self):
        makefile = textwrap.dedent(
            r"""
            define Package/linkease
              DEPENDS:=+linkease-common-bin
              EXTRA_DEPENDS:=linkease-common-bin (>=1.7.6~0)
            endef
            $(eval $(Package/linkease))
            $(info Depends: $(EXTRA_DEPENDS))
            all: ; @:
            """
        )

        result = subprocess.run(
            ["make", "--no-print-directory", "-f", "/dev/stdin"],
            input=makefile,
            text=True,
            check=True,
            capture_output=True,
        )

        self.assertEqual(
            "Depends: linkease-common-bin (>=1.7.6~0)", result.stdout.strip()
        )


if __name__ == "__main__":
    unittest.main()
