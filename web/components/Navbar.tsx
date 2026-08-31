"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/", label: "home" },
  { href: "/about", label: "about" },
  { href: "/camera", label: "camera" },
  { href: "/manual", label: "manual" },
  { href: "/support", label: "support us" },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 z-50 w-full">
      <div className="mx-auto flex h-20 max-w-6xl items-center justify-between px-5">
        <div className="pointer-events-none absolute inset-0 rounded-b-[28px] bg-white/70 shadow-sm" />
        <Link href="/" className="relative z-10 flex items-center" onClick={() => setOpen(false)}>
          <Image
            src="/pic/Logo.png"
            alt="Lutong BahAI"
            width={140}
            height={70}
            className="h-14 w-auto"
            priority
          />
        </Link>
        <button
          type="button"
          className="relative z-10 rounded-full px-3 py-2 font-display text-pink md:hidden"
          aria-label="Toggle menu"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? "close" : "menu"}
        </button>
        <ul className="relative z-10 hidden items-center gap-8 font-display text-lg lowercase md:flex">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={`pb-1 transition-colors ${
                    active
                      ? "text-pink border-b-2 border-pink"
                      : "text-muted hover:text-pink hover:border-b-2 hover:border-pink"
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
      {open ? (
        <ul className="relative z-10 mx-4 mt-1 space-y-2 rounded-2xl bg-white/95 p-4 shadow-md font-display lowercase md:hidden">
          {links.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="block rounded-lg px-3 py-2 text-muted hover:bg-cream hover:text-pink"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </nav>
  );
}
