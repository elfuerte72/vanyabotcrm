"""Tests for funnel message definitions."""

from src.funnel.messages import FunnelMessage, get_funnel_message


class TestGetFunnelMessageEN:
    """EN funnel: 9 stages (0-8) + 2 upsells (9-10)."""

    def test_all_en_stages_exist(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "en")
            assert msg is not None, f"Missing message for stage={stage}"
            assert msg.text, f"Empty text for stage={stage}"
            assert len(msg.buttons) > 0, f"No buttons for stage={stage}"

    def test_en_stage_out_of_range_returns_none(self):
        assert get_funnel_message(11, "en") is None
        assert get_funnel_message(-1, "en") is None

    def test_stages_0_to_8_have_buy_and_question(self):
        for stage in range(9):
            msg = get_funnel_message(stage, "en")
            assert len(msg.buttons) == 2, f"Stage {stage} should have 2 buttons"
            assert msg.buttons[0][1] == "buy_now", f"Stage {stage} first button should be buy_now"
            assert msg.buttons[1][1] == f"en_funnel_q_{stage}", f"Stage {stage} second button should be question"

    def test_stage_0_has_photo(self):
        msg = get_funnel_message(0, "en")
        assert msg.photo_name, "Stage 0 should have a photo"
        assert "en_funnel_stage_0" in msg.photo_name

    def test_stage_6_has_photo(self):
        msg = get_funnel_message(6, "en")
        assert msg.photo_name, "Stage 6 should have a photo"
        assert "en_funnel_stage_6" in msg.photo_name

    def test_stages_without_photos(self):
        for stage in [1, 2, 3, 4, 5, 7, 8]:
            msg = get_funnel_message(stage, "en")
            assert not msg.photo_name, f"Stage {stage} should not have a photo"

    def test_upsell_stages_have_buy_and_decline(self):
        for stage in (9, 10):
            msg = get_funnel_message(stage, "en")
            assert len(msg.buttons) == 2
            assert msg.buttons[0][1] == "buy_now"
            assert msg.buttons[1][1] == "upsell_decline"

    def test_stage_0_mentions_49_aed(self):
        msg = get_funnel_message(0, "en")
        assert "49 AED" in msg.text

    def test_upsell_1_mentions_79_aed(self):
        msg = get_funnel_message(9, "en")
        assert "79 AED" in msg.buttons[0][0]

    def test_upsell_2_mentions_129_aed(self):
        msg = get_funnel_message(10, "en")
        assert "129 AED" in msg.buttons[0][0]

    def test_buttons_are_tuples(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "en")
            for btn in msg.buttons:
                assert isinstance(btn, tuple), f"Button is not tuple at stage {stage}"
                assert len(btn) == 2, f"Button tuple wrong length at stage {stage}"


class TestGetFunnelMessageAR:
    """AR funnel: 9 stages (0-8) + 2 upsells (9-10)."""

    def test_all_ar_stages_exist(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "ar")
            assert msg is not None, f"Missing AR message for stage={stage}"
            assert msg.text, f"Empty text for AR stage={stage}"
            assert len(msg.buttons) > 0, f"No buttons for AR stage={stage}"

    def test_ar_stage_out_of_range(self):
        assert get_funnel_message(11, "ar") is None
        assert get_funnel_message(-1, "ar") is None

    def test_stages_0_to_8_have_buy_and_question(self):
        for stage in range(9):
            msg = get_funnel_message(stage, "ar")
            assert len(msg.buttons) == 2, f"AR stage {stage} should have 2 buttons"
            assert msg.buttons[0][1] == "buy_now", f"AR stage {stage} first button should be buy_now"
            assert msg.buttons[1][1] == f"ar_funnel_q_{stage}", f"AR stage {stage} second button should be question"

    def test_stage_0_has_photo(self):
        msg = get_funnel_message(0, "ar")
        assert msg.photo_name, "AR stage 0 should have a photo"

    def test_stage_6_has_photo(self):
        msg = get_funnel_message(6, "ar")
        assert msg.photo_name, "AR stage 6 should have a photo"

    def test_stages_without_photos(self):
        for stage in [1, 2, 3, 4, 5, 7, 8]:
            msg = get_funnel_message(stage, "ar")
            assert not msg.photo_name, f"AR stage {stage} should not have a photo"

    def test_upsell_stages_have_buy_and_decline(self):
        for stage in (9, 10):
            msg = get_funnel_message(stage, "ar")
            assert len(msg.buttons) == 2
            assert msg.buttons[0][1] == "buy_now"
            assert msg.buttons[1][1] == "upsell_decline"

    def test_stage_0_mentions_49_aed(self):
        msg = get_funnel_message(0, "ar")
        assert "49" in msg.text

    def test_upsell_1_mentions_79_aed(self):
        msg = get_funnel_message(9, "ar")
        assert "79" in msg.buttons[0][0]

    def test_upsell_2_mentions_129_aed(self):
        msg = get_funnel_message(10, "ar")
        assert "129" in msg.buttons[0][0]

    def test_buttons_are_tuples(self):
        for stage in range(11):
            msg = get_funnel_message(stage, "ar")
            for btn in msg.buttons:
                assert isinstance(btn, tuple), f"Button is not tuple at AR stage {stage}"
                assert len(btn) == 2, f"Button tuple wrong length at AR stage {stage}"

    def test_unknown_language_uses_ar_default(self):
        msg = get_funnel_message(0, "fr")
        assert msg is not None


