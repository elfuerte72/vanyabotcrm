import { describe, it, expect } from 'vitest';
import { eventButtonLabels, funnelStageLabels, funnelVariantLabels, getMaxFunnelStage } from '../../shared/constants.js';

describe('eventButtonLabels', () => {
  const knownEventData = [
    'buy_now', 'show_info', 'show_results', 'remind_later', 'check_suitability', 'none',
    'zone_belly', 'zone_thighs', 'zone_arms', 'zone_glutes',
    'nutrition_en', 'cardio_en', 'different', 'beginner', 'price', 'help',
    'coaching', 'gym', 'access', 'upgrade_79', 'upgrade_99',
    'lang_ru', 'lang_en', 'lang_ar',
    'confirm_data', 'fix_data',
    'confirm_paid_ru', 'video_workout', 'learn_workout', 'video_circle', 'upsell_decline',
  ];

  it.each(knownEventData)('has label for "%s"', (key) => {
    expect(eventButtonLabels[key]).toBeDefined();
    expect(eventButtonLabels[key].label).toBeTruthy();
    expect(eventButtonLabels[key].botResponse).toBeTruthy();
  });
});

describe('funnelStageLabels', () => {
  const knownFunnelData = [
    'wakeup_sent', 'stage_0_zone_ask',
    'stage_0', 'stage_1', 'stage_2', 'stage_3', 'stage_4',
    'stage_5', 'stage_6', 'stage_7', 'stage_8',
    'stage_9', 'stage_10', 'stage_11', 'stage_12',
  ];

  it.each(knownFunnelData)('has label for "%s"', (key) => {
    expect(funnelStageLabels[key]).toBeDefined();
    expect(funnelStageLabels[key].length).toBeGreaterThan(0);
  });
});

describe('funnelVariantLabels', () => {
  it.each(['belly', 'thighs', 'arms', 'glutes'])('has label for "%s"', (key) => {
    expect(funnelVariantLabels[key]).toBeDefined();
  });
});

describe('getMaxFunnelStage', () => {
  it('returns 12 for RU belly', () => {
    expect(getMaxFunnelStage('ru', 'belly')).toBe(12);
  });

  it('returns 11 for RU thighs/arms/glutes', () => {
    expect(getMaxFunnelStage('ru', 'thighs')).toBe(11);
    expect(getMaxFunnelStage('ru', 'arms')).toBe(11);
    expect(getMaxFunnelStage('ru', 'glutes')).toBe(11);
  });

  it('returns 12 for RU without variant', () => {
    expect(getMaxFunnelStage('ru', null)).toBe(12);
    expect(getMaxFunnelStage('ru', undefined)).toBe(12);
  });

  it('returns 10 for EN and AR', () => {
    expect(getMaxFunnelStage('en', null)).toBe(10);
    expect(getMaxFunnelStage('ar', null)).toBe(10);
  });

  it('defaults to RU when language is null/undefined', () => {
    expect(getMaxFunnelStage(null, 'belly')).toBe(12);
    expect(getMaxFunnelStage(undefined, null)).toBe(12);
  });
});
