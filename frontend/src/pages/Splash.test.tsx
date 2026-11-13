import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LOGO_SRC } from "../components/SplashLogo";
import Splash, { SPLASH_DURATION_MS } from "./Splash";

describe("Splash screen (Task 1.6 / Req 1)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("renders ONLY the logo, the name, and the tagline (no nav/buttons/forms/footer)", () => {
    render(<Splash onDone={() => {}} />);

    // Logo image present with the official asset source and a non-empty alt.
    const img = screen.getByTestId("splash-logo-img") as HTMLImageElement;
    expect(img.getAttribute("src")).toBe(LOGO_SRC);
    expect(img.getAttribute("alt")).toBe("KHABARDAR");

    // Name and tagline (default English).
    expect(screen.getByText("KHABARDAR")).toBeInTheDocument();
    expect(screen.getByText("Think Before You Trust.")).toBeInTheDocument();

    // Forbidden elements are absent.
    const screenEl = screen.getByTestId("splash-screen");
    expect(screenEl.querySelector("nav")).toBeNull();
    expect(screenEl.querySelector("button")).toBeNull();
    expect(screenEl.querySelector("input")).toBeNull();
    expect(screenEl.querySelector("form")).toBeNull();
    expect(screenEl.querySelector("footer")).toBeNull();
  });

  it("uses the full-screen Deep Navy background token and the entrance animation class", () => {
    render(<Splash onDone={() => {}} />);
    const screenEl = screen.getByTestId("splash-screen");
    expect(screenEl.className).toContain("bg-deep-navy");
    expect(screenEl.className).toContain("fixed");
    // Entrance animation wrapper present (duration/behavior defined in CSS).
    expect(screenEl.querySelector(".splash-enter")).not.toBeNull();
  });

  it("auto-advances exactly once after ~2 seconds (timer behavior)", () => {
    const onDone = vi.fn();
    render(<Splash onDone={onDone} />);

    expect(onDone).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(SPLASH_DURATION_MS - 1);
    });
    expect(onDone).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  it("clears the timer on unmount (no transition after unmount)", () => {
    const onDone = vi.fn();
    const { unmount } = render(<Splash onDone={onDone} />);
    unmount();
    act(() => {
      vi.advanceTimersByTime(SPLASH_DURATION_MS * 2);
    });
    expect(onDone).not.toHaveBeenCalled();
  });

  it("logo success path: image is shown and no fallback placeholder", () => {
    render(<Splash onDone={() => {}} />);
    expect(screen.getByTestId("splash-logo-img")).toBeInTheDocument();
    expect(screen.queryByTestId("splash-logo-fallback")).toBeNull();
  });

  it("logo failure path: fallback renders name+tagline and the timer still fires", () => {
    const onDone = vi.fn();
    render(<Splash onDone={onDone} />);

    // Simulate the logo asset failing to load.
    const img = screen.getByTestId("splash-logo-img");
    act(() => {
      img.dispatchEvent(new Event("error"));
    });

    // Image replaced by the fallback placeholder; name + tagline still shown.
    expect(screen.queryByTestId("splash-logo-img")).toBeNull();
    expect(screen.getByTestId("splash-logo-fallback")).toBeInTheDocument();
    expect(screen.getByText("KHABARDAR")).toBeInTheDocument();
    expect(screen.getByText("Think Before You Trust.")).toBeInTheDocument();

    // The transition timer is unaffected by the logo failure.
    act(() => {
      vi.advanceTimersByTime(SPLASH_DURATION_MS);
    });
    expect(onDone).toHaveBeenCalledTimes(1);
  });
});
