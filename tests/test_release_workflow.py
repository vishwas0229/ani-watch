from pathlib import Path


def test_release_workflow_has_quality_build_smoke_and_publish_gates() -> None:
    workflow = Path(__file__).parents[1] / ".github" / "workflows" / "release.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "quality:" in text
    assert "python -m pytest" in text
    assert "python -m ruff check ." in text
    assert "python -m ruff format --check ." in text
    assert "build:" in text
    assert "needs: quality" in text
    assert "python -m build --wheel --sdist" in text
    assert "python -m twine check dist/*" in text
    assert "smoke:" in text
    assert "actions/upload-artifact@v4" in text
    assert "actions/download-artifact@v4" in text
    assert "publish:" in text
    assert "needs: smoke" in text
    assert "contents: write" in text


def test_release_workflow_verifies_tag_and_package_versions() -> None:
    workflow = Path(__file__).parents[1] / ".github" / "workflows" / "release.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "github.ref_type == 'tag'" in text
    assert "GITHUB_REF_NAME#v" in text
    assert 'version("ani-watch")' in text
    assert "changelog_version" in text
