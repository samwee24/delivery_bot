"""Foxglove layouts: an Indicator path must name a message field, not just a topic.

A bare topic path ('/robot/status/video') gives the Indicator the whole message, so no rule
ever matches and every tile shows its fallback, e.g. 'POWER OK' while the Pi is under-voltage.
"""
import glob
import json
import os
import re

LAYOUTS = glob.glob(os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'foxglove', '*.json'))
FIELD_PATH = re.compile(r'^/[\w/]+\.\w+')


def indicator_paths(layout: dict) -> dict:
    return {k: v.get('path', '') for k, v in layout.get('configById', {}).items()
            if k.startswith('Indicator!')}


def test_layouts_found():
    assert LAYOUTS


def test_indicator_paths_name_a_field():
    bad = {}
    for f in LAYOUTS:
        with open(f) as fh:
            for panel, path in indicator_paths(json.load(fh)).items():
                if not FIELD_PATH.match(path):
                    bad[f'{os.path.basename(f)}:{panel}'] = path
    assert not bad, f'Indicator paths without a field: {bad}'


def test_field_path_pattern():
    assert FIELD_PATH.match('/robot/status/video.data')
    assert not FIELD_PATH.match('/robot/status/video')
