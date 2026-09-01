const limits = [
  {
    title: "Sensitive to lighting",
    body: "Detection works best in a well-lit kitchen. Glare, night lighting, and blurry frames will miss items.",
  },
  {
    title: "Filipino cuisine first",
    body: "Recipes stay focused on lutong bahay. The model is trained on household ingredients, not every cuisine.",
  },
  {
    title: "33 ingredients for now",
    body: "The detector knows 33 classes from best.pt. Other foods show as not yet available. Rice, toyo, and suka are pantry staples in recipes, not camera classes.",
  },
  {
    title: "Visible ingredients only",
    body: "Scan or pick from the 33-class list. The camera cannot see sauces — recipes may still use rice, oil, salt, toyo, and suka.",
  },
  {
    title: "Needs the internet",
    body: "Detection and recipe generation run on the API. You need a connection while you scan and cook.",
  },
];

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 pb-16">
      <p className="font-display text-sm uppercase tracking-widest text-muted">
        A prototype from Baura Co.
      </p>
      <h1 className="mt-2 font-display text-4xl font-semibold text-pink sm:text-5xl">
        About Lutong BahAI
      </h1>
      <p className="mt-6 text-lg leading-relaxed text-ink">
        Lutong BahAI is an AI-powered kitchen helper. You scan the ingredients
        you already have. The system identifies what it can see, then suggests
        Filipino recipes so leftovers become dinner instead of waste.
      </p>
      <p className="mt-4 text-lg leading-relaxed text-muted">
        The goal is simpler meal planning, less food waste, and recipes that
        still taste like home — adobo, giniling, torta, and the dishes families
        actually cook.
      </p>

      <h2 className="mt-12 font-display text-3xl text-pink">How it works</h2>
      <ol className="mt-4 list-decimal space-y-3 pl-5 text-ink">
        <li>Open Camera and allow the browser to use your webcam.</li>
        <li>Place ingredients in view. Add a missed class from the 33-name list if needed.</li>
        <li>Generate five recipe ideas, pick one, and cook from the steps.</li>
      </ol>

      <h2 className="mt-12 font-display text-3xl text-pink">Limits</h2>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {limits.map((limit) => (
          <article key={limit.title} className="rounded-2xl bg-white p-5 shadow-sm">
            <h3 className="font-display text-xl text-pink">{limit.title}</h3>
            <p className="mt-2 text-sm text-muted">{limit.body}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
