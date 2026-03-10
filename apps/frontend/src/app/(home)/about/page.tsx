'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { SimpleFooter } from '@/components/home/simple-footer';

const corePillars = [
  {
    title: 'Built by founders, for founders',
    description:
      'VentureVerse is built by Brinc, a global venture accelerator. The platform is designed around real founder workflows, not generic prompts.',
  },
  {
    title: 'One startup context across all apps',
    description:
      'Use one app, and every other app learns about your startup. Your pitch, valuation, and investor workflow stay connected.',
  },
  {
    title: 'Startup-native AI training',
    description:
      'Each app is trained on thousands of startup documents and outcomes, so responses stay grounded in venture execution.',
  },
];

const highlights = [
  {
    value: '20M+',
    label: 'Startup Profiles in Data Layer',
  },
  {
    value: '10K+',
    label: 'Pitch Decks and Venture Documents',
  },
  {
    value: 'Global',
    label: 'Founder and Investor Ecosystem',
  },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-background">
      <article className="mx-auto w-full max-w-6xl px-6 pb-24 pt-28 md:px-10">
        <section className="grid gap-10 lg:grid-cols-[1.2fr_1fr] lg:items-end">
          <div className="space-y-6">
            <Image
              src="/ventureverse-logomark-light.svg"
              alt="VentureVerse"
              width={220}
              height={64}
              className="dark:hidden"
              priority
            />
            <Image
              src="/ventureverse-logomark-dark.svg"
              alt="VentureVerse"
              width={220}
              height={64}
              className="hidden dark:block"
              priority
            />
            <h1 className="text-4xl font-semibold tracking-tight text-foreground md:text-6xl">
              The AI Venture Operating System
            </h1>
            <p className="max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl">
              Build, grow, and scale your venture with AI workflows purpose-built for founders and investors.
              VentureVerse helps teams move faster from strategy to execution.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {highlights.map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-border/70 bg-card/50 p-5 backdrop-blur"
              >
                <p className="text-3xl font-semibold tracking-tight text-foreground">{item.value}</p>
                <p className="mt-1 text-sm text-muted-foreground">{item.label}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-14 overflow-hidden rounded-3xl border border-border/70 bg-card/30">
          <div className="relative aspect-[16/8] w-full">
            <Image
              src="/ventureverse-about-banner.svg"
              alt="VentureVerse product banner"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 1200px"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/80 via-background/20 to-transparent" />
          </div>
        </section>

        <section className="mt-16 grid gap-6 md:grid-cols-3">
          {corePillars.map((pillar) => (
            <div key={pillar.title} className="rounded-2xl border border-border/70 bg-card/40 p-6">
              <h2 className="text-xl font-semibold tracking-tight text-foreground">{pillar.title}</h2>
              <p className="mt-3 leading-relaxed text-muted-foreground">{pillar.description}</p>
            </div>
          ))}
        </section>

        <section className="mt-16 rounded-3xl border border-border/70 bg-card/40 p-8 md:p-10">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">
            Why founders choose VentureVerse
          </h2>
          <p className="mt-4 max-w-3xl leading-relaxed text-muted-foreground">
            VentureVerse combines pitch support, valuation workflows, investor matching, and venture operations in one
            connected system. Instead of disconnected point tools, your team gets a single AI layer that compounds
            context as you build.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-xl bg-foreground px-4 py-2.5 text-sm font-medium text-background hover:bg-foreground/90"
            >
              Explore Platform
              <ArrowRight className="size-4" />
            </Link>
            <Link
              href="https://ventureverse.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-background px-4 py-2.5 text-sm font-medium text-foreground hover:bg-accent"
            >
              Visit VentureVerse.com
            </Link>
          </div>
        </section>
      </article>

      <SimpleFooter />
    </main>
  );
}
