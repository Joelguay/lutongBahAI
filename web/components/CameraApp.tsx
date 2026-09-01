"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  detectFrame,
  fetchRecipeSteps,
  fetchRecipes,
  getHealth,
  type DetectBox,
  type HealthResponse,
  type RecipeSteps,
  type RecipeSummary,
} from "@/lib/api";
import { resolveClassName } from "@/lib/ingredients";

type View = "camera" | "list" | "steps";

function captureJpeg(video: HTMLVideoElement): Promise<Blob | null> {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  if (!canvas.width || !canvas.height) return Promise.resolve(null);
  const ctx = canvas.getContext("2d");
  if (!ctx) return Promise.resolve(null);
  ctx.drawImage(video, 0, 0);
  return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.72));
}

export function CameraApp() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const busyRef = useRef(false);

  const [cameraOn, setCameraOn] = useState(false);
  const [conf, setConf] = useState(0.5);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [boxes, setBoxes] = useState<DetectBox[]>([]);
  const [detected, setDetected] = useState<string[]>([]);
  const [manual, setManual] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [view, setView] = useState<View>("camera");
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [steps, setSteps] = useState<RecipeSteps | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classes = health?.classes ?? [];
  const ingredients = Array.from(new Set([...detected, ...manual]));

  useEffect(() => {
    getHealth()
      .then((data) => {
        setHealth(data);
        setHealthError(null);
      })
      .catch((err: Error) => {
        setHealthError(err.message || "API is not reachable. Start the FastAPI server on port 8000.");
      });
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
    setBoxes([]);
  }, []);

  const startCamera = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);
    } catch {
      setError("Camera permission was denied or no camera is available.");
    }
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const drawBoxes = useCallback((next: DetectBox[]) => {
    const canvas = overlayRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const width = video.clientWidth;
    const height = video.clientHeight;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = "#e47c82";
    ctx.lineWidth = 2;
    ctx.font = "14px Fredoka, sans-serif";
    for (const box of next) {
      const [x1, y1, x2, y2] = box.xyxy;
      const left = x1 * width;
      const top = y1 * height;
      const boxW = (x2 - x1) * width;
      const boxH = (y2 - y1) * height;
      ctx.strokeRect(left, top, boxW, boxH);
      const label = `${box.name} ${Math.round(box.conf * 100)}%`;
      const textW = ctx.measureText(label).width;
      ctx.fillStyle = "#e47c82";
      ctx.fillRect(left, Math.max(0, top - 20), textW + 8, 20);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, left + 4, Math.max(14, top - 5));
    }
  }, []);

  useEffect(() => {
    drawBoxes(boxes);
  }, [boxes, drawBoxes]);

  useEffect(() => {
    if (!cameraOn || view !== "camera") return;
    const id = window.setInterval(async () => {
      const video = videoRef.current;
      if (!video || busyRef.current) return;
      busyRef.current = true;
      try {
        const blob = await captureJpeg(video);
        if (!blob) return;
        const result = await detectFrame(blob, conf);
        setDetected(result.ingredients);
        setBoxes(result.boxes);
      } catch {
        /* keep last good frame */
      } finally {
        busyRef.current = false;
      }
    }, 700);
    return () => window.clearInterval(id);
  }, [cameraOn, conf, view]);

  const addManual = () => {
    const name = draft.trim();
    if (!name) return;
    const resolved = resolveClassName(name, classes);
    if (!resolved) {
      setError(`"${name}" is not yet available.`);
      return;
    }
    setError(null);
    setManual((prev) => (prev.includes(resolved) ? prev : [...prev, resolved]));
    setDraft("");
  };

  const removeIngredient = (name: string) => {
    setDetected((prev) => prev.filter((item) => item !== name));
    setManual((prev) => prev.filter((item) => item !== name));
  };

  const showRecipes = async () => {
    if (ingredients.length === 0) {
      setError("Add at least one ingredient (scan or pick a class).");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const next = await fetchRecipes(ingredients);
      setRecipes(next);
      setView("list");
      stopCamera();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load recipes.");
    } finally {
      setLoading(false);
    }
  };

  const openSteps = async (name: string) => {
    setLoading(true);
    setError(null);
    try {
      const next = await fetchRecipeSteps(name, ingredients);
      setSteps(next);
      setView("steps");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load recipe steps.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <p className="py-24 text-center font-display text-xl text-muted">
        {view === "camera" ? "Finding recipes for you..." : "Writing your recipe steps..."}
      </p>
    );
  }

  if (view === "list") {
    return (
      <div className="mx-auto max-w-3xl px-6 pb-16">
        <div className="mb-6 flex items-center justify-between gap-4">
          <h1 className="font-display text-3xl text-pink">Top Filipino recipes</h1>
          <button
            type="button"
            className="rounded-full bg-white px-4 py-2 text-sm text-pink shadow-sm"
            onClick={() => {
              setView("camera");
              setError(null);
            }}
          >
            ← Back to camera
          </button>
        </div>
        {error ? <p className="mb-4 text-pink">{error}</p> : null}
        <div className="space-y-4">
          {recipes.map((recipe) => (
            <article key={recipe.name} className="rounded-2xl bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  className="rounded-full border border-pink/40 px-3 py-1 text-sm text-pink"
                  onClick={() => openSteps(recipe.name)}
                >
                  View steps
                </button>
                <h2 className="font-display text-2xl">{recipe.name}</h2>
              </div>
              <p className="mt-2 text-muted">{recipe.description}</p>
            </article>
          ))}
        </div>
      </div>
    );
  }

  if (view === "steps" && steps) {
    return (
      <div className="mx-auto max-w-3xl px-6 pb-16">
        <div className="mb-6 flex items-center justify-between gap-4">
          <h1 className="font-display text-3xl text-pink">{steps.name}</h1>
          <button
            type="button"
            className="rounded-full bg-white px-4 py-2 text-sm text-pink shadow-sm"
            onClick={() => {
              setView("list");
              setSteps(null);
            }}
          >
            ← Back to list
          </button>
        </div>
        <div className="rounded-2xl bg-white p-5 shadow-sm">
          <p>
            <strong>Servings:</strong> {steps.servings}
          </p>
          <p className="mt-1">
            <strong>Allergens:</strong> {steps.allergens}
          </p>
        </div>
        <section className="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="font-display text-xl text-pink">Ingredients</h2>
          <ul className="mt-2 list-disc pl-5">
            {steps.ingredients.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        <section className="mt-4 rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="font-display text-xl text-pink">Steps</h2>
          <ol className="mt-3 space-y-4">
            {steps.steps.map((step, index) => (
              <li key={`${step.title}-${index}`}>
                <p className="font-semibold">
                  {index + 1}. {step.title}
                </p>
                <p className="mt-1 text-muted">{step.detail}</p>
              </li>
            ))}
          </ol>
        </section>
        {steps.notes.length > 0 ? (
          <section className="mt-4 rounded-2xl bg-white p-5 shadow-sm">
            <h2 className="font-display text-xl text-pink">Tips & notes</h2>
            <ul className="mt-2 list-disc pl-5 text-muted">
              {steps.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 pb-16">
      <h1 className="text-center font-display text-4xl text-pink">Place an ingredient</h1>
      <p className="mt-2 text-center text-muted">
        Your browser camera stays on this device. Frames are sent to the API for
        detection.
      </p>

      {healthError ? (
        <p className="mt-4 rounded-2xl bg-white p-4 text-center text-pink shadow-sm">{healthError}</p>
      ) : null}
      {health?.detector === "mock" ? (
        <p className="mt-4 rounded-2xl bg-white p-4 text-center text-muted shadow-sm">
          Detection is in mock mode (no <code>best.pt</code> yet). Pick a class
          from the list below — recipes still work when Gemini is configured.
        </p>
      ) : null}

      <div className="relative mx-auto mt-6 aspect-[4/3] w-full max-w-[640px] overflow-hidden rounded-2xl bg-black">
        <video
          ref={videoRef}
          className="h-full w-full object-cover"
          playsInline
          muted
        />
        <canvas ref={overlayRef} className="pointer-events-none absolute inset-0 h-full w-full" />
        {!cameraOn ? (
          <div className="absolute inset-0 flex items-center justify-center font-display text-2xl text-white">
            CAMERA OFF
          </div>
        ) : null}
      </div>

      <div className="mx-auto mt-4 flex max-w-[640px] items-center gap-3">
        <label className="text-sm text-muted" htmlFor="conf">
          Confidence {Math.round(conf * 100)}%
        </label>
        <input
          id="conf"
          type="range"
          min={0.2}
          max={0.9}
          step={0.05}
          value={conf}
          onChange={(event) => setConf(Number(event.target.value))}
          className="flex-1"
        />
      </div>

      <div className="mt-6 flex flex-wrap justify-center gap-4">
        <button
          type="button"
          className="rounded-full bg-pink px-8 py-3 font-display text-lg font-semibold text-white"
          onClick={() => (cameraOn ? stopCamera() : startCamera())}
        >
          {cameraOn ? "Turn off camera" : "Turn on camera"}
        </button>
        <button
          type="button"
          className="rounded-full bg-pink px-8 py-3 font-display text-lg font-semibold text-white"
          onClick={showRecipes}
        >
          Show recipes
        </button>
      </div>

      <section className="mx-auto mt-8 max-w-[640px]">
        <h2 className="font-display text-xl text-pink">Ingredients</h2>
        <p className="mt-1 text-sm text-muted">
          This version recognizes {classes.length || 33} ingredients. Scan or pick
          from the list. Rice, toyo, and suka are assumed in recipes.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {ingredients.length === 0 ? (
            <p className="text-sm text-muted">None yet — scan or pick a class.</p>
          ) : (
            ingredients.map((name) => (
              <button
                key={name}
                type="button"
                className="rounded-full bg-white px-3 py-1 text-sm shadow-sm"
                onClick={() => removeIngredient(name)}
              >
                {name} ×
              </button>
            ))
          )}
        </div>
        <form
          className="mt-4 flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            addManual();
          }}
        >
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            list="ingredient-classes"
            placeholder="Pick a class, e.g. Garlic"
            className="flex-1 rounded-full border border-black/10 bg-white px-4 py-2"
          />
          <datalist id="ingredient-classes">
            {classes.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
          <button
            type="submit"
            className="rounded-full bg-pink px-5 py-2 font-display text-white"
          >
            Add
          </button>
        </form>
      </section>

      {error ? <p className="mt-6 text-center text-pink">{error}</p> : null}
    </div>
  );
}
