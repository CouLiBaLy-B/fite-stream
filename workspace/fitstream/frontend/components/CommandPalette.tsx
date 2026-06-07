"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { 
  Sparkles, Images, Activity, Home, 
  Sun, Moon, Monitor, Search
} from "lucide-react";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light" | "system">("dark");
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("theme") as any;
    if (saved) setTheme(saved);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "light") {
      root.classList.remove("dark");
      root.classList.add("light");
    } else {
      root.classList.add("dark");
      root.classList.remove("light");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const runCommand = (fn: () => void) => {
    setOpen(false);
    fn();
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10 text-[13px] text-muted hover:bg-white/[0.06] transition-colors"
      >
        <Search className="size-3.5" />
        <span className="hidden sm:inline">Search</span>
        <kbd className="ml-1 hidden sm:inline-flex h-5 items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px]">
          ⌘K
        </kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm">
          <div className="fixed left-1/2 top-[20%] w-full max-w-[640px] -translate-x-1/2">
            <Command className="glass rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
              <div className="flex items-center border-b border-white/10 px-4">
                <Search className="size-4 text-muted mr-3" />
                <Command.Input
                  autoFocus
                  placeholder="Search pages, pipelines, actions..."
                  className="flex-1 h-12 bg-transparent outline-none text-[14px] placeholder:text-muted"
                />
              </div>
              
              <Command.List className="p-2 max-h-[380px] overflow-y-auto">
                <Command.Empty className="py-8 text-center text-[13px] text-muted">
                  No results found.
                </Command.Empty>

                <Command.Group heading="Pages" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-muted">
                  {[
                    { icon: Home, label: "Home", href: "/" },
                    { icon: Sparkles, label: "Create", href: "/create" },
                    { icon: Images, label: "Gallery", href: "/gallery" },
                    { icon: Activity, label: "Monitor", href: "/monitor" },
                  ].map((item) => (
                    <Command.Item
                      key={item.href}
                      onSelect={() => runCommand(() => router.push(item.href))}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] cursor-pointer aria-selected:bg-white/10"
                    >
                      <item.icon className="size-4 text-muted" />
                      {item.label}
                    </Command.Item>
                  ))}
                </Command.Group>

                <Command.Group heading="Pipelines">
                  {[
                    { icon: "📸", label: "Animate", mode: "animate" },
                    { icon: "📖", label: "Story", mode: "story" },
                    { icon: "👗", label: "Try-On", mode: "tryon" },
                    { icon: "🎨", label: "Compose", mode: "compose" },
                    { icon: "🎭", label: "Style Transfer", mode: "style" },
                    { icon: "⚡", label: "Real-Time", mode: "realtime" },
                  ].map((p) => (
                    <Command.Item
                      key={p.mode}
                      onSelect={() => runCommand(() => router.push(`/create?mode=${p.mode}`))}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] cursor-pointer aria-selected:bg-white/10"
                    >
                      <span className="text-[16px] w-4 text-center">{p.icon}</span>
                      {p.label}
                      <span className="ml-auto text-[11px] text-muted">Create</span>
                    </Command.Item>
                  ))}
                </Command.Group>

                <Command.Group heading="Theme">
                  {[
                    { icon: Moon, label: "Dark", value: "dark" },
                    { icon: Sun, label: "Light", value: "light" },
                    { icon: Monitor, label: "System", value: "system" },
                  ].map((t) => (
                    <Command.Item
                      key={t.value}
                      onSelect={() => runCommand(() => setTheme(t.value as any))}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] cursor-pointer aria-selected:bg-white/10"
                    >
                      <t.icon className="size-4 text-muted" />
                      {t.label}
                      {theme === t.value && (
                        <span className="ml-auto text-[11px] text-purple">Active</span>
                      )}
                    </Command.Item>
                  ))}
                </Command.Group>
              </Command.List>

              <div className="border-t border-white/10 px-3 py-2 flex items-center justify-between">
                <div className="text-[11px] text-muted">Navigate ↑↓ • Select ↵ • Close ESC</div>
                <button
                  onClick={() => setOpen(false)}
                  className="text-[11px] px-2 py-1 rounded bg-white/5 hover:bg-white/10"
                >
                  Close
                </button>
              </div>
            </Command>
          </div>
        </div>
      )}
    </>
  );
}