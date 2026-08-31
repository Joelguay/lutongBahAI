import Link from "next/link";

const features = [
  {
    title: "Easy to Use",
    body: "Scan your ingredients and we suggest authentic Filipino recipes instantly.",
  },
  {
    title: "Authenticity",
    body: "Traditional Filipino dishes passed down through generations, now at your fingertips.",
  },
  {
    title: "Beginner Friendly",
    body: "Perfect for all skill levels, from first-time cooks to experienced lutong bahay.",
  },
];

export default function HomePage() {
  return (
    <div>
      <section className="mx-auto flex max-w-3xl flex-col items-center px-6 pb-16 pt-10 text-center">
        <p className="font-display text-sm tracking-[0.3em] text-muted uppercase">
          An AI-powered system
        </p>
        <h1 className="mt-3 font-display text-5xl font-semibold tracking-wide text-pink sm:text-7xl">
          LUTONG BAHAI
        </h1>
        <p className="mt-6 max-w-xl text-lg text-muted">
          Point your camera at what you have in the kitchen. We detect the
          ingredients and suggest five Filipino recipes you can cook today.
        </p>
        <Link
          href="/camera"
          className="mt-10 inline-block rounded-full bg-pink px-12 py-3 font-display text-2xl font-semibold uppercase text-white shadow-md transition hover:bg-pink-dark"
        >
          Start
        </Link>
      </section>

      <section className="bg-cream-dark/60 px-6 py-16">
        <div className="mx-auto max-w-5xl text-center">
          <p className="font-display text-sm text-muted">As of 2025</p>
          <h2 className="font-display text-4xl font-semibold text-pink sm:text-5xl">
            Features
          </h2>
          <p className="mt-2 font-display text-xl text-ink">That you&apos;ll love!</p>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {features.map((feature) => (
              <article
                key={feature.title}
                className="rounded-3xl bg-white p-8 text-left shadow-sm"
              >
                <h3 className="font-display text-2xl text-pink">{feature.title}</h3>
                <p className="mt-3 text-muted">{feature.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
