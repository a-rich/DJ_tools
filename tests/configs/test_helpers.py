"""Testing for the helpers module."""

import inspect
import logging
from pathlib import Path
import re
from unittest import mock

from pip._vendor import tomli
import pytest

from djtools.configs.helpers import (
    _arg_parse,
    BaseConfig,
    build_config,
    _filter_dict,
    PKG_CFG,
)
from djtools.version import get_version

from ..test_utils import mock_exists, MockOpen


@pytest.mark.parametrize(
    "log_level_name, log_level", [("DEBUG", 10), ("WARNING", 30)]
)
@mock.patch("argparse.ArgumentParser.parse_args")
def test_arg_parse_sets_log_level(
    mock_parse_args, namespace, log_level_name, log_level
):
    """Test for the arg_parse function."""
    namespace.log_level = log_level_name
    mock_parse_args.return_value = namespace
    _arg_parse()
    logger = logging.getLogger("djtools.configs.helpers")
    assert logger.getEffectiveLevel() == log_level


@mock.patch("argparse.ArgumentParser.parse_args")
def test_arg_parse_gets_version(mock_parse_args, namespace, capsys):
    """Test for the arg_parse function."""
    namespace.version = True
    mock_parse_args.return_value = namespace
    with pytest.raises(SystemExit):
        _arg_parse()
    with open(
        Path(__file__).parent.parent.parent / "pyproject.toml", mode="rb"
    ) as _file:
        toml_dict = tomli.load(_file)
    assert (
        capsys.readouterr().out.replace(".", "").strip()
        == toml_dict["project"]["version"].replace(".", "").strip()
    )


@mock.patch("argparse.ArgumentParser.parse_args")
def test_arg_parse_links_configs_dir_does_exist(
    mock_parse_args, tmpdir, namespace
):
    """Test for the arg_parse function."""
    config_path = Path(tmpdir) / "new_dir" / "link_dir"
    namespace.link_configs = config_path
    mock_parse_args.return_value = namespace
    assert not config_path.parent.exists()
    _arg_parse()
    assert config_path.exists()
    assert config_path.is_symlink()


@mock.patch("argparse.ArgumentParser.parse_args")
def test_arg_parse_links_configs_dir_parent_does_not_exist(
    mock_parse_args, tmpdir, namespace
):
    """Test for the arg_parse function."""
    config_path = str(tmpdir)
    namespace.link_configs = config_path
    mock_parse_args.return_value = namespace
    with pytest.raises(
        ValueError,
        # NOTE(a-rich): WindowsPath needs to be escaped for `\` characters to
        # appear in the `match` argument.
        match=re.escape(
            f"{config_path} must be a directory that does not already exist"
        ),
    ):
        _arg_parse()


@mock.patch(
    "builtins.open",
    MockOpen(
        files=["config.yaml"],
        content="yaml_valid: {false",
    ).open,
)
def test_build_config_invalid_config_yaml(caplog):
    """Test for the build_config function."""
    caplog.set_level("CRITICAL")
    with (
        mock.patch.object(Path, "exists", return_value=True),
        pytest.raises(RuntimeError),
    ):
        build_config()
    assert 'Error reading "config.yaml"' in caplog.records[0].message


@mock.patch("djtools.spotify.helpers.get_spotify_client", mock.Mock())
@mock.patch("argparse.ArgumentParser.parse_args")
def test_build_config_no_config_yaml(
    mock_parse_args, namespace, config_file_teardown
):
    """Test for the build_config function."""
    # pylint: disable=unused-argument
    mock_parse_args.return_value = namespace
    config_dir = (
        Path(__file__).parent.parent.parent / "src" / "djtools" / "configs"
    )
    config_file = config_dir / "config.yaml"
    assert not config_file.exists()
    build_config()
    assert config_file.exists()


@mock.patch(
    "builtins.open",
    MockOpen(
        files=["config.yaml"],
        content="configs:\n  ARTIST_FIRST: false",
    ).open,
)
@mock.patch(
    "djtools.configs.helpers.Path.exists",
    lambda path: mock_exists(
        [
            ("config.yaml", True),
        ],
        path,
    ),
)
@mock.patch("argparse.ArgumentParser.parse_args")
def test_build_config_overrides_using_args(mock_parse_args, namespace):
    """Test for the build_config function."""
    namespace.artist_first = True
    mock_parse_args.return_value = namespace
    config = build_config()
    assert config.ARTIST_FIRST is True


@mock.patch("argparse.ArgumentParser.parse_args")
def test_build_config_reads_generated_config(
    mock_parse_args, namespace, config_file_teardown
):
    """Test for the build_config function."""
    # pylint: disable=unused-argument
    namespace.log_level = "INFO"
    mock_parse_args.return_value = namespace
    config_dir = (
        Path(__file__).parent.parent.parent / "src" / "djtools" / "configs"
    )
    config_file = config_dir / "config.yaml"

    # config.yaml won't exist so build_config generates one.
    assert not config_file.exists()
    first_config = build_config()

    # config.yaml now exists so build_config reads the pre-existing one.
    assert config_file.exists()
    second_config = build_config()

    # Both configs should be identical.
    assert first_config == second_config


@mock.patch(
    "builtins.open",
    MockOpen(
        files=["config.yaml"],
        write_only=True,
    ).open,
)
@mock.patch("argparse.ArgumentParser.parse_args")
def test_build_config_version(mock_parse_args, namespace, capsys):
    """Test for the build_config function."""
    namespace.version = True
    mock_parse_args.return_value = namespace
    with pytest.raises(SystemExit):
        build_config()
    assert capsys.readouterr().out == f"{get_version()}\n"


@pytest.mark.parametrize("config", PKG_CFG.values())
@mock.patch("djtools.spotify.helpers.get_spotify_client", mock.Mock())
def test_filter_dict(config):
    """Test for the filter_dict function."""
    super_config = BaseConfig()
    sub_config = config(**dict(super_config))
    result = _filter_dict(sub_config)
    super_keys = set(super_config.model_dump())
    sub_keys = set(sub_config.model_dump())
    result_keys = set(result)
    assert len(result_keys) + len(super_keys) == len(sub_keys)
    assert result_keys.union(super_keys) == sub_keys
    assert sub_keys.difference(result_keys) == super_keys
    assert sub_keys.difference(super_keys) == result_keys


def test_stack_inspection_for_cli_arg_parsing():
    """Test stack inspection for cli arg parsing."""
    stack = inspect.stack()
    entry_frame = stack[-1]
    test_loc = str(Path("bin") / "pytest")
    windows_loc = str(Path("lib") / "runpy.py")
    windows_frozen = "<frozen runpy>"
    assert entry_frame[1].endswith((test_loc, windows_loc, windows_frozen))
