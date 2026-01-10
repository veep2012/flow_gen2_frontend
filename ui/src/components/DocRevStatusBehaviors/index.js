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

const resolveBehaviorByFile = (fileKey) => {
  const normalizedKey = normalizeFileKey(fileKey);
  if (!normalizedKey) return DefaultBehavior;
  if (behaviorByExactFile[normalizedKey]) return behaviorByExactFile[normalizedKey];

  const normalized = normalizedKey.toLowerCase().trim();
  if (normalized.startsWith("idc")) return IDCBehavior;
  if (normalized.startsWith("indesign")) return InDesignBehavior;
  if (normalized.startsWith("readyforissue")) return ReadyForIssueBehavior;
  if (normalized.startsWith("official")) return OfficialBehavior;
  if (normalized.startsWith("history")) return HistoryBehavior;

  return DefaultBehavior;
};

export { resolveBehaviorByFile };
