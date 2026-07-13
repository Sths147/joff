from unittest.mock import patch

import pytest

from errors import PipelineError
from pipeline import fetch_latest_jo, get_profile, personalized_summary, save_profile


def _patched(**overrides):
    defaults = dict(
        load_credentials=("id", "secret"),
        init_urls=None,
        get_token="token",
        get_jo_container=({"joCont": {"datePubli": 1783468800000}}, "JORF n°0158"),
        extract_texts=[{"id": "JORFTEXT1", "titre": "x", "nature": "LOI"}],
    )
    defaults.update(overrides)
    return defaults


def test_fetch_latest_jo_skips_refetch_when_already_stored():
    p = _patched()
    with patch("pipeline.load_credentials", return_value=p["load_credentials"]), patch(
        "pipeline.init_urls"
    ), patch("pipeline.get_token", return_value=p["get_token"]), patch(
        "pipeline.get_jo_container", return_value=p["get_jo_container"]
    ), patch(
        "pipeline.storage.find_jo",
        return_value={"label": "JORF n°0158", "texts": p["extract_texts"]},
    ) as mock_find, patch(
        "pipeline.fetch_all_texts"
    ) as mock_fetch_all, patch(
        "pipeline.build_index"
    ) as mock_build, patch(
        "pipeline.storage.save_jo"
    ) as mock_save:
        result = fetch_latest_jo()

    mock_find.assert_called_once_with("2026-07-08")
    mock_fetch_all.assert_not_called()
    mock_build.assert_not_called()
    mock_save.assert_not_called()
    assert result == {"label": "JORF n°0158", "texts": p["extract_texts"]}


def test_fetch_latest_jo_fetches_and_stores_when_new():
    p = _patched()
    with patch("pipeline.load_credentials", return_value=p["load_credentials"]), patch(
        "pipeline.init_urls"
    ), patch("pipeline.get_token", return_value=p["get_token"]), patch(
        "pipeline.get_jo_container", return_value=p["get_jo_container"]
    ), patch(
        "pipeline.extract_texts", return_value=p["extract_texts"]
    ), patch(
        "pipeline.storage.find_jo", return_value=None
    ) as mock_find, patch(
        "pipeline.fetch_all_texts"
    ) as mock_fetch_all, patch(
        "pipeline.build_index"
    ) as mock_build, patch(
        "pipeline.storage.save_jo"
    ) as mock_save:
        result = fetch_latest_jo()

    mock_find.assert_called_once_with("2026-07-08")
    mock_fetch_all.assert_called_once()
    mock_build.assert_called_once()
    mock_save.assert_called_once_with("2026-07-08", "JORF n°0158", p["extract_texts"])
    assert result == {"label": "JORF n°0158", "texts": p["extract_texts"]}


def test_personalized_summary_uses_saved_bio():
    with patch("pipeline.storage.get_profile", return_value="Lawyer in Lyon"), patch(
        "pipeline.get_api_key", return_value="key"
    ), patch("pipeline.summarize_day", return_value="résumé") as mock_summarize:
        result = personalized_summary()
    mock_summarize.assert_called_once_with("key", "Lawyer in Lyon")
    assert result == "résumé"


def test_personalized_summary_requires_a_profile():
    with patch("pipeline.storage.get_profile", return_value=None):
        with pytest.raises(PipelineError):
            personalized_summary()


def test_get_profile_defaults_to_empty_string():
    with patch("pipeline.storage.get_profile", return_value=None):
        assert get_profile() == ""


def test_save_profile_delegates_to_storage():
    with patch("pipeline.storage.save_profile") as mock_save:
        result = save_profile("Lawyer in Lyon")
    mock_save.assert_called_once_with("Lawyer in Lyon")
    assert result == "Lawyer in Lyon"
