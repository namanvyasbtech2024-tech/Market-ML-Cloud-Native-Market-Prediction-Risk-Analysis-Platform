"""
Unit Test Suite for S3 Deployment Asset Readiness & Static Link Resolution
Validates presence and non-emptiness of all assets required for S3 static website hosting.
"""

import os

def test_s3_assets_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "app", "templates", "index.html")
    css_path = os.path.join(base_dir, "app", "static", "style_v3.css")
    js_path = os.path.join(base_dir, "app", "static", "script_v52.js")

    assert os.path.exists(template_path), "index.html must exist"
    assert os.path.exists(css_path), "style_v3.css must exist"
    assert os.path.exists(js_path), "script_v52.js must exist"

    assert os.path.getsize(template_path) > 1000, "index.html must not be empty"
    assert os.path.getsize(css_path) > 100, "style_v3.css must not be empty"
    assert os.path.getsize(js_path) > 1000, "script_v52.js must not be empty"


def test_script_s3_bridge():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    js_path = os.path.join(base_dir, "app", "static", "script_v52.js")

    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "s3-website" in content, "script_v52.js must include S3 static hosting bridge"
    assert "13.217.227.166" in content, "script_v52.js must target EC2 live backend"
