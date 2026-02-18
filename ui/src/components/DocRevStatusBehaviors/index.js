import React from "react";
import DefaultBehavior from "./DefaultBehavior";

const HistoryBehavior = React.lazy(() => import("./HistoryBehavior"));
const IDCBehavior = React.lazy(() => import("./IDCBehavior"));
const InDesignBehavior = React.lazy(() => import("./InDesignBehavior"));
const OfficialBehavior = React.lazy(() => import("./OfficialBehavior"));
const ReadyForIssueBehavior = React.lazy(() => import("./ReadyForIssueBehavior"));

const behaviorByExactFile = {
  InDesignBehavior,
  IDCBehavior,
  ReadyForIssueBehavior,
  OfficialBehavior,
  HistoryBehavior,
};

const normalizeFileKey = (fileKey) =>
  typeof fileKey === "string" ? fileKey.replace(/\.jsx$/i, "") : "";

const normalizeBehaviorToken = (value) =>
  typeof value === "string" ? value.toLowerCase().replace(/[^a-z0-9]/g, "") : "";

const resolveBehaviorByFile = (fileKey, behaviorName = "") => {
  const normalizedKey = normalizeFileKey(fileKey);
  if (normalizedKey && behaviorByExactFile[normalizedKey]) {
    return behaviorByExactFile[normalizedKey];
  }

  const candidates = [
    normalizeBehaviorToken(normalizedKey),
    normalizeBehaviorToken(behaviorName),
  ].filter(Boolean);

  if (
    candidates.some((token) => token.startsWith("idc") || token.includes("interdisciplinecheck"))
  ) {
    return IDCBehavior;
  }
  if (candidates.some((token) => token.startsWith("indesign"))) {
    return InDesignBehavior;
  }
  if (candidates.some((token) => token.startsWith("readyforissue") || token.startsWith("rfi"))) {
    return ReadyForIssueBehavior;
  }
  if (candidates.some((token) => token.startsWith("official"))) {
    return OfficialBehavior;
  }
  if (candidates.some((token) => token.startsWith("history"))) {
    return HistoryBehavior;
  }

  if (normalizedKey) {
    return DefaultBehavior;
  }
  if (behaviorName) {
    return DefaultBehavior;
  }

  return DefaultBehavior;
};

export { resolveBehaviorByFile };
