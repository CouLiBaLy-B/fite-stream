"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Images, Activity, Zap, ArrowRight } from "lucide-react";

const stats = [
  { label: "Pipelines", value: "6" },
  { label: "Styles", value: "10" },
  { label: "Endpoints", value: "35+" },
  { label: "Languages", value: "8" },
];

const features = [
  {
    icon: "📸",
    title: "Animate",
    desc: "Photo + prompt → fluid video",
    href: "/create?mode=animate",
    color: "from-purple/20 to-purple/5",
  },
  {
    icon: "📖",
    title: "Story Mode",
    desc: "Multi-scene narratives with auto-transitions",
    href: "/create?mode=story",
    color: "from-pink/20 to-pink/5",
  },
  {
    icon: "👗",
    title: "Virtual Try-On",
    desc: "Person + garment → walking video",
    href: "/create?mode=tryon",
    color: "from-emerald/20 to-emerald/5",
  },
  {
    icon: "🎨",
    title: "Compose",
    desc: "2-8 images combined with @Image refs",
    href: "/create?mode=compose",
    color: "from-blue-500/20 to-blue-500/5",
  },
  {
    icon: "🎭",
    title: "Style Transfer",
    desc: "Ghibli, Pixar, Noir, Cyberpunk...",
    href: "/create?mode=style",
    color: "from-amber-500/20 to-amber-500/5",
  },
  {
    icon: "⚡",
    title: "Real-Time",
    desc: "23.8 FPS streaming (FashionChameleon)",
    href: "/create?mode=realtime",
    color: "from-purple/20 to-pink/20",
  },
];

export default function Home() {
  return (
    <div className="max-w-[1200px] mx-auto px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass mb-6">
          <Zap className="size-3.5 text-amber-400" />
          <span className="text-[12px] font-medium">Powered by Wan VACE 1.3B & LoomVideo</span>
        </div>
        
        <h1 className="text-[clamp(36px,6vw,64px)] font-[800] tracking-[-0.02em] leading-[1.05] mb-4">
          Turn Photos Into
          <br />
          <span className="bg-gradient-to-r from-purple via-pink to-emerald bg-clip-text text-transparent">
            Living Stories
          </span>
        </h1>
        
        <p className="text-[17px] leading-relaxed text-muted max-w-[580px] mx-auto mb-8">
          Upload a photo of anyone. Write a prompt. Get fluid AI-generated animations — 
          virtual try-on, storytelling, style transfer. Production-ready API.
        </p>

        <div className="flex items-center justify-center gap-3">
          <Link
            href="/create"
            className="group inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-black font-medium text-[14px] hover:bg-white/90 transition-all"
          >
            <Sparkles className="size-4" />
            Open Creator
            <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/gallery"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl glass glass-hover font-medium text-[14px]"
          >
            <Images className="size-4" />
            Browse Gallery
          </Link>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/[0.06] rounded-2xl overflow-hidden mb-16 border border-white/[0.06]"
      >
        {stats.map((s) => (
          <div key={s.label} className="bg-panel/50 backdrop-blur px-6 py-8 text-center">
            <div className="text-[32px] font-bold tracking-tight">{s.value}</div>
            <div className="text-[12px] uppercase tracking-wider text-muted mt-1">{s.label}</div>
          </div>
        ))}
      </motion.div>

      <div className="mb-4">
        <h2 className="text-[22px] font-semibold tracking-tight mb-2">Generation Pipelines</h2>
        <p className="text-[14px] text-muted">Six powerful modes for every creative need</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3 mb-16">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * i }}
          >
            <Link
              href={f.href}
              className="group block glass glass-hover rounded-2xl p-5 h-full"
            >
              <div className={`size-10 rounded-xl bg-gradient-to-br ${f.color} border border-white/10 flex items-center justify-center text-[20px] mb-3 group-hover:scale-105 transition-transform`}>
                {f.icon}
              </div>
              <h3 className="font-semibold mb-1">{f.title}</h3>
              <p className="text-[13px] text-muted leading-snug">{f.desc}</p>
            </Link>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-3">
        {[
          { icon: Images, title: "Gallery", desc: "Search, tag, favorite, collections", href: "/gallery" },
          { icon: Activity, title: "Monitoring", desc: "GPU, p50/p95, cache hit-rate", href: "/monitor" },
          { icon: Sparkles, title: "API & SDK", desc: "35+ endpoints, Python client", href: "/docs" },
        ].map((item) => (
          <Link
            key={item.title}
            href={item.href}
            className="glass glass-hover rounded-2xl p-5 flex items-start gap-3"
          >
            <div className="size-9 rounded-lg bg-white/5 flex items-center justify-center shrink-0">
              <item.icon className="size-4 text-muted" />
            </div>
            <div>
              <h3 className="font-medium text-[14px] mb-0.5">{item.title}</h3>
              <p className="text-[13px] text-muted">{item.desc}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}