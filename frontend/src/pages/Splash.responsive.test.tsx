import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import Splash from "./Splash";

const __dirname = dirname(fileURLToPath(import.meta.url));

describe("Splash responsive / reduced-motion (CSS rules)", () => {
  it("logo uses aspect-preserving, viewport-bounded classes (no clipping)", () => {
    vi.useFakeTimers();
    render(<Splash onDone={() => {}} />);
    const img = screen.getByTestId("splash-logo-img");
    // object-contain preserves aspect ratio; max-h/max-w keep it within the
    // viewport (320px..large) without clipping; h-auto/w-auto avoid distortion.
    expect(img.className).toContain("object-contain");
    expect(img.className).toContain("max-h-[40vh]");
    expect(img.className).toContain("max-w-[80vw]");
    expect(img.className).toContain("h-auto");
    expect(img.className).toContain("w-auto");
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("stylesheet defines the entrance animation within 300-800ms and a reduced-motion guard", () => {
    const css = readFileSync(resolve(__dirname, "../styles/index.css"), "utf8");

    // Animation keyframes + class exist.
    expect(css).toMatch(/@keyframes\s+splash-enter/);
    expect(css).toMatch(/\.splash-enter\s*\{[^}]*animation:\s*splash-enter\s+(\d+)ms/);

    // Duration is within the allowed 300-800ms range.
    const m = css.match(/animation:\s*splash-enter\s+(\d+)ms/);
    expect(m).not.toBeNull();
    const durationMs = Number(m![1]);
    expect(durationMs).toBeGreaterThanOrEqual(300);
    expect(durationMs).toBeLessThanOrEqual(800);

    // prefers-reduced-motion disables the entrance animation.
    expect(css).toMatch(
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[\s\S]*\.splash-enter\s*\{[^}]*animation:\s*none/,
    );
  });
});
