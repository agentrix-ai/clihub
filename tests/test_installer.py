"""Tests for the installer manager."""

import asyncio

from cli_gateway.installer.manager import InstallerManager
from cli_gateway.models.provider import Provider


def _fake_provider(binary: str = "echo"):
    return Provider(
        name="fake", display_name="Fake", cli_binary=binary,
        install_command="echo 'installed'",
    )


def test_check_installed_existing_binary():
    mgr = InstallerManager()
    installed, version = asyncio.run(mgr.check_installed(_fake_provider("echo")))
    assert installed is True


def test_check_installed_nonexistent_binary():
    mgr = InstallerManager()
    installed, version = asyncio.run(mgr.check_installed(_fake_provider("nonexistent_binary_xyz")))
    assert installed is False
    assert version is None


def test_install_echo():
    mgr = InstallerManager()
    result = asyncio.run(mgr.install(_fake_provider()))
    assert result.success


def test_check_all():
    mgr = InstallerManager()
    providers = {
        "echo": _fake_provider("echo"),
        "missing": _fake_provider("nonexistent_xyz"),
    }
    results = asyncio.run(mgr.check_all(providers))
    assert results["echo"][0] is True
    assert results["missing"][0] is False
