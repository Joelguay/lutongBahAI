function key(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

/** Maps typed / Roboflow spellings to the display names from GET /v1/classes. */
const ALIASES: Record<string, string> = {
  cheese: "Cheese",
  cheeze: "Cheese",
  parsley: "Parsley",
  parsely: "Parsley",
  sausage: "Sausage",
  saus: "Sausage",
  hotdog: "Sausage",
  calamansi: "Green calamansi",
  limecomg: "Green calamansi",
  greencalamansi: "Green calamansi",
  limecomy: "Yellow calamansi",
  yellowcalamansi: "Yellow calamansi",
  gbellp: "Green bell pepper",
  greenbellpepper: "Green bell pepper",
  greenbell: "Green bell pepper",
  rbellp: "Red bell pepper",
  redbellpepper: "Red bell pepper",
  redbell: "Red bell pepper",
  ybellp: "Yellow bell pepper",
  yellowbellpepper: "Yellow bell pepper",
  yellowbell: "Yellow bell pepper",
  pepperg: "Green pepper",
  greenpepper: "Green pepper",
  pepperr: "Red pepper",
  redpepper: "Red pepper",
  shrimgroup: "Shrimp",
  shrimpgroup: "Shrimp",
  shrimps: "Shrimp",
  shimp: "Shrimp",
  eggplant: "Eggplant",
  talong: "Eggplant",
};

export function resolveClassName(raw: string, classes: string[]): string | null {
  const compact = key(raw);
  if (!compact) return null;
  const byKey = new Map(classes.map((name) => [key(name), name]));
  const direct = byKey.get(compact);
  if (direct) return direct;
  const alias = ALIASES[compact];
  if (alias) return byKey.get(key(alias)) ?? null;
  return null;
}
