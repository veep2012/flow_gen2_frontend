import DefaultBehavior from "./DefaultBehavior";
import HistoryBehavior from "./HistoryBehavior";
import IDCBehavior from "./IDCBehavior";
import InDesignBehavior from "./InDesignBehavior";
import OfficialBehavior from "./OfficialBehavior";
import ReadyForIssueBehavior from "./ReadyForIssueBehavior";

const behaviorByExactName = {
  InDesign: InDesignBehavior,
  IDC: IDCBehavior,
  "Ready for Issue": ReadyForIssueBehavior,
  Official: OfficialBehavior,
  History: HistoryBehavior,
};

const resolveBehaviorByName = (name) => {
  if (!name) return DefaultBehavior;
  if (behaviorByExactName[name]) return behaviorByExactName[name];

  const normalized = name.toLowerCase().trim();
  if (normalized.startsWith("idc")) return IDCBehavior;
  if (normalized.startsWith("indesign")) return InDesignBehavior;
  if (normalized.startsWith("ready for issue")) return ReadyForIssueBehavior;
  if (normalized.startsWith("official")) return OfficialBehavior;
  if (normalized.startsWith("history")) return HistoryBehavior;

  return DefaultBehavior;
};

export { resolveBehaviorByName };
