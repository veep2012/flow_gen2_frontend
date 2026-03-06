import { afterEach, describe, expect, it } from "vitest";
import {
  buildLogoutForUserSwitchUrl,
  buildReauthUrl,
  resolveAuthStartBase,
} from "./authNavigation";

describe("authNavigation", () => {
  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        origin: "http://localhost:5558",
      },
    });
  });

  it("builds the configured re-authentication URL", () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        origin: "http://localhost:5558",
      },
    });

    const authStartBase = resolveAuthStartBase("http://localhost/oauth2/start");
    expect(buildReauthUrl(authStartBase, "/documents?tab=current#info")).toBe(
      "http://localhost/oauth2/start?rd=%2Fdocuments%3Ftab%3Dcurrent%23info",
    );
  });

  it("builds a logout URL that returns to the switch-user login flow", () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: {
        ...window.location,
        origin: "http://localhost:5558",
      },
    });

    const authStartBase = resolveAuthStartBase("http://localhost/oauth2/start");
    expect(buildLogoutForUserSwitchUrl(authStartBase, "/documents?tab=current#info")).toBe(
      "http://localhost/oauth2/sign_out?rd=http%3A%2F%2Flocalhost%2Foauth2%2Fstart%3Frd%3D%252Fdocuments%253Ftab%253Dcurrent%2523info",
    );
  });
});
