from subprocess import PIPE
from unittest import mock

import pytest

from djtools.configs.config import BaseConfig


def test_baseconfig_aws_profile():
    BaseConfig()


def test_baseconfig_aws_profile_not_set(caplog):
    caplog.set_level("WARNING")
    cfg = {"AWS_PROFILE": ""}
    BaseConfig(**cfg)
    assert caplog.records[0].message == (
        "Without AWS_PROFILE set to a valid profile ('default' or otherwise) "
        "you cannot use any of the following features: CHECK_TRACKS, "
        "DOWNLOAD_MUSIC, DOWNLOAD_SPOTIFY, DOWNLOAD_XML, UPLOAD_MUSIC, "
        "UPLOAD_XML"
    )


# TODO(a-rich): Figure out why this fails in the test runner.
# def test_baseconfig_aws_profile_invalid():
#     cfg = {"AWS_PROFILE": "definitely not a real AWS profile"}
#     with pytest.raises(
#         RuntimeError, match="AWS_PROFILE is not a valid profile!"
#     ):
#         BaseConfig(**cfg)

 
# TODO(a-rich): Figure out why this fails in the test runner.
# @mock.patch("djtools.configs.config.Popen", side_effect=Exception())
# def test_baseconfig_awscli_not_installed(mock_popen):
#     cfg = {"AWS_PROFILE": "definitely not a real AWS profile"}
#     with pytest.raises(
#         RuntimeError,
#         match=(
#             "Failed to run AWS command; make sure you've installed awscli "
#             "correctly."
#         )
#     ):
#         BaseConfig(**cfg)


def test_baseconfig_no_spotify_credentials(caplog):
    cfg = {"AWS_PROFILE": "default", "SPOTIFY_CLIENT_ID": ""}
    BaseConfig(**cfg)
    assert caplog.records[0].message == (
        "Without all the configuration options SPOTIFY_CLIENT_ID, "
        "SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI, set to valid "
        "values, you cannot use the following features: AUTO_PLAYLIST_UPDATE, "
        "DOWNLOAD_SPOTIFY, PLAYLIST_FROM_UPLOAD, "
        "CHECK_TRACKS_SPOTIFY_PLAYLISTS"
    )


def test_baseconfig_invalid_spotify_credentials():
    cfg = {
        "AWS_PROFILE": "default",
        "SPOTIFY_CLIENT_ID": "not a real ID",
        "SPOTIFY_CLIENT_SECRET": "not a real secret",
        "SPOTIFY_REDIRECT_URI": "not a real URI",
    }
    with pytest.raises(RuntimeError, match="Spotify credentials are invalid!"):
        BaseConfig(**cfg)


def test_baseconfig_no_xml_path(caplog):
    caplog.set_level("WARNING")
    cfg = {
        "AWS_PROFILE": "default",
        "SPOTIFY_CLIENT_ID": "",
        "XML_PATH": "",
    }
    BaseConfig(**cfg)
    assert caplog.records[1].message == (
        "XML_PATH is not set. Without this set to a valid Rekordbox XML "
        "export, you cannot use the following features: "
        "COPY_TRACKS_PLAYLISTS, DOWNLOAD_XML, RANDOMIZE_TRACKS_PLAYLISTS, "
        "REKORDBOX_PLAYLISTS, UPLOAD_XML"
    )


def test_baseconfig_xml_path_does_not_exist(caplog):
    caplog.set_level("WARNING")
    cfg = {
        "AWS_PROFILE": "default",
        "SPOTIFY_CLIENT_ID": "",
        "XML_PATH": "nonexistent XML",
    }
    BaseConfig(**cfg)
    assert caplog.records[1].message == (
        "XML_PATH does not exist. Without this set to a valid "
        "Rekordbox XML export, you cannot use the following features: "
        "COPY_TRACKS_PLAYLISTS, DOWNLOAD_XML, "
        "RANDOMIZE_TRACKS_PLAYLISTS, REKORDBOX_PLAYLISTS, UPLOAD_XML"
    )
