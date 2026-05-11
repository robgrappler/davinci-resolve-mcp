# tests/unit/test_helper_failures.py - Regression tests for Resolve helper failures.

from __future__ import annotations

import importlib
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class FakeItem:
    GetType = None
    GetMediaType = None

    def __init__(self, item_id: str, name: str, start: int = 0, end: int = 10):
        self.item_id = item_id
        self.name = name
        self.start = start
        self.end = end
        self.properties = {}

    def GetUniqueId(self):
        return self.item_id

    def GetName(self):
        return self.name

    def GetStart(self):
        return self.start

    def GetEnd(self):
        return self.end

    def SetProperty(self, property_name, property_value):
        self.properties[property_name] = property_value
        return True


class FakeTimeline:
    def __init__(self, video_items=None, audio_items=None):
        self.video_items = video_items or []
        self.audio_items = audio_items or []

    def GetTrackCount(self, track_type):
        return 1

    def GetItemListInTrack(self, track_type, track_index):
        return self.video_items if track_type == "video" else self.audio_items


class FakeProject:
    def __init__(self, timeline):
        self.timeline = timeline

    def GetCurrentTimeline(self):
        return self.timeline


class FakeProjectManager:
    def __init__(self, project):
        self.project = project

    def GetCurrentProject(self):
        return self.project


class FakeResolve:
    def __init__(self, timeline):
        self.project_manager = FakeProjectManager(FakeProject(timeline))

    def GetProjectManager(self):
        return self.project_manager


def load_server_with_timeline(monkeypatch, timeline):
    module = importlib.import_module("resolve_mcp_server")
    monkeypatch.setattr(module, "resolve", FakeResolve(timeline))
    return module


def test_enable_keyframes_does_not_call_missing_get_type(monkeypatch):
    item = FakeItem("item-1", "clip.mov")
    module = load_server_with_timeline(monkeypatch, FakeTimeline(video_items=[item]))

    result = module.enable_keyframes("item-1", "Sizing")

    assert "Successfully enabled Sizing" in result
    assert item.properties["KeyframeMode"] == 2


def test_stabilization_does_not_call_missing_get_type(monkeypatch):
    item = FakeItem("item-1", "clip.mov")
    module = load_server_with_timeline(monkeypatch, FakeTimeline(video_items=[item]))

    result = module.set_timeline_item_stabilization("item-1", enabled=True, method="Similarity", strength=0.35)

    assert "Successfully set" in result
    assert item.properties["StabilizationEnable"] == 1
    assert item.properties["StabilizationMethod"] == "Similarity"
    assert item.properties["StabilizationStrength"] == 0.35


def test_audio_does_not_call_missing_get_media_type(monkeypatch):
    item = FakeItem("audio-1", "clip.wav")
    module = load_server_with_timeline(monkeypatch, FakeTimeline(audio_items=[item]))

    result = module.set_timeline_item_audio("audio-1", volume=1.0, pan=0.0, eq_enabled=False)

    assert "Successfully set" in result
    assert item.properties["Volume"] == 1.0
    assert item.properties["Pan"] == 0.0
    assert item.properties["EQEnable"] == 0


def test_add_keyframe_reports_missing_api_method(monkeypatch):
    item = FakeItem("item-1", "clip.mov")
    module = load_server_with_timeline(monkeypatch, FakeTimeline(video_items=[item]))

    result = module.add_keyframe("item-1", "ZoomX", 1, 1.2)

    assert "does not expose AddKeyframe" in result
    assert "does not support that helper" in result



class FakeSettingsProject:
    def __init__(self):
        self.values = {"separateColorSpaceAndGamma": "0"}
        self.calls = []

    def GetSetting(self, property_name):
        return self.values.get(property_name, "")

    def SetSetting(self, property_name, property_value):
        self.calls.append((property_name, property_value))
        return property_name == "colorSpaceTimeline"


def test_set_color_space_uses_resolve_timeline_color_key():
    from src.utils.project_properties import set_color_space

    project = FakeSettingsProject()

    assert set_color_space(project, "Rec.709", "Gamma 2.4") is True
    assert project.calls[0] == ("colorSpaceTimeline", "Rec.709 Gamma 2.4")
