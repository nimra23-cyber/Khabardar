import { afterEach, beforeEach, describe, expect, it } from "vitest";

import i18n from "./index";
import en from "./en.json";
import ur from "./ur.json";
import urLatn from "./ur-Latn.json";

/** Recursively collect dotted key paths from a nested translation object. */
function collectKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  const keys: string[] = [];
  for (const [k, v] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === "object" && !Array.isArray(v)) {
      keys.push(...collectKeys(v as Record<string, unknown>, path));
    } else {
      keys.push(path);
    }
  }
  return keys.sort();
}

describe("i18n runtime missing-key fallback (category 1)", () => {
  beforeEach(async () => {
    await i18n.changeLanguage("en");
  });
  afterEach(async () => {
    await i18n.changeLanguage("en");
  });

  it("falls back to the English string when a key is missing in the active language", async () => {
    // Inject a key that exists ONLY in English, then switch to Urdu and ask
    // for it: i18next must return the English value via fallbackLng.
    i18n.addResource("en", "translation", "_runtimeOnly.probe", "ENGLISH_ONLY_VALUE");

    await i18n.changeLanguage("ur");
    // The key is absent in `ur`, so fallback to English must occur.
    expect(i18n.t("_runtimeOnly.probe")).toBe("ENGLISH_ONLY_VALUE");

    await i18n.changeLanguage("ur-Latn");
    expect(i18n.t("_runtimeOnly.probe")).toBe("ENGLISH_ONLY_VALUE");
  });

  it("returns the real translation when the key exists in the active language", async () => {
    await i18n.changeLanguage("ur");
    // 'language.label' exists in ur -> should NOT fall back to English.
    expect(i18n.t("language.label")).toBe("زبان");
    expect(i18n.t("language.label")).not.toBe("Language");
  });
});

describe("translation-key completeness (category 2)", () => {
  const enKeys = collectKeys(en as Record<string, unknown>);

  it("ur bundle has exactly the same key set as en", () => {
    const urKeys = collectKeys(ur as Record<string, unknown>);
    expect(urKeys).toEqual(enKeys);
  });

  it("ur-Latn bundle has exactly the same key set as en", () => {
    const urLatnKeys = collectKeys(urLatn as Record<string, unknown>);
    expect(urLatnKeys).toEqual(enKeys);
  });

  it("no translation bundle has empty string values", () => {
    for (const [label, bundle] of [
      ["en", en],
      ["ur", ur],
      ["ur-Latn", urLatn],
    ] as const) {
      const flat = JSON.stringify(bundle);
      expect(flat.includes('""'), `${label} must not contain empty values`).toBe(false);
    }
  });
});
