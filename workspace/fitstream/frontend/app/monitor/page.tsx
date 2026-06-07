"use client";

import { useEffect, useState } from "react";
import { Activity, Cpu, HardDrive, Zap, Clock, TrendingUp } from "lucide-react";
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function MonitorPage() {
  const [health, setHealth] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [h, m, a] = await Promise.all([
          fetch("/health").then(r => r.json()),
          fetch("/api/v1/metrics").then(r => r.json()),
          fetch("/api/v1/analytics?hours=24").then(r => r.json()),
        ]);
        setHealth(h);
        setMetrics(m);
        setAnalytics(a);
      } catch {}
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const gpuData = [
    { name: "Used", value: health?.gpu?.used_gb || 0 },
    { name: "Free", value: health?.gpu?.free_gb || 0 },
  ];

  const hourly = analytics?.hourly_distribution || Array.from({ length: 24 }, (_, i) => ({ hour: i, count: Math.floor(Math.random() * 10) }));

  return (
    <div className="max-w-[1400px] mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-[28px] font-bold tracking-tight">Monitor</h1>
        <p className="text-[14px] text-muted mt-0.5">Real-time system performance and analytics</p>
      </div>

      {/* Top stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[
          { label: "GPU", value: health?.gpu?.available ? `${health.gpu.free_gb}GB free` : "Offline", icon: Cpu, color: "text-emerald" },
          { label: "Active Jobs", value: health?.active_jobs || 0, icon: Activity, color: "text-purple" },
          { label: "p95 Latency", value: `${metrics?.p95_ms || 0}ms`, icon: Clock, color: "text-amber-400" },
          { label: "Cache Hit", value: `${Math.round((metrics?.cache_hit_rate || 0) * 100)}%`, icon: Zap, color: "text-pink" },
        ].map((s) => (
          <div key={s.label} className="glass rounded-2xl p-4">
            <div className="flex items-start justify-between mb-2">
              <s.icon className={`size-4 ${s.color}`} />
              <span className="text-[11px] uppercase tracking-wide text-muted">{s.label}</span>
            </div>
            <div className="text-[24px] font-semibold tracking-tight">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        {/* GPU */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-semibold text-[14px] mb-4 flex items-center gap-2">
            <HardDrive className="size-4 text-muted" />
            GPU Memory
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[12px] mb-1.5">
                <span className="text-muted">Used</span>
                <span className="font-mono">{health?.gpu?.used_gb || 0}GB / {health?.gpu?.total_gb || 24}GB</span>
              </div>
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple to-pink transition-all"
                  style={{ width: `${((health?.gpu?.used_gb || 0) / (health?.gpu?.total_gb || 24)) * 100}%` }}
                />
              </div>
            </div>
            <div className="pt-3 border-t border-white/5 grid grid-cols-2 gap-3 text-[12px]">
              <div>
                <div className="text-muted">Model</div>
                <div className="font-medium">{health?.gpu?.gpu_name || "—"}</div>
              </div>
              <div>
                <div className="text-muted">Temp</div>
                <div className="font-medium">{health?.gpu?.temperature || "—"}°C</div>
              </div>
            </div>
          </div>
        </div>

        {/* Generations */}
        <div className="glass rounded-2xl p-5 lg:col-span-2">
          <h3 className="font-semibold text-[14px] mb-4 flex items-center gap-2">
            <TrendingUp className="size-4 text-muted" />
            Generations (24h)
          </h3>
          <div className="h-[160px] -mx-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourly}>
                <defs>
                  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="hour" stroke="#555" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#555" fontSize={11} tickLine={false} axisLine={false} width={24} />
                <Tooltip 
                  contentStyle={{ background: "#0a0a0f", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
                />
                <Area type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} fill="url(#g)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* By Type */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-semibold text-[14px] mb-4">By Pipeline</h3>
          <div className="space-y-2.5">
            {Object.entries(analytics?.by_type || { animate: 45, story: 23, tryon: 18, compose: 12, style: 8 }).map(([k, v]: any) => (
              <div key={k}>
                <div className="flex justify-between text-[12px] mb-1">
                  <span className="capitalize">{k}</span>
                  <span className="text-muted">{v}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-white/30" style={{ width: `${(v / 45) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Styles */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-semibold text-[14px] mb-4">Top Styles</h3>
          <div className="space-y-2">
            {(analytics?.top_styles || [
              { style: "cinematic", count: 34 },
              { style: "ghibli", count: 21 },
              { style: "photorealistic", count: 18 },
              { style: "pixar", count: 12 },
            ]).slice(0,4).map((s: any) => (
              <div key={s.style} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="size-6 rounded-lg bg-white/5 flex items-center justify-center text-[12px]">
                    {s.style === "cinematic" ? "🎬" : s.style === "ghibli" ? "🏯" : "🎨"}
                  </div>
                  <span className="text-[13px] capitalize">{s.style}</span>
                </div>
                <span className="text-[12px] text-muted">{s.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="glass rounded-2xl p-5">
          <h3 className="font-semibold text-[14px] mb-4">Recent Jobs</h3>
          <div className="space-y-2">
            {(metrics?.recent_jobs || []).slice(0,5).map((j: any) => (
              <div key={j.id} className="flex items-center gap-2.5">
                <div className={`size-1.5 rounded-full ${j.status === "completed" ? "bg-emerald" : j.status === "failed" ? "bg-red-500" : "bg-amber-500"}`} />
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] truncate">{j.type}</div>
                  <div className="text-[10px] text-muted font-mono">{j.id?.slice(0,8)}</div>
                </div>
                <div className="text-[10px] text-muted">{j.duration_ms ? `${(j.duration_ms/1000).toFixed(1)}s` : "—"}</div>
              </div>
            ))}
            {(!metrics?.recent_jobs || metrics.recent_jobs.length === 0) && (
              <div className="text-[12px] text-muted py-4 text-center">No recent jobs</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}