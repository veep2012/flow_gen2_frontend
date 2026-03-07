import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App.jsx";

function jsonResponse(status, body, requestId) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...(requestId ? { "X-Request-Id": requestId } : {}),
    },
  });
}

function buildFetchMock(currentUserStatus, detail, requestId) {
  return vi.fn((input) => {
    const url = String(input);
    if (url.includes("/people/users/current_user")) {
      return Promise.resolve(jsonResponse(currentUserStatus, { detail }, requestId));
    }
    return Promise.resolve(jsonResponse(200, []));
  });
}

describe("App auth error screen", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", buildFetchMock(401, "Authentication required", "req-401"));
    vi.unstubAllEnvs();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("renders the dedicated auth error page for 401 responses", async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sign-in is required" })).toBeInTheDocument();
    });

    expect(screen.getByText(/Status:/)).toHaveTextContent("Status: 401 · Authentication required");
    expect(screen.getByText(/Request ID:/)).toHaveTextContent("Request ID: req-401");
    expect(screen.getByRole("button", { name: "Refresh session" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in as different user" })).toBeInTheDocument();
  });

  it("uses the configured auth entrypoint for re-authentication", async () => {
    const assign = vi.fn();
    vi.stubGlobal("fetch", buildFetchMock(401, "Authentication required", "req-401"));
    vi.stubEnv("VITE_AUTH_START_URL", "http://localhost/oauth2/start");

    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        origin: "http://localhost:5558",
        pathname: "/documents",
        search: "?tab=current",
        hash: "#info",
        assign,
      },
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sign in as different user" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign in as different user" }));

    expect(assign).toHaveBeenCalledWith(
      "http://localhost/oauth2/start?rd=%2Fdocuments%3Ftab%3Dcurrent%23info",
    );
  });

  it("routes logout through sign_out and back into switch-user login", async () => {
    const assign = vi.fn();
    vi.stubGlobal("fetch", buildFetchMock(200, "Authentication required", "req-200"));
    vi.stubEnv("VITE_AUTH_START_URL", "http://localhost/oauth2/start");

    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        origin: "http://localhost:5558",
        pathname: "/documents",
        search: "?tab=current",
        hash: "#info",
        assign,
      },
    });

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /konstantin ni designer/i }));
    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(assign).toHaveBeenCalledWith(
      "http://localhost/oauth2/sign_out?rd=http%3A%2F%2Flocalhost%2Foauth2%2Fstart%3Frd%3D%252Fdocuments%253Ftab%253Dcurrent%2523info",
    );
  });

  it("renders the dedicated auth error page for 400 responses", async () => {
    vi.stubGlobal(
      "fetch",
      buildFetchMock(400, "Invalid X-User-Id header. Expected existing user_acronym.", "req-400"),
    );

    render(<App />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Session verification failed" }),
      ).toBeInTheDocument();
    });

    expect(screen.getByText(/Status:/)).toHaveTextContent(
      "Status: 400 · Invalid X-User-Id header. Expected existing user_acronym.",
    );
    expect(screen.getByText(/Request ID:/)).toHaveTextContent("Request ID: req-400");
  });
});
