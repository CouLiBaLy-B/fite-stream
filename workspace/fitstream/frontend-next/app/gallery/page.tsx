"use client";

import { useEffect, useState } from "react";
import { Search, Heart, Download, Trash2, Filter } from "lucide-react";
import { motion } from "framer-motion";

type Item = {
  id: string;
  type: string;
  prompt: string;
  created_at: string;
  video_url?: string;
  thumbnail?: string;
};

export default function GalleryPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/gallery?limit=48")
      .then(r => r.json())
      .then(d => {
        setItems(d.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filtered = items.filter(i => 
    !query || i.prompt?.toLowerCase().includes(query.toLowerCase()) || i.type.includes(query.toLowerCase())
  );

  return (
    <div className="max-w-[1400px] mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-[28px] font-bold tracking-tight">Gallery</h1>
          <p className="text-[14px] text-muted mt-0.5">{filtered.length} videos • Search and manage your generations</p>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        <div className="relative flex-1 max-w-[400px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by prompt, type, style..."
            className="w-full h-[40px] pl-9 pr-3 bg-white/[0.03] border border-white/10 rounded-xl text-[14px] focus:outline-none focus:border-purple/50"
          />
        </div>
        <button className="h-[40px] px-3 rounded-xl glass glass-hover flex items-center gap-1.5 text-[13px]">
          <Filter className="size-3.5" />
          Filter
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="aspect-[9/16] rounded-2xl bg-white/[0.03] animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center">
          <div className="text-[48px] mb-3 opacity-20">🖼️</div>
          <div className="font-medium mb-1">No videos yet</div>
          <div className="text-[14px] text-muted">Generate your first video in the Creator Studio</div>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {filtered.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02 }}
              className="group relative aspect-[9/16] rounded-2xl overflow-hidden bg-black border border-white/10"
            >
              <video
                src={`/api/v1/jobs/${item.id}/video`}
                className="w-full h-full object-cover"
                muted
                loop
                playsInline
                onMouseEnter={e => e.currentTarget.play()}
                onMouseLeave={e => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/0 to-black/40 opacity-0 group-hover:opacity-100 transition-opacity" />
              
              <div className="absolute top-2 left-2 right-2 flex justify-between">
                <span className="px-2 py-1 rounded-lg bg-black/70 backdrop-blur text-[10px] font-medium uppercase tracking-wide">
                  {item.type}
                </span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="size-7 rounded-lg bg-black/70 backdrop-blur flex items-center justify-center hover:bg-white/20">
                    <Heart className="size-3.5" />
                  </button>
                  <a 
                    href={`/api/v1/jobs/${item.id}/video`}
                    download
                    className="size-7 rounded-lg bg-black/70 backdrop-blur flex items-center justify-center hover:bg-white/20"
                  >
                    <Download className="size-3.5" />
                  </a>
                </div>
              </div>

              <div className="absolute bottom-0 left-0 right-0 p-3 translate-y-2 group-hover:translate-y-0 opacity-0 group-hover:opacity-100 transition-all">
                <div className="text-[12px] leading-snug line-clamp-2 text-white/90">{item.prompt}</div>
                <div className="text-[10px] text-white/50 mt-1">{new Date(item.created_at).toLocaleDateString()}</div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}