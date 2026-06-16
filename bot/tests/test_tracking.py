"""Tests for CTA click tracking — signed redirect links and the /go handler."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web

from config.settings import settings
from src.i18n import ru as ru_strings
from src.services.tracking import build_cta_url, sign_chat_id, verify_signature


class TestSignature:
    def test_sign_is_deterministic_and_short(self):
        sig = sign_chat_id(12345)
        assert sig == sign_chat_id(12345)
        assert len(sig) == 16

    def test_verify_roundtrip(self):
        assert verify_signature(12345, sign_chat_id(12345)) is True

    def test_verify_rejects_wrong_signature(self):
        assert verify_signature(12345, "deadbeefdeadbeef") is False

    def test_verify_rejects_signature_for_other_chat_id(self):
        # A signature minted for one chat_id must not validate for another.
        assert verify_signature(99999, sign_chat_id(12345)) is False

    def test_verify_rejects_empty(self):
        assert verify_signature(12345, "") is False


class TestBuildCtaUrl:
    def test_url_points_at_go_endpoint(self):
        url = build_cta_url(12345)
        assert url.startswith(settings.public_base_url.rstrip("/") + "/go?")
        assert "u=12345" in url
        assert f"sig={sign_chat_id(12345)}" in url


class TestRedirectHandler:
    async def test_valid_signature_logs_and_redirects(self):
        from src.handlers import tracking

        chat_id = 777
        request = SimpleNamespace(query={"u": str(chat_id), "sig": sign_chat_id(chat_id)})

        with patch.object(tracking, "save_user_event", new_callable=AsyncMock) as save:
            with pytest.raises(web.HTTPFound) as exc:
                await tracking.handle_cta_redirect(request)  # type: ignore[arg-type]

        save.assert_awaited_once()
        assert save.await_args.args[0] == chat_id
        assert save.await_args.args[1] == "cta_click"
        assert save.await_args.args[2] == "meal_plan_cta"
        assert exc.value.location == ru_strings.MEAL_PLAN_CTA_URL

    async def test_invalid_signature_redirects_without_logging(self):
        from src.handlers import tracking

        request = SimpleNamespace(query={"u": "777", "sig": "bad"})

        with patch.object(tracking, "save_user_event", new_callable=AsyncMock) as save:
            with pytest.raises(web.HTTPFound) as exc:
                await tracking.handle_cta_redirect(request)  # type: ignore[arg-type]

        save.assert_not_called()
        assert exc.value.location == ru_strings.MEAL_PLAN_CTA_URL

    async def test_bad_chat_id_redirects_without_logging(self):
        from src.handlers import tracking

        request = SimpleNamespace(query={"u": "notanumber", "sig": "whatever"})

        with patch.object(tracking, "save_user_event", new_callable=AsyncMock) as save:
            with pytest.raises(web.HTTPFound) as exc:
                await tracking.handle_cta_redirect(request)  # type: ignore[arg-type]

        save.assert_not_called()
        assert exc.value.location == ru_strings.MEAL_PLAN_CTA_URL
