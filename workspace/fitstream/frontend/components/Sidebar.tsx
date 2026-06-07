"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  Sparkles, 
  Images, 
  Activity,
  Film,
} from "lucide-react";
import { useEffect, useState } from "react";
import { CommandPalette } from "./CommandPalette";

const nav = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/create", label: "Create", icon: Sparkles },
  { href: "/gallery", label: "Gallery", icon: Images },
  { href: "/monitor", label: "Monitor", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    fetch("/health").then(r => r.json()).then(setHealth).catch(() => {});
    const id = setInterval(() => {
      fetch("/health").then(r => r.json()).then(setHealth).catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <aside className="fixed left-0 top-0 h-screen w-[240px] border-r border-white/[0.06] bg-panel/80 backdrop-blur-xl z-40 hidden lg:flex flex-col">
      <div className="h-[56px] flex items-center px-5 border-b border-white/[0.06]">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="size-8 rounded-xl bg-gradient-to-br from-purple to-pink flex items-center justify-center shadow-glow">
            <Film className="size-4 text-white" />
          </div>
          <span className="font-semibold tracking-tight">FitStream</span>
        </Link>
      </div>

      <div className="p-3 flex-1 overflow-y-auto">
        <div className="mb-4">
          <CommandPalette />
        </div>

        <nav className="space-y-1">
          {nav.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-[14px] transition-all",
                  active 
                    ? "bg-white/[0.08] text-white" 
                    : "text-muted hover:text-white hover:bg-white/[0.04]"
                )}
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-8">
          <div className="px-3 mb-2 text-[11px] font-medium uppercase tracking-wider text-muted/60">
            Pipelines
          </div>
          <div className="space-y-1">
            {[
              { id: "animate", label: "Animate", icon: "📸" },
              { id: "story", label: "Story", icon: "📖" },
              { id: "tryon", label: "Try-On", icon: "👗" },
              { id: "compose", label: "Compose", icon: "🎨" },
            ].map(p => (
              <Link
                key={p.id}
                href={`/create?mode=${p.id}`}
                className="flex items-center gap-3 px-3 py-1.5 rounded-lg text-[13px] text-muted hover:text-white hover:bg-white/[0.03] transition-colors"
              >
                <span className="text-[15px] w-4 text-center">{p.icon}</span>
                {p.label}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="p-3 border-t border-white/[0.06]">
        <div className="glass rounded-xl p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <div className={cn(
              "size-2 rounded-full",
              health?.gpu?.available ? "bg-emerald shadow-[0_0_8px_rgba(6,214,160,0.5)]" : "bg-red-500"
            )} />
            <span className="text-[12px] font-medium">
              {health?.gpu?.available ? health.gpu.gpu_name || "GPU Ready" : "No GPU"}
            </span>
          </div>
          <div className="text-[11px] text-muted">
            {health?.gpu?.available 
              ? `${health.gpu.free_gb}GB free • ${health?.active_jobs || 0} jobs`
              : "API offline"}
          </div>
        </div>
      </div>
    </aside>
  );
}