class TestGetFunnelMessageRU:
    """RU funnel: 13 stages (0-12) with zone branching."""

    def test_stage_0_common_exists(self):
        msg = get_funnel_message(0, "ru")
        assert msg is not None
        assert msg.text

    def test_stage_0_has_zone_buttons(self):
        msg = get_funnel_message(0, "ru")
        callbacks = [b[1] for b in msg.buttons]
        assert "zone_belly" in callbacks
        assert "zone_thighs" in callbacks
        assert "zone_arms" in callbacks
        assert "zone_glutes" in callbacks

    def test_stage_0_zone_buttons_only(self):
        msg = get_funnel_message(0, "ru")
        assert not msg.has_url_button  # wakeup is sent separately
        assert len(msg.buttons) == 4

    def test_stages_1_to_12_require_variant(self):
        for stage in range(1, 13):
            msg = get_funnel_message(stage, "ru", variant=None)
            assert msg is None, f"Stage {stage} without variant should return None"

    def test_all_belly_stages_exist(self):
        for stage in range(13):
            msg = get_funnel_message(stage, "ru", variant="belly" if stage > 0 else None)
            assert msg is not None, f"Missing RU belly message for stage={stage}"
            assert msg.text, f"Empty text for stage={stage}"

    def test_ru_stage_out_of_range(self):
        assert get_funnel_message(13, "ru", variant="belly") is None
        assert get_funnel_message(-1, "ru") is None

    def test_stage_1_has_photo_and_buy(self):
        msg = get_funnel_message(1, "ru", variant="belly")
        assert msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_2_media_group(self):
        msg = get_funnel_message(2, "ru", variant="belly")
        assert msg.photo_name, "Stage 2 should have primary photo"
        assert len(msg.extra_photos) > 0, "Stage 2 should have extra photos (media group)"
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_3_video_note(self):
        msg = get_funnel_message(3, "ru", variant="belly")
        assert msg.video_note_id, "Stage 3 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_4_buy_button(self):
        msg = get_funnel_message(4, "ru", variant="belly")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_5_video_note(self):
        msg = get_funnel_message(5, "ru", variant="belly")
        assert msg.video_note_id, "Stage 5 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_6_hard_sell(self):
        msg = get_funnel_message(6, "ru", variant="belly")
        assert msg.buttons[0][1] == "buy_now"

    def test_stages_7_8_no_buttons(self):
        for stage in (7, 8):
            msg = get_funnel_message(stage, "ru", variant="belly")
            assert len(msg.buttons) == 0, f"Stage {stage} should have no buttons"

    def test_stage_9_media_group(self):
        msg = get_funnel_message(9, "ru", variant="belly")
        assert msg.photo_name
        assert len(msg.extra_photos) > 0
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_10_buy(self):
        msg = get_funnel_message(10, "ru", variant="belly")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_11_photo_and_buy(self):
        msg = get_funnel_message(11, "ru", variant="belly")
        assert msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_12_channel_url(self):
        msg = get_funnel_message(12, "ru", variant="belly")
        assert msg.has_url_button
        assert "ivanfit_health" in msg.url

    def test_ru_price_690(self):
        msg = get_funnel_message(1, "ru", variant="belly")
        assert "690" in msg.text


