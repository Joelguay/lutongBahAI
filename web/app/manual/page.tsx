const steps = [
  {
    title: "Open the website",
    body: "Load Lutong BahAI in your browser. The homepage explains what the app does; Camera is where cooking starts.",
  },
  {
    title: "Access the camera",
    body: "Click Start on the home page or Camera in the nav. Allow permission when the browser asks.",
  },
  {
    title: "Scan ingredients",
    body: "Place what you have in view. Detected names appear as chips. If the camera misses one, pick it from the 33-class list.",
  },
  {
    title: "Generate recipes",
    body: "Click Show recipes. We send your ingredient list to the API and return five Filipino dishes.",
  },
  {
    title: "Select a recipe",
    body: "Pick the one you want to cook. You will get servings, allergens, ingredients, and step-by-step instructions.",
  },
  {
    title: "Start cooking",
    body: "Follow the steps in your kitchen. Use Back if you want another dish from the same scan.",
  },
];

export default function ManualPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 pb-16">
      <h1 className="text-center font-display text-4xl font-semibold text-pink sm:text-5xl">
        User manual
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-center text-muted">
        Six steps from leftover ingredients to a Filipino recipe.
      </p>
      <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {steps.map((step, index) => (
          <article key={step.title} className="rounded-3xl bg-white p-6 shadow-sm">
            <p className="font-display text-sm text-pink">Step {index + 1}</p>
            <h2 className="mt-1 font-display text-2xl text-ink">{step.title}</h2>
            <p className="mt-3 text-muted">{step.body}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
