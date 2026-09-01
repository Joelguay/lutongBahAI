function key(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

const ALIASES: Record<string, string> = {
  cheese: "Cheeze",
  parsley: "Parsely",
  sausage: "Saus",
  hotdog: "Saus",
  calamansi: "LimeComG",
  greencalamansi: "LimeComG",
  yellowcalamansi: "LimeComY",
  greenbellpepper: "GBellP",
  greenbell: "GBellP",
  redbellpepper: "RBellP",
  redbell: "RBellP",
  yellowbellpepper: "YBellP",
  yellowbell: "YBellP",
  greenpepper: "PepperG",
  redpepper: "PepperR",
  shrimpgroup: "ShrimGroup",
  shrimps: "ShrimGroup",
  eggplant: "EggPlant",
  talong: "EggPlant",
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
