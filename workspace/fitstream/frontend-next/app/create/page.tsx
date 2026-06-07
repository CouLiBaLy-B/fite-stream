"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, X, Play, Loader2, Check, AlertCircle,
  Image as ImageIcon, Sparkles, Wand2
} from "lucide-react";
import { cn, STYLES } from "@/lib/utils";
import { toast } from "sonner";

type Job = {
  id: string;
  type: string;
  status: string;
  prompt: string;
  progress: number;
  video?: string;
  error?: string;
  created: number;
};

const MODES = [
  { id: "animate", label: "Animate", icon: "📸", desc: "Photo → video" },
  { id: "story", label: "Story", icon: "📖", desc: "Multi-scene" },
  { id: "tryon", label: "Try-On", icon: "👗", desc: "Virtual fitting" },
  { id: "compose", label: "Compose", icon: "🎨", desc: "Multi-image" },
  { id: "style", label: "Style", icon: "🎭", desc: "Art transfer" },
  { id: "realtime", label: "Real-Time", icon: "⚡", desc: "Fast" },
];

function CreatePageInner() {
  const search = useSearchParams();
  const [mode, setMode] = useState(search.get("mode") || "animate");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [uploading, setUploading] = useState(false);
  
  // Form state
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [previews, setPreviews] = useState<Record<string, string>>({});
  const [prompt, setPrompt] = useState("");
  const [story, setStory] = useState("");
  const [style, setStyle] = useState("cinematic");
  const [preset, setPreset] = useState("standard");
  const [frames, setFrames] = useState(49);
  const [category, setCategory] = useState("auto");
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const m = search.get("mode");
    if (m && MODES.find(x => x.id === m)) setMode(m);
  }, [search]);

  // WebSocket for real-time updates
  useEffect(() => {
    const connectWS = () => {
      try {
        const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/jobs/all`);
        ws.onmessage = (e) => {
          const data = JSON.parse(e.data);
          setJobs(prev => prev.map(j => 
            j.id === data.job_id 
              ? { ...j, status: data.status, progress: data.progress || j.progress }
              : j
          ));
        };
        wsRef.current = ws;
      } catch {}
    };
    connectWS();
    return () => wsRef.current?.close();
  }, []);

  const handleFile = (key: string, file: File) => {
    setFiles(f => ({ ...f, [key]: file }));
    const url = URL.createObjectURL(file);
    setPreviews(p => ({ ...p, [key]: url }));
  };

  const dropZone = (key: string, label: string, multiple = false) => (
    <div
      onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("border-purple/50"); }}
      onDragLeave={(e) => e.currentTarget.classList.remove("border-purple/50")}
      onDrop={(e) => {
        e.preventDefault();
        e.currentTarget.classList.remove("border-purple/50");
        const f = e.dataTransfer.files[0];
        if (f) handleFile(key, f);
      }}
      className="relative group"
    >
      <input
        type="file"
        accept="image/*"
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        onChange={(e) => e.target.files?.[0] && handleFile(key, e.target.files[0])}
      />
      <div className={cn(
        "border-2 border-dashed border-white/10 rounded-2xl p-8 text-center transition-all",
        "group-hover:border-white/20 group-hover:bg-white/[0.02]",
        previews[key] && "border-emerald/50 bg-emerald/5"
      )}>
        {previews[key] ? (
          <div className="relative">
            <img src={previews[key]} className="max-h-[180px] mx-auto rounded-xl" alt="" />
            <button
              onClick={(e) => { e.preventDefault(); setFiles(f => ({ ...f, [key]: null })); setPreviews(p => ({ ...p, [key]: "" })); }}
              className="absolute -top-2 -right-2 size-6 rounded-full bg-red-500 flex items-center justify-center"
            >
              <X className="size-3" />
            </button>
          </div>
        ) : (
          <>
            <Upload className="size-8 mx-auto mb-3 text-muted" />
            <div className="text-[14px] font-medium">{label}</div>
            <div className="text-[12px] text-muted mt-1">Drop image or click • JPG/PNG/WebP</div>
          </>
        )}
      </div>
    </div>
  );

  const submit = async () => {
    setUploading(true);
    const form = new FormData();
    let endpoint = "";

    try {
      if (mode === "animate") {
        if (!files.main) throw new Error("Select an image");
        form.append("image", files.main);
        form.append("prompt", prompt || "A person walking naturally");
        form.append("style", style);
        form.append("preset", preset);
        form.append("num_frames", String(frames));
        endpoint = "/api/v1/animate";
      } else if (mode === "story") {
        if (!files.main) throw new Error("Select an image");
        form.append("image", files.main);
        form.append("story", story || prompt);
        form.append("style", style);
        form.append("preset", preset);
        endpoint = "/api/v1/story";
      } else if (mode === "tryon") {
        if (!files.person || !files.garment) throw new Error("Select person & garment");
        form.append("person_image", files.person);
        form.append("garment_image", files.garment);
        form.append("category", category);
        form.append("style", style);
        endpoint = "/api/v1/tryon";
      } else if (mode === "compose") {
        const imgs = [files.img1, files.img2, files.img3, files.img4].filter(Boolean);
        if (imgs.length < 2) throw new Error("Select at least 2 images");
        imgs.forEach(f => form.append("images", f!));
        form.append("prompt", prompt);
        form.append("style", style);
        endpoint = "/api/v1/compose";
      } else if (mode === "style") {
        if (!files.main) throw new Error("Select an image");
        form.append("image", files.main);
        form.append("prompt", prompt);
        form.append("style", style);
        endpoint = "/api/v1/style";
      } else if (mode === "realtime") {
        if (!files.main) throw new Error("Select an image");
        form.append("image", files.main);
        form.append("prompt", prompt);
        endpoint = "/api/v1/realtime/generate";
      }

      const res = await fetch(endpoint, { method: "POST", body: form });
      const data = await res.json();
      
      if (data.job_id) {
        const job: Job = {
          id: data.job_id,
          type: mode,
          status: "queued",
          prompt: prompt || story || "Generation",
          progress: 0,
          created: Date.now(),
        };
        setJobs(j => [job, ...j].slice(0, 20));
        toast.success("Job queued", { description: `ID: ${data.job_id.slice(0, 8)}` });
        pollJob(data.job_id);
      } else {
        throw new Error(data.detail || "Failed");
      }
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setUploading(false);
    }
  };

  const pollJob = async (id: string) => {
    const check = async () => {
      try {
        const r = await fetch(`/api/v1/jobs/${id}`);
        const d = await r.json();
        setJobs(prev => prev.map(j => j.id === id ? {
          ...j,
          status: d.status,
          progress: d.progress || 0,
          video: d.status === "completed" ? `/api/v1/jobs/${id}/video` : undefined,
          error: d.error,
        } : j));
        if (d.status !== "completed" && d.status !== "failed") {
          setTimeout(check, 2000);
        } else if (d.status === "completed") {
          toast.success("Video ready!");
        }
      } catch {}
    };
    check();
  };

  return (
    <div className="max-w-[1400px] mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[28px] font-bold tracking-tight">Creator Studio</h1>
          <p className="text-[14px] text-muted mt-0.5">Build AI videos from photos</p>
        </div>
      </div>

      {/* Mode Tabs */}
      <div className="flex gap-1.5 mb-6 overflow-x-auto pb-1">
        {MODES.map(m => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={cn(
              "flex items-center gap-2 px-3.5 py-2 rounded-xl text-[13px] font-medium whitespace-nowrap transition-all border",
              mode === m.id
                ? "bg-white text-black border-white"
                : "bg-white/[0.03] border-white/10 text-muted hover:bg-white/[0.06] hover:text-white"
            )}
          >
            <span className="text-[16px]">{m.icon}</span>
            <span>{m.label}</span>
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-[1fr_360px] gap-6 items-start">
        {/* Main */}
        <div className="glass rounded-[20px] p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {mode === "animate" && (
                <div className="space-y-5">
                  {dropZone("main", "Drop person photo")}
                  <div>
                    <label className="text-[12px] font-medium text-muted uppercase tracking-wide mb-2 block">Prompt</label>
                    <textarea
                      value={prompt}
                      onChange={e => setPrompt(e.target.value)}
                      placeholder="The person walks through a sunlit garden, stops to smell a rose..."
                      className="w-full h-[90px] bg-black/40 border border-white/10 rounded-xl px-3.5 py-2.5 text-[14px] resize-none focus:outline-none focus:border-purple/50 focus:ring-1 focus:ring-purple/50"
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-[11px] text-muted mb-1.5 block">Style</label>
                      <select value={style} onChange={e => setStyle(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[13px]">
                        {STYLES.map(s => <option key={s.id} value={s.id}>{s.icon} {s.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] text-muted mb-1.5 block">Quality</label>
                      <select value={preset} onChange={e => setPreset(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[13px]">
                        <option value="draft">Draft</option>
                        <option value="standard">Standard</option>
                        <option value="high">High</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] text-muted mb-1.5 block">Frames</label>
                      <input type="number" value={frames} onChange={e => setFrames(+e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[13px]" />
                    </div>
                  </div>
                </div>
              )}

              {mode === "story" && (
                <div className="space-y-5">
                  {dropZone("main", "Drop person photo")}
                  <div>
                    <label className="text-[12px] font-medium text-muted uppercase tracking-wide mb-2 block">Story</label>
                    <textarea
                      value={story}
                      onChange={e => setStory(e.target.value)}
                      placeholder="Marie walks through Paris. She enters a bakery. She buys a croissant. She watches the sunset."
                      className="w-full h-[110px] bg-black/40 border border-white/10 rounded-xl px-3.5 py-2.5 text-[14px] resize-none focus:outline-none focus:border-purple/50"
                    />
                  </div>
                </div>
              )}

              {mode === "tryon" && (
                <div className="space-y-5">
                  <div className="grid md:grid-cols-2 gap-4">
                    {dropZone("person", "Person photo")}
                    {dropZone("garment", "Garment photo")}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-muted mb-1.5 block">Category</label>
                      <select value={category} onChange={e => setCategory(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[13px]">
                        <option value="auto">Auto-detect</option>
                        <option value="tops">Tops</option>
                        <option value="dresses">Dresses</option>
                        <option value="outerwear">Outerwear</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[11px] text-muted mb-1.5 block">Style</label>
                      <select value={style} onChange={e => setStyle(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[13px]">
                        {STYLES.slice(0,6).map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {mode === "compose" && (
                <div className="space-y-5">
                  <div className="grid grid-cols-2 gap-3">
                    {["img1","img2","img3","img4"].map((k,i) => (
                      <div key={k}>{dropZone(k, `@Image ${i+1}`)}</div>
                    ))}
                  </div>
                  <textarea
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    placeholder="The woman (@Image 1) wearing the dress (@Image 2) at the café (@Image 3)..."
                    className="w-full h-[80px] bg-black/40 border border-white/10 rounded-xl px-3.5 py-2.5 text-[14px] resize-none"
                  />
                </div>
              )}

              {mode === "style" && (
                <div className="space-y-5">
                  {dropZone("main", "Drop image to restyle")}
                  <div>
                    <label className="text-[12px] font-medium text-muted uppercase tracking-wide mb-2.5 block">Style</label>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                      {STYLES.map(s => (
                        <button
                          key={s.id}
                          onClick={() => setStyle(s.id)}
                          className={cn(
                            "p-3 rounded-xl border text-[12px] font-medium transition-all",
                            style === s.id
                              ? "bg-purple/20 border-purple/50 text-white"
                              : "bg-white/[0.02] border-white/10 hover:bg-white/[0.05] text-muted"
                          )}
                        >
                          <div className="text-[20px] mb-1">{s.icon}</div>
                          {s.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <textarea
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    placeholder="Optional prompt to guide style..."
                    className="w-full h-[70px] bg-black/40 border border-white/10 rounded-xl px-3.5 py-2.5 text-[14px] resize-none"
                  />
                </div>
              )}

              {mode === "realtime" && (
                <div className="space-y-5">
                  {dropZone("main", "Drop photo for fast generation")}
                  <textarea
                    value={prompt}
                    onChange={e => setPrompt(e.target.value)}
                    placeholder="Quick action description..."
                    className="w-full h-[80px] bg-black/40 border border-white/10 rounded-xl px-3.5 py-2.5 text-[14px] resize-none"
                  />
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[12px] text-amber-200">
                    ⚡ Real-time mode uses LTX-Video for ~2s generation. Quality lower than standard pipelines.
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          <button
            onClick={submit}
            disabled={uploading}
            className="w-full mt-6 h-[44px] rounded-xl bg-white text-black font-medium text-[14px] flex items-center justify-center gap-2 hover:bg-white/90 disabled:opacity-50 transition-all"
          >
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            {uploading ? "Generating..." : `Generate ${MODES.find(m => m.id === mode)?.label}`}
          </button>
        </div>

        {/* Sidebar - Jobs */}
        <div className="space-y-3">
          <div className="glass rounded-[20px] p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-[14px]">Recent Jobs</h3>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-white/10">{jobs.length}</span>
            </div>
            <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1 -mr-1">
              {jobs.length === 0 ? (
                <div className="text-center py-12 text-muted">
                  <Wand2 className="size-8 mx-auto mb-2 opacity-30" />
                  <div className="text-[13px]">No jobs yet</div>
                </div>
              ) : jobs.map(job => (
                <div key={job.id} className="group relative p-3 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-colors">
                  <div className="flex items-start gap-2.5">
                    <div className={cn(
                      "size-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5",
                      job.status === "completed" ? "bg-emerald/20 text-emerald" :
                      job.status === "failed" ? "bg-red-500/20 text-red-400" :
                      "bg-amber-500/20 text-amber-400"
                    )}>
                      {job.status === "completed" ? <Check className="size-3.5" /> :
                       job.status === "failed" ? <AlertCircle className="size-3.5" /> :
                       <Loader2 className="size-3.5 animate-spin" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="text-[11px] font-medium uppercase tracking-wide text-muted">{job.type}</span>
                        <span className="text-[10px] text-muted/60">•</span>
                        <span className="text-[10px] text-muted/60 font-mono">{job.id.slice(0,6)}</span>
                      </div>
                      <div className="text-[12px] leading-snug line-clamp-2 text-white/80">{job.prompt}</div>
                      {job.status === "processing" || job.status === "queued" ? (
                        <div className="mt-2 h-1 rounded-full bg-white/10 overflow-hidden">
                          <div 
                            className="h-full bg-purple transition-all duration-500"
                            style={{ width: `${Math.max(5, job.progress * 100)}%` }}
                          />
                        </div>
                      ) : null}
                      {job.video && (
                        <video src={job.video} controls className="w-full mt-2.5 rounded-lg bg-black" />
                      )}
                      {job.error && (
                        <div className="mt-1.5 text-[11px] text-red-400">{job.error}</div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-[20px] p-4">
            <h3 className="font-semibold text-[13px] mb-3">Templates</h3>
            <div className="space-y-1.5">
              {[
                "Walking through garden at golden hour",
                "Confident runway walk, fashion show",
                "Dancing in the rain, cinematic",
                "Sitting at Paris café, people watching",
              ].map(t => (
                <button
                  key={t}
                  onClick={() => setPrompt(t)}
                  className="w-full text-left px-2.5 py-1.5 rounded-lg text-[12px] text-muted hover:text-white hover:bg-white/5 transition-colors"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense>
      <CreatePageInner />
    </Suspense>
  );
}