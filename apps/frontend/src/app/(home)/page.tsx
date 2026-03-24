'use client';

import Link from 'next/link';
import { BackgroundAALChecker } from '@/components/auth/background-aal-checker';
import { HeroSection as NewHeroSection } from '@/components/home/hero-section';
import { SimpleFooter } from '@/components/home/simple-footer';

const homeCards = [
  {
    title: 'Founder workflows, not generic chat',
    description:
      'Pitch support, valuation logic, investor matching, and execution workflows in one startup-native system.',
  },
  {
    title: 'Shared startup intelligence',
    description:
      'Enter startup context once, then every app learns from that context so teams avoid repeating work.',
  },
  {
    title: 'Built with venture DNA',
    description:
      'Created by Brinc for founders, operators, and investors working through real fundraising and growth decisions.',
  },
];

export default function Home() {
  return (
    <BackgroundAALChecker>
      <div className="min-h-dvh bg-background">
        <div className="h-dvh">
          <NewHeroSection />
        </div>

        <section className="border-t border-border/60">
          <div className="mx-auto w-full max-w-6xl px-6 py-16 md:px-10 md:py-20">
            <div className="max-w-3xl">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                VentureVerse Platform
              </p>
              <h2 className="mt-4 text-3xl font-semibold tracking-tight text-foreground md:text-5xl">
                Built to help ventures execute faster
              </h2>
              <p className="mt-4 text-base leading-relaxed text-muted-foreground md:text-lg">
                VentureVerse is the AI Venture Operating System that helps teams build, fund, and scale with connected
                intelligence across every core workflow.
              </p>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {homeCards.map((card) => (
                <div key={card.title} className="rounded-2xl border border-border/70 bg-card/40 p-6">
                  <h3 className="text-lg font-semibold text-foreground">{card.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{card.description}</p>
                </div>
              ))}
            </div>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link
                href="/about"
                className="inline-flex items-center rounded-xl bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:bg-foreground/90"
              >
                About VentureVerse
              </Link>
              <Link
                href="https://ventureverse.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center rounded-xl border border-border bg-background px-4 py-2.5 text-sm font-medium text-foreground hover:bg-accent"
              >
                VentureVerse.com
              </Link>
            </div>
          </div>
        </section>

        <SimpleFooter />
      </div>
    </BackgroundAALChecker>
  );
}
