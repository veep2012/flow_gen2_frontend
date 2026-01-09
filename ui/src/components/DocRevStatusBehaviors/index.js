import DefaultBehavior from "./DefaultBehavior";
import HistoryBehavior from "./HistoryBehavior";
import IDCBehavior from "./IDCBehavior";
import InDesignBehavior from "./InDesignBehavior";
import OfficialBehavior from "./OfficialBehavior";
import ReadyForIssueBehavior from "./ReadyForIssueBehavior";

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
