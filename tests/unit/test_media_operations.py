"""Unit tests for davinci_resolve_mcp.api.media_operations.

Resolve is mocked entirely.  Covers guard/validation logic for all
public functions plus representative happy-path and key failure branches.
Deep clip-linking and pseudo-subclip branches are covered by input-guard
tests only.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from davinci_resolve_mcp.api import media_operations as ops


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _resolve(project=None):
    pm = MagicMock()
    pm.GetCurrentProject.return_value = project
    r = MagicMock()
    r.GetProjectManager.return_value = pm
    return r


def _folder(name="Master", clips=None, subfolders=None):
    f = MagicMock()
    f.GetName.return_value = name
    f.GetClipList.return_value = clips if clips is not None else []
    f.GetSubFolderList.return_value = subfolders if subfolders is not None else []
    return f


def _clip(name="Clip", props=None):
    c = MagicMock()
    c.GetName.return_value = name
    c.GetClipProperty.return_value = props if props is not None else {"Type": "Video", "Duration": "100", "FPS": "24"}
    return c


def _build(*, root_clips=None, subfolders=None, timeline=None):
    """Return (resolve, media_pool, root_folder, project) fully wired."""
    root = _folder(name="Master", clips=root_clips or [], subfolders=subfolders or [])
    mp = MagicMock()
    mp.GetRootFolder.return_value = root
    project = MagicMock()
    project.GetMediaPool.return_value = mp
    project.GetCurrentTimeline.return_value = timeline
    resolve = _resolve(project=project)
    return resolve, mp, root, project


# ---------------------------------------------------------------------------
# list_media_pool_clips
# ---------------------------------------------------------------------------


def test_list_media_pool_clips_not_connected():
    assert ops.list_media_pool_clips(None) == [{"error": "Not connected to DaVinci Resolve"}]


def test_list_media_pool_clips_no_project_manager():
    r = MagicMock()
    r.GetProjectManager.return_value = None
    assert ops.list_media_pool_clips(r) == [{"error": "Failed to get Project Manager"}]


def test_list_media_pool_clips_no_project():
    assert ops.list_media_pool_clips(_resolve(project=None)) == [{"error": "No project currently open"}]


def test_list_media_pool_clips_no_media_pool():
    project = MagicMock()
    project.GetMediaPool.return_value = None
    assert ops.list_media_pool_clips(_resolve(project=project)) == [{"error": "Failed to get Media Pool"}]


def test_list_media_pool_clips_no_root_folder():
    mp = MagicMock()
    mp.GetRootFolder.return_value = None
    project = MagicMock()
    project.GetMediaPool.return_value = mp
    assert ops.list_media_pool_clips(_resolve(project=project)) == [{"error": "Failed to get Root Folder"}]


def test_list_media_pool_clips_empty_returns_info():
    resolve, _, _, _ = _build(root_clips=[])
    assert ops.list_media_pool_clips(resolve) == [{"info": "No clips found in the media pool"}]


def test_list_media_pool_clips_skips_item_without_get_clip_property():
    """Clips lacking a callable GetClipProperty must be skipped silently."""
    bad = MagicMock()
    bad.GetClipProperty = "not-callable"
    bad.GetName.return_value = "BadClip"
    resolve, _, _, _ = _build(root_clips=[bad])
    assert ops.list_media_pool_clips(resolve) == [{"info": "No clips found in the media pool"}]


def test_list_media_pool_clips_returns_clip_info():
    clip = _clip(name="Promo.mp4", props={"Type": "Video", "Duration": "50", "FPS": "30"})
    resolve, _, _, _ = _build(root_clips=[clip])
    result = ops.list_media_pool_clips(resolve)
    assert len(result) == 1
    assert result[0]["name"] == "Promo.mp4"
    assert result[0]["fps"] == "30"


# ---------------------------------------------------------------------------
# import_media
# ---------------------------------------------------------------------------


def test_import_media_not_connected():
    assert ops.import_media(None, "/some/file.mp4") == "Error: Not connected to DaVinci Resolve"


def test_import_media_empty_path():
    assert ops.import_media(_resolve(project=MagicMock()), "") == "Error: File path cannot be empty"


def test_import_media_file_not_found():
    result = ops.import_media(_resolve(project=MagicMock()), "/nonexistent/clip.mp4")
    assert result.startswith("Error: File")


def test_import_media_success(tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"")
    resolve, mp, _, _ = _build()
    mp.ImportMedia.return_value = [MagicMock()]
    assert ops.import_media(resolve, str(f)) == "Successfully imported 'clip.mp4'"
    mp.ImportMedia.assert_called_once_with([str(f)])


def test_import_media_failure(tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"")
    resolve, mp, _, _ = _build()
    mp.ImportMedia.return_value = []
    assert "Failed to import" in ops.import_media(resolve, str(f))


# ---------------------------------------------------------------------------
# create_bin
# ---------------------------------------------------------------------------


def test_create_bin_not_connected():
    assert ops.create_bin(None, "Roughs") == "Error: Not connected to DaVinci Resolve"


def test_create_bin_empty_name():
    assert ops.create_bin(_resolve(project=MagicMock()), "") == "Error: Bin name cannot be empty"


def test_create_bin_no_project():
    assert ops.create_bin(_resolve(project=None), "Roughs") == "Error: No project currently open"


def test_create_bin_duplicate_rejected():
    existing = _folder(name="Roughs")
    resolve, _, _, _ = _build(subfolders=[existing])
    assert ops.create_bin(resolve, "Roughs") == "Error: Bin 'Roughs' already exists"


def test_create_bin_success():
    resolve, mp, _, _ = _build(subfolders=[])
    mp.AddSubFolder.return_value = MagicMock()
    assert ops.create_bin(resolve, "Finals") == "Successfully created bin 'Finals'"


def test_create_bin_failure():
    resolve, mp, _, _ = _build(subfolders=[])
    mp.AddSubFolder.return_value = None
    assert ops.create_bin(resolve, "Finals") == "Failed to create bin 'Finals'"


# ---------------------------------------------------------------------------
# list_bins
# ---------------------------------------------------------------------------


def test_list_bins_not_connected():
    assert ops.list_bins(None) == [{"error": "Not connected to DaVinci Resolve"}]


def test_list_bins_no_project():
    assert ops.list_bins(_resolve(project=None)) == [{"error": "No project currently open"}]


def test_list_bins_returns_root_and_subfolders():
    sub = _folder(name="Roughs", clips=[_clip()])
    resolve, _, _, _ = _build(root_clips=[_clip()], subfolders=[sub])
    result = ops.list_bins(resolve)
    names = [r["name"] for r in result]
    assert "Roughs" in names
    assert any(r.get("is_root") for r in result)


def test_list_bins_only_root_no_subfolders_returns_info():
    """When there are no sub-bins the result is the 'no bins found' sentinel."""
    resolve, _, _, _ = _build(root_clips=[], subfolders=[])
    assert ops.list_bins(resolve) == [{"info": "No bins found in the media pool"}]


# ---------------------------------------------------------------------------
# get_bin_contents
# ---------------------------------------------------------------------------


def test_get_bin_contents_not_connected():
    assert ops.get_bin_contents(None, "Roughs") == [{"error": "Not connected to DaVinci Resolve"}]


def test_get_bin_contents_master_returns_root_clips():
    clip = _clip(name="Raw.mp4")
    resolve, _, _, _ = _build(root_clips=[clip])
    result = ops.get_bin_contents(resolve, "master")
    assert result[0]["name"] == "Raw.mp4"
    assert result[0]["bin"] == "Master"


def test_get_bin_contents_finds_named_bin():
    clip = _clip(name="Cut.mp4")
    sub = _folder(name="Finals", clips=[clip])
    resolve, _, _, _ = _build(subfolders=[sub])
    result = ops.get_bin_contents(resolve, "Finals")
    assert result[0]["name"] == "Cut.mp4"
    assert result[0]["bin"] == "Finals"


def test_get_bin_contents_bin_not_found():
    resolve, _, _, _ = _build(subfolders=[])
    assert ops.get_bin_contents(resolve, "Missing") == [{"error": "Bin 'Missing' not found in Media Pool"}]


# ---------------------------------------------------------------------------
# format_clip_list  (pure helper — no Resolve interaction)
# ---------------------------------------------------------------------------


def test_format_clip_list_empty_list():
    assert ops.format_clip_list([], "Master") == [{"info": "No clips found in bin 'Master'"}]


def test_format_clip_list_none():
    assert ops.format_clip_list(None, "Roughs") == [{"info": "No clips found in bin 'Roughs'"}]


def test_format_clip_list_returns_clip_fields():
    clip = _clip(
        name="Shot.mp4",
        props={"Type": "Video", "Duration": "30", "FPS": "24", "Width": 1920, "Height": 1080},
    )
    result = ops.format_clip_list([clip], "Master")
    assert len(result) == 1
    assert result[0]["name"] == "Shot.mp4"
    assert result[0]["resolution"] == "1920x1080"
    assert result[0]["bin"] == "Master"


# ---------------------------------------------------------------------------
# list_timeline_clips
# ---------------------------------------------------------------------------


def test_list_timeline_clips_not_connected():
    assert ops.list_timeline_clips(None) == [{"error": "Not connected to DaVinci Resolve"}]


def test_list_timeline_clips_no_project():
    assert ops.list_timeline_clips(_resolve(project=None)) == [{"error": "No project currently open"}]


def test_list_timeline_clips_no_timeline():
    resolve, _, _, _ = _build(timeline=None)
    assert ops.list_timeline_clips(resolve) == [{"error": "No timeline currently active"}]


def test_list_timeline_clips_returns_video_and_audio():
    vcl = MagicMock()
    vcl.GetName.return_value = "V1Clip"
    vcl.GetStart.return_value = 0
    vcl.GetEnd.return_value = 100
    vcl.GetDuration.return_value = 100

    acl = MagicMock()
    acl.GetName.return_value = "A1Clip"
    acl.GetStart.return_value = 0
    acl.GetEnd.return_value = 100
    acl.GetDuration.return_value = 100

    timeline = MagicMock()
    timeline.GetTrackCount.side_effect = lambda t: 1 if t in ("video", "audio") else 0
    timeline.GetItemListInTrack.side_effect = lambda t, _i: [vcl] if t == "video" else [acl]

    resolve, _, _, _ = _build(timeline=timeline)
    result = ops.list_timeline_clips(resolve)
    names = {r["name"] for r in result}
    tracks = {r["track"] for r in result}
    assert names == {"V1Clip", "A1Clip"}
    assert "V1" in tracks and "A1" in tracks


# ---------------------------------------------------------------------------
# add_clip_to_timeline
# ---------------------------------------------------------------------------


def test_add_clip_to_timeline_not_connected():
    assert ops.add_clip_to_timeline(None, "Clip.mp4") == ("Error: Not connected to DaVinci Resolve")


def test_add_clip_to_timeline_no_project():
    assert ops.add_clip_to_timeline(_resolve(project=None), "Clip.mp4") == ("Error: No project currently open")


def test_add_clip_to_timeline_clip_not_found():
    resolve, _, _, _ = _build(root_clips=[])
    assert ops.add_clip_to_timeline(resolve, "Missing.mp4") == ("Error: Clip 'Missing.mp4' not found in Media Pool")


def test_add_clip_to_timeline_no_current_timeline():
    clip = _clip(name="Promo.mp4")
    resolve, _, _, _ = _build(root_clips=[clip], timeline=None)
    assert ops.add_clip_to_timeline(resolve, "Promo.mp4") == "Error: No timeline currently active"


def test_add_clip_to_timeline_named_timeline_not_found():
    clip = _clip(name="Promo.mp4")
    resolve, _, _, project = _build(root_clips=[clip])
    project.GetTimelineCount.return_value = 0
    assert ops.add_clip_to_timeline(resolve, "Promo.mp4", timeline_name="Ghost") == (
        "Error: Timeline 'Ghost' not found"
    )


def test_add_clip_to_timeline_success():
    clip = _clip(name="Promo.mp4")
    timeline = MagicMock()
    resolve, mp, _, _ = _build(root_clips=[clip], timeline=timeline)
    mp.AppendToTimeline.return_value = [MagicMock()]
    assert ops.add_clip_to_timeline(resolve, "Promo.mp4") == ("Successfully added clip 'Promo.mp4' to timeline")
    mp.AppendToTimeline.assert_called_once()


def test_add_clip_to_timeline_failure():
    clip = _clip(name="Promo.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip], timeline=MagicMock())
    mp.AppendToTimeline.return_value = []
    assert ops.add_clip_to_timeline(resolve, "Promo.mp4") == ("Failed to add clip 'Promo.mp4' to timeline")


# ---------------------------------------------------------------------------
# delete_media
# ---------------------------------------------------------------------------


def test_delete_media_not_connected():
    assert ops.delete_media(None, "Clip.mp4") == "Error: Not connected to DaVinci Resolve"


def test_delete_media_no_project():
    assert ops.delete_media(_resolve(project=None), "Clip.mp4") == ("Error: No project currently open")


def test_delete_media_clip_not_found():
    resolve, _, _, _ = _build(root_clips=[])
    assert ops.delete_media(resolve, "Missing.mp4") == ("Error: Clip 'Missing.mp4' not found in Media Pool")


def test_delete_media_success():
    clip = _clip(name="Old.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip])
    mp.DeleteClips.return_value = True
    assert ops.delete_media(resolve, "Old.mp4") == ("Successfully deleted clip 'Old.mp4' from Media Pool")


def test_delete_media_failure():
    clip = _clip(name="Old.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip])
    mp.DeleteClips.return_value = False
    assert ops.delete_media(resolve, "Old.mp4") == ("Failed to delete clip 'Old.mp4' from Media Pool")


# ---------------------------------------------------------------------------
# move_media_to_bin
# ---------------------------------------------------------------------------


def test_move_media_to_bin_not_connected():
    assert ops.move_media_to_bin(None, "Clip.mp4", "Finals") == ("Error: Not connected to DaVinci Resolve")


def test_move_media_to_bin_bin_not_found():
    clip = _clip(name="Clip.mp4")
    resolve, _, _, _ = _build(root_clips=[clip], subfolders=[])
    assert ops.move_media_to_bin(resolve, "Clip.mp4", "NoSuchBin") == ("Error: Bin 'NoSuchBin' not found in Media Pool")


def test_move_media_to_bin_clip_not_found():
    sub = _folder(name="Finals")
    resolve, _, _, _ = _build(root_clips=[], subfolders=[sub])
    assert ops.move_media_to_bin(resolve, "Missing.mp4", "Finals") == (
        "Error: Clip 'Missing.mp4' not found in Media Pool"
    )


def test_move_media_to_bin_success():
    clip = _clip(name="Clip.mp4")
    sub = _folder(name="Finals")
    resolve, mp, _, _ = _build(root_clips=[clip], subfolders=[sub])
    mp.MoveClips.return_value = True
    assert ops.move_media_to_bin(resolve, "Clip.mp4", "Finals") == (
        "Successfully moved clip 'Clip.mp4' to bin 'Finals'"
    )


def test_move_media_to_bin_to_master():
    """Moving to 'master' resolves to the root folder."""
    clip = _clip(name="Clip.mp4")
    sub = _folder(name="Roughs", clips=[clip])
    resolve, mp, _, _ = _build(root_clips=[], subfolders=[sub])
    mp.MoveClips.return_value = True
    result = ops.move_media_to_bin(resolve, "Clip.mp4", "master")
    assert "Successfully moved" in result


# ---------------------------------------------------------------------------
# auto_sync_audio
# ---------------------------------------------------------------------------


def test_auto_sync_audio_not_connected():
    assert ops.auto_sync_audio(None, ["a", "b"]).startswith("Error: Not connected")


def test_auto_sync_audio_too_few_clips():
    assert ops.auto_sync_audio(_resolve(project=MagicMock()), ["only_one"]) == (
        "Error: At least two clips are required for audio synchronization"
    )


def test_auto_sync_audio_invalid_method():
    assert ops.auto_sync_audio(_resolve(project=MagicMock()), ["a", "b"], sync_method="magic") == (
        "Error: Sync method must be 'waveform' or 'timecode'"
    )


def test_auto_sync_audio_clip_not_found():
    resolve, _, _, _ = _build(root_clips=[_clip(name="a")])
    assert "not found" in ops.auto_sync_audio(resolve, ["a", "missing"])


def test_auto_sync_audio_success():
    resolve, mp, _, _ = _build(root_clips=[_clip(name="a"), _clip(name="b")])
    mp.SetCurrentFolder.return_value = True
    mp.SelectClips.return_value = True
    mp.AutoSyncAudio.return_value = True
    result = ops.auto_sync_audio(resolve, ["a", "b"])
    assert "Successfully synced audio" in result
    assert "2 clips" in result


# ---------------------------------------------------------------------------
# unlink_clips
# ---------------------------------------------------------------------------


def test_unlink_clips_not_connected():
    assert ops.unlink_clips(None, ["a"]).startswith("Error: Not connected")


def test_unlink_clips_empty_list():
    assert ops.unlink_clips(_resolve(project=MagicMock()), []) == ("Error: No clip names provided for unlinking")


def test_unlink_clips_clip_not_found():
    resolve, _, _, _ = _build(root_clips=[])
    assert "not found" in ops.unlink_clips(resolve, ["missing"])


def test_unlink_clips_success():
    clip = _clip(name="Raw.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip])
    mp.UnlinkClips.return_value = True
    assert ops.unlink_clips(resolve, ["Raw.mp4"]) == "Successfully unlinked 1 clips"


def test_unlink_clips_failure():
    clip = _clip(name="Raw.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip])
    mp.UnlinkClips.return_value = False
    assert ops.unlink_clips(resolve, ["Raw.mp4"]) == "Error: Failed to unlink clips"


# ---------------------------------------------------------------------------
# relink_clips  (input validation)
# ---------------------------------------------------------------------------


def test_relink_clips_not_connected():
    assert ops.relink_clips(None, ["a"], folder_path="/tmp").startswith("Error: Not connected")


def test_relink_clips_empty_clip_names():
    assert ops.relink_clips(_resolve(project=MagicMock()), [], folder_path="/tmp") == (
        "Error: No clip names provided for relinking"
    )


def test_relink_clips_no_path_or_folder():
    result = ops.relink_clips(_resolve(project=MagicMock()), ["a"])
    assert "Either media_paths or folder_path" in result


def test_relink_clips_both_paths_and_folder():
    result = ops.relink_clips(_resolve(project=MagicMock()), ["a"], media_paths=["/x"], folder_path="/dir")
    assert "Cannot specify both" in result


def test_relink_clips_mismatched_media_paths():
    result = ops.relink_clips(_resolve(project=MagicMock()), ["a", "b"], media_paths=["/x"])
    assert "number must match" in result


# ---------------------------------------------------------------------------
# create_sub_clip
# ---------------------------------------------------------------------------


def test_create_sub_clip_not_connected():
    assert ops.create_sub_clip(None, "Clip", 0, 10) == "Error: Not connected to DaVinci Resolve"


def test_create_sub_clip_empty_name():
    assert ops.create_sub_clip(_resolve(project=MagicMock()), "", 0, 10) == ("Error: Clip name cannot be empty")


def test_create_sub_clip_start_not_less_than_end():
    assert ops.create_sub_clip(_resolve(project=MagicMock()), "Clip", 50, 10) == (
        "Error: Start frame must be less than end frame"
    )


def test_create_sub_clip_negative_start():
    assert ops.create_sub_clip(_resolve(project=MagicMock()), "Clip", -1, 10) == (
        "Error: Start frame cannot be negative"
    )


def test_create_sub_clip_clip_not_found():
    resolve, _, _, _ = _build(root_clips=[])
    assert ops.create_sub_clip(resolve, "Missing", 0, 10) == ("Error: Source clip 'Missing' not found in Media Pool")


def test_create_sub_clip_no_api_returns_helpful_error():
    """When neither MediaPool nor clip has CreateSubClip a clear error is returned."""
    clip = _clip(name="Source.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip])
    mp.CreateSubClip = "not-callable"
    clip.CreateSubClip = "not-callable"
    result = ops.create_sub_clip(resolve, "Source.mp4", 0, 100)
    assert "not supported" in result.lower() or "CreateSubClip" in result


def test_create_sub_clip_success():
    sub = MagicMock()
    clip = _clip(name="Source.mp4")
    resolve, mp, _, _ = _build(root_clips=[clip])
    mp.CreateSubClip.return_value = sub
    result = ops.create_sub_clip(resolve, "Source.mp4", 0, 100)
    assert "Successfully created subclip" in result
    clip.ClearMarkInOut.assert_called()


# ---------------------------------------------------------------------------
# create_pseudo_subclip  (guards)
# ---------------------------------------------------------------------------


def test_create_pseudo_subclip_not_connected():
    assert ops.create_pseudo_subclip(None, "Clip", 0, 10) == ("Error: Not connected to DaVinci Resolve")


def test_create_pseudo_subclip_empty_name():
    assert ops.create_pseudo_subclip(_resolve(project=MagicMock()), "", 0, 10) == ("Error: Clip name cannot be empty")


def test_create_pseudo_subclip_invalid_frames():
    assert ops.create_pseudo_subclip(_resolve(project=MagicMock()), "Clip", 20, 5) == (
        "Error: Start frame must be less than end frame"
    )


def test_create_pseudo_subclip_clip_not_found():
    resolve, _, _, _ = _build(root_clips=[])
    assert "not found" in ops.create_pseudo_subclip(resolve, "Missing", 0, 10)


# ---------------------------------------------------------------------------
# create_pseudo_subclip_compound  (guards)
# ---------------------------------------------------------------------------


def test_create_pseudo_subclip_compound_not_connected():
    assert ops.create_pseudo_subclip_compound(None, "TL_Name", bin_name="Roughs").startswith("Error: Not connected")


def test_create_pseudo_subclip_compound_empty_timeline_name():
    assert (
        ops.create_pseudo_subclip_compound(_resolve(project=MagicMock()), "", bin_name="Roughs")
        == "Error: Timeline name cannot be empty"
    )


def test_create_pseudo_subclip_compound_no_bin():
    assert (
        ops.create_pseudo_subclip_compound(_resolve(project=MagicMock()), "SomeTL")
        == "Error: Bin name is required for pseudo-subclip compound creation"
    )


# ---------------------------------------------------------------------------
# normalize_latest_compound_clip
# ---------------------------------------------------------------------------


def test_normalize_latest_compound_clip_not_connected():
    assert ops.normalize_latest_compound_clip(None, "Roughs", "NewName").startswith("Error: Not connected")


def test_normalize_latest_compound_clip_empty_source_bin():
    assert (
        ops.normalize_latest_compound_clip(_resolve(project=MagicMock()), "", "NewName")
        == "Error: Source bin name cannot be empty"
    )


def test_normalize_latest_compound_clip_empty_new_name():
    assert (
        ops.normalize_latest_compound_clip(_resolve(project=MagicMock()), "Roughs", "")
        == "Error: New name for compound clip cannot be empty"
    )


def test_normalize_latest_compound_clip_no_compound_clips():
    regular = _clip(name="NotACompound.mp4", props={"Type": "Video"})
    sub = _folder(name="Roughs", clips=[regular])
    resolve, _, _, _ = _build(subfolders=[sub])
    result = ops.normalize_latest_compound_clip(resolve, "Roughs", "NewName")
    assert "no compound clips" in result


def test_normalize_latest_compound_clip_success():
    compound = MagicMock()
    compound.GetClipProperty.return_value = {"Type": "Compound"}
    compound.GetName.return_value = "OldCompound"
    sub = _folder(name="Roughs", clips=[compound])
    resolve, _, _, _ = _build(subfolders=[sub])
    result = ops.normalize_latest_compound_clip(resolve, "Roughs", "NewName")
    compound.SetName.assert_called_once_with("NewName")
    assert "Successfully renamed" in result