class TestGetFunnelMessageRUThighs:
    """RU thighs funnel: 11 stages (1-11) after zone selection."""

    def test_all_thighs_stages_exist(self):
        for stage in range(1, 12):
            msg = get_funnel_message(stage, "ru", variant="thighs")
            assert msg is not None, f"Missing RU thighs message for stage={stage}"
            assert msg.text, f"Empty text for stage={stage}"

    def test_thighs_out_of_range(self):
        assert get_funnel_message(12, "ru", variant="thighs") is None
        assert get_funnel_message(13, "ru", variant="thighs") is None

    def test_stage_1_has_photo_and_buy(self):
        msg = get_funnel_message(1, "ru", variant="thighs")
        assert msg.photo_name
        assert "ru_thighs_stage_1" in msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_2_media_group(self):
        msg = get_funnel_message(2, "ru", variant="thighs")
        assert msg.photo_name, "Stage 2 should have primary photo"
        assert "ru_thighs_stage_2a" in msg.photo_name
        assert len(msg.extra_photos) > 0, "Stage 2 should have extra photos (media group)"
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_3_video_note(self):
        msg = get_funnel_message(3, "ru", variant="thighs")
        assert msg.video_note_id, "Stage 3 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_4_buy_button(self):
        msg = get_funnel_message(4, "ru", variant="thighs")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_5_video_note(self):
        msg = get_funnel_message(5, "ru", variant="thighs")
        assert msg.video_note_id, "Stage 5 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_6_hard_sell(self):
        msg = get_funnel_message(6, "ru", variant="thighs")
        assert msg.buttons[0][1] == "buy_now"
        assert "690" in msg.text

    def test_stages_7_8_no_buttons(self):
        for stage in (7, 8):
            msg = get_funnel_message(stage, "ru", variant="thighs")
            assert len(msg.buttons) == 0, f"Stage {stage} should have no buttons"

    def test_stage_9_buy(self):
        msg = get_funnel_message(9, "ru", variant="thighs")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_10_photo_and_buy(self):
        msg = get_funnel_message(10, "ru", variant="thighs")
        assert msg.photo_name
        assert "ru_thighs_stage_10" in msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_11_channel_url(self):
        msg = get_funnel_message(11, "ru", variant="thighs")
        assert msg.has_url_button
        assert "ivanfit_health" in msg.url

    def test_thighs_price_690(self):
        msg = get_funnel_message(6, "ru", variant="thighs")
        assert "690" in msg.text

    def test_thighs_mentions_galife(self):
        """Thighs variant should mention галифе-зону."""
        msg = get_funnel_message(1, "ru", variant="thighs")
        assert "галифе" in msg.text.lower()

    def test_thighs_educational_fact(self):
        """Stage 8 should mention эстроген."""
        msg = get_funnel_message(8, "ru", variant="thighs")
        assert "эстроген" in msg.text.lower()


class TestGetFunnelMessageRUArms:
    """RU arms funnel: 11 stages (1-11) after zone selection."""

    def test_all_arms_stages_exist(self):
        for stage in range(1, 12):
            msg = get_funnel_message(stage, "ru", variant="arms")
            assert msg is not None, f"Missing RU arms message for stage={stage}"
            assert msg.text, f"Empty text for stage={stage}"

    def test_arms_out_of_range(self):
        assert get_funnel_message(12, "ru", variant="arms") is None
        assert get_funnel_message(13, "ru", variant="arms") is None

    def test_stage_1_has_photo_and_buy(self):
        msg = get_funnel_message(1, "ru", variant="arms")
        assert msg.photo_name
        assert "ru_arms_stage_1" in msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_2_media_group(self):
        msg = get_funnel_message(2, "ru", variant="arms")
        assert msg.photo_name, "Stage 2 should have primary photo"
        assert "ru_arms_stage_2a" in msg.photo_name
        assert len(msg.extra_photos) > 0, "Stage 2 should have extra photos (media group)"
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_3_video_note(self):
        msg = get_funnel_message(3, "ru", variant="arms")
        assert msg.video_note_id, "Stage 3 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_4_buy_button(self):
        msg = get_funnel_message(4, "ru", variant="arms")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_5_video_note(self):
        msg = get_funnel_message(5, "ru", variant="arms")
        assert msg.video_note_id, "Stage 5 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_6_hard_sell(self):
        msg = get_funnel_message(6, "ru", variant="arms")
        assert msg.buttons[0][1] == "buy_now"
        assert "690" in msg.text

    def test_stages_7_8_no_buttons(self):
        for stage in (7, 8):
            msg = get_funnel_message(stage, "ru", variant="arms")
            assert len(msg.buttons) == 0, f"Stage {stage} should have no buttons"

    def test_stage_9_buy(self):
        msg = get_funnel_message(9, "ru", variant="arms")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_10_photo_and_buy(self):
        msg = get_funnel_message(10, "ru", variant="arms")
        assert msg.photo_name
        assert "ru_arms_stage_10" in msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_11_channel_url(self):
        msg = get_funnel_message(11, "ru", variant="arms")
        assert msg.has_url_button
        assert "ivanfit_health" in msg.url

    def test_arms_price_690(self):
        msg = get_funnel_message(6, "ru", variant="arms")
        assert "690" in msg.text

    def test_arms_mentions_triceps(self):
        """Arms variant should mention трицепс."""
        msg = get_funnel_message(1, "ru", variant="arms")
        assert "трицепс" in msg.text.lower()

    def test_arms_educational_fact(self):
        """Stage 8 should mention лимфоток."""
        msg = get_funnel_message(8, "ru", variant="arms")
        assert "лимфоток" in msg.text.lower()


