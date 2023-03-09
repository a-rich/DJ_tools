import os

from bs4 import BeautifulSoup
import pytest
import yaml

from djtools.rekordbox.playlist_builder import (
    PlaylistBuilder, rekordbox_playlists    
)


pytest_plugins = [
    "test_data",
]


@pytest.mark.parametrize(
    "remainder_type", ["", "folder", "playlist", "invalid"]
)
def test_playlistbuilder(remainder_type, test_xml, test_playlist_config):
    playlist_builder = PlaylistBuilder(
        rekordbox_database=test_xml,
        playlist_config=test_playlist_config,
        pure_genre_playlists=["Techno"],
        playlist_remainder_type=remainder_type
    )()


def test_playlistbuilder_combiner_playlist_contains_new_playlist_selector_tracks(
    test_playlist_config, test_xml
):
    # Insert test track and Combiner playlist to target it.
    with open(test_playlist_config, mode="r", encoding="utf-8",) as _file:
        playlist_config = yaml.load(_file, Loader=yaml.FullLoader) or {}
    with open(test_xml, mode="r", encoding="utf-8") as _file:
        db = BeautifulSoup(_file.read(), "xml")
    new_track = db.new_tag("TRACK")
    new_track_ID = "-1"
    new_track.attrs = {
        "TrackID": new_track_ID,
        "AverageBpm": "140.00",
        "Genre": "Dubstep",
        "Rating": "255",
        "Location": "file://localhost/test-track.mp3",
        "Comments": "",
    }
    collection = db.find_all("COLLECTION")[0]
    collection.insert(0, new_track)
    selector_playlist = "{All Bass} & [140]"
    playlist_config["Combiner"]["playlists"] = [selector_playlist]
    playlist_config = {
        k: v for k, v in playlist_config.items()
        if k in ["GenreTagParser", "Combiner"]
    }
    with open(test_playlist_config, mode="w", encoding="utf-8",) as _file:
        playlist_config = yaml.dump(playlist_config, _file)
    with open(test_xml, mode="wb", encoding=db.orignal_encoding) as _file:
        _file.write(db.prettify("utf-8"))

    # Test pre-conditions.
    playlist = db.find_all("NODE", {"Name": "All Bass", "Type": "1"})[0]
    for track_key in playlist.find_all("TRACK"):
        assert (
            track_key["Key"] != new_track_ID,
            "Test track should not exist in All Bass!"
        )
    test_track = None
    for track in db.find_all("TRACK"):
        if not track.get("Location"):
            continue
        if track.get("TrackID") == new_track_ID:
            test_track = track
    assert test_track, "Test track should exist in XML!"

    # Run the PlaylistBuilder (GenreTagParser and Combiner).
    playlist_builder = PlaylistBuilder(
        rekordbox_database=test_xml,
        playlist_config=test_playlist_config,
    )()

    # Load XML generated by the PlaylistBuilder.
    path, file_name = os.path.split(test_xml)
    with open(os.path.join(path, f"auto_{file_name}"), mode="r", encoding="utf-8") as _file:
        db = BeautifulSoup(_file.read(), "xml")

    # Test that the test track was inserted into the "All Bass" playlist.
    test_track = None
    playlist = db.find_all("NODE", {"Name": "All Bass", "Type": "1"})[0]
    for track_key in playlist.find_all("TRACK"):
        if track_key["Key"] == new_track_ID:
            test_track = track_key
    assert test_track, "New track was not found in the genre playlist!"

    # Test that the test track was inserted into the Combiner playlist.
    test_track = None
    test_track = None
    playlist = db.find_all("NODE", {"Name": selector_playlist, "Type": "1"})[0]
    for track_key in playlist.find_all("TRACK"):
        if track_key["Key"] == new_track_ID:
            test_track = track_key
    assert test_track, "New track was not found in the Combiner playlist!"


def test_playlistbuilder_invalid_parser(
    tmpdir, test_xml, test_playlist_config
):
    with open(test_playlist_config, mode="r", encoding="utf-8",) as _file:
        playlist_config = yaml.load(_file, Loader=yaml.FullLoader) or {}
    parser_type = "nonexistent_parser"
    playlist_config[parser_type] = {}
    with open(test_playlist_config, mode="w", encoding="utf-8",) as _file:
        playlist_config = yaml.dump(playlist_config, _file)
    with pytest.raises(
        AttributeError,
        match=f"{parser_type} is not a valid TagParser!"
    ):
        PlaylistBuilder(
            rekordbox_database=test_xml,
            playlist_config=test_playlist_config,
        )()


def test_playlistbuilder_invalid_playlist(
    tmpdir, test_xml, test_playlist_config
):
    with open(test_playlist_config, mode="r", encoding="utf-8",) as _file:
        playlist_config = yaml.load(_file, Loader=yaml.FullLoader) or {}
    content = [0]
    playlist_config = {
        "GenreTagParser": {"name": "invalid", "playlists": content}
    }
    with open(test_playlist_config, mode="w", encoding="utf-8",) as _file:
        playlist_config = yaml.dump(playlist_config, _file)
    with pytest.raises(
        ValueError,
        match=f"Encountered invalid input type {type(content[0])}: {content[0]}"
    ):
        PlaylistBuilder(
            rekordbox_database=test_xml,
            playlist_config=test_playlist_config,
        )()


def test_rekordbox_playlists(test_config, test_xml):
    test_config.XML_PATH = test_xml
    rekordbox_playlists(test_config)
