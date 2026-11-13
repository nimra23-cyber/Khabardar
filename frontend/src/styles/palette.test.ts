import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { CSS_TOKEN_EXPECTED, PALETTE } from "./palette";

const __dirname = dirname(fileURLToPath(import.meta.url));

describe("palette tokens (exact values)", () => {
  it("TS palette holds the exact approved brand values", () => {
    expect(PALETTE).toEqual({
      deepNavy: "#101D31",
      midnightBlue: "#172A45",
      metallicSilver: "#C5D0DC",
      electricBlue: "#3987FF",
      surfaceLight: "#F4F7FB",
      surfaceDark: "#0B1423",
      danger: "#E5484D",
      warning: "#E5A323",
      safe: "#1C9B70",
    });
  });

  it("tokens.css declares each --color-* variable with the exact value", () => {
    const cssPath = resolve(__dirname, "tokens.css");
    const css = readFileSync(cssPath, "utf8");

    for (const [varName, expectedHex] of Object.entries(CSS_TOKEN_EXPECTED)) {
      // Match e.g. `--color-deep-navy: #101d31;` (case-insensitive on hex).
      const re = new RegExp(`${varName}\\s*:\\s*(#[0-9a-fA-F]{6})\\s*;`);
      const match = css.match(re);
      expect(match, `token ${varName} must be declared in tokens.css`).not.toBeNull();
      expect(match![1].toUpperCase()).toBe(expectedHex.toUpperCase());
    }
  });

  it("risk severity tokens map to Danger/Warning/Safe exactly", () => {
    expect(CSS_TOKEN_EXPECTED["--color-danger"]).toBe("#E5484D");
    expect(CSS_TOKEN_EXPECTED["--color-warning"]).toBe("#E5A323");
    expect(CSS_TOKEN_EXPECTED["--color-safe"]).toBe("#1C9B70");
  });
});