class TestGetFunnelMessageRUGlutes:
    """RU glutes funnel: 11 stages (1-11) after zone selection."""

    def test_all_glutes_stages_exist(self):
        for stage in range(1, 12):
            msg = get_funnel_message(stage, "ru", variant="glutes")
            assert msg is not None, f"Missing RU glutes message for stage={stage}"
            assert msg.text, f"Empty text for stage={stage}"

    def test_glutes_out_of_range(self):
        assert get_funnel_message(12, "ru", variant="glutes") is None
        assert get_funnel_message(13, "ru", variant="glutes") is None

    def test_stage_1_has_photo_and_buy(self):
        msg = get_funnel_message(1, "ru", variant="glutes")
        assert msg.photo_name
        assert "ru_glutes_stage_1" in msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_2_media_group(self):
        msg = get_funnel_message(2, "ru", variant="glutes")
        assert msg.photo_name, "Stage 2 should have primary photo"
        assert "ru_glutes_stage_2a" in msg.photo_name
        assert len(msg.extra_photos) > 0, "Stage 2 should have extra photos (media group)"
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_3_video_note(self):
        msg = get_funnel_message(3, "ru", variant="glutes")
        assert msg.video_note_id, "Stage 3 should have a video note"
        assert len(msg.buttons) == 0

    def test_stage_4_buy_button(self):
        msg = get_funnel_message(4, "ru", variant="glutes")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_5_hard_sell_no_video(self):
        """Glutes stage 5 is hard sell (NOT video note like arms/thighs)."""
        msg = get_funnel_message(5, "ru", variant="glutes")
        assert msg.buttons[0][1] == "buy_now"
        assert not msg.video_note_id, "Glutes stage 5 should NOT have video note"
        assert "690" in msg.text

    def test_stages_6_7_no_buttons(self):
        for stage in (6, 7):
            msg = get_funnel_message(stage, "ru", variant="glutes")
            assert len(msg.buttons) == 0, f"Stage {stage} should have no buttons"

    def test_stage_8_photo_and_buy(self):
        msg = get_funnel_message(8, "ru", variant="glutes")
        assert msg.photo_name
        assert "ru_glutes_stage_8" in msg.photo_name
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_9_buy(self):
        msg = get_funnel_message(9, "ru", variant="glutes")
        assert msg.buttons[0][1] == "buy_now"

    def test_stage_10_buy(self):
        msg = get_funnel_message(10, "ru", variant="glutes")
        assert msg.buttons[0][1] == "buy_now"
        assert "ягодиц" in msg.buttons[0][0].lower() or "ягодицы" in msg.buttons[0][0].lower()

    def test_stage_11_channel_url(self):
        msg = get_funnel_message(11, "ru", variant="glutes")
        assert msg.has_url_button
        assert "ivanfit_health" in msg.url

    def test_glutes_price_690(self):
        msg = get_funnel_message(5, "ru", variant="glutes")
        assert "690" in msg.text

    def test_glutes_mentions_form(self):
        """Glutes variant should mention форма/ягодиц."""
        msg = get_funnel_message(1, "ru", variant="glutes")
        text_lower = msg.text.lower()
        assert "ягодиц" in text_lower or "форма" in text_lower

    def test_glutes_educational_fact(self):
        """Stage 7 should mention пучки (muscle bundles)."""
        msg = get_funnel_message(7, "ru", variant="glutes")
        assert "пучк" in msg.text.lower()
