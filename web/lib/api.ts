export type DetectBox = {
  name: string;
  conf: number;
  xyxy: number[];
};

export type DetectResponse = {
  mode: "mock" | "yolo" | string;
  ingredients: string[];
  boxes: DetectBox[];
};

export type RecipeSummary = {
  name: string;
  description: string;
};

export type RecipeSteps = {
  name: string;
  servings: string;
  allergens: string;
  ingredients: string[];
  steps: { title: string; detail: string }[];
  notes: string[];
  reference: string;
};

export type HealthResponse = {
  ok: boolean;
  detector: string;
  classes: string[];
  openai_configured: boolean;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function readError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: string };
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* ignore */
  }
  return res.statusText;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/v1/health`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function detectFrame(blob: Blob, conf: number): Promise<DetectResponse> {
  const form = new FormData();
  form.append("file", blob, "frame.jpg");
  const res = await fetch(`${API_URL}/v1/detect?conf=${conf}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchRecipes(ingredients: string[]): Promise<RecipeSummary[]> {
  const res = await fetch(`${API_URL}/v1/recipes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ingredients }),
  });
  if (!res.ok) throw new Error(await readError(res));
  const data = (await res.json()) as { recipes: RecipeSummary[] };
  return data.recipes;
}

export async function fetchRecipeSteps(
  name: string,
  ingredients: string[],
): Promise<RecipeSteps> {
  const res = await fetch(`${API_URL}/v1/recipes/steps`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, ingredients }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
