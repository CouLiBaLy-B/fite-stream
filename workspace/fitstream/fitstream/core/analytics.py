"""
FitStream Analytics Engine
Insights and statistics on content generation patterns.

Tracks:
  - Most popular prompts / styles / garment categories
  - Generation trends (hourly, daily)
  - Average generation times by type and preset
  - Quality score distribution
  - User engagement patterns (if auth enabled)

Usage:
    analytics = AnalyticsEngine()
    analytics.record_generation(type="animate", style="cinematic", time=42.5, ...)
    report = analytics.get_report()
"""

import time
from collections import defaultdict, Counter
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GenerationEvent:
    """A recorded generation event."""
    timestamp: float
    type: str                # animate, story, tryon, compose, style
    style: str = ""
    preset: str = ""
    prompt_length: int = 0
    generation_time: float = 0.0
    num_frames: int = 0
    success: bool = True
    garment_category: str = ""
    seed: int = 0


class AnalyticsEngine:
    """
    In-memory analytics engine for generation insights.
    
    Not a replacement for a proper analytics service (Mixpanel, Amplitude),
    but useful for self-hosted deployments and monitoring.
    """
    
    def __init__(self, max_events: int = 10000) -> None:
        self._events: List[GenerationEvent] = []
        self._max_events = max_events
        self._start_time = time.time()
    
    def record(
        self,
        type: str,
        style: str = "",
        preset: str = "",
        prompt: str = "",
        generation_time: float = 0.0,
        num_frames: int = 0,
        success: bool = True,
        garment_category: str = "",
        seed: int = 0,
    ):
        """Record a generation event."""
        event = GenerationEvent(
            timestamp=time.time(),
            type=type,
            style=style,
            preset=preset,
            prompt_length=len(prompt),
            generation_time=generation_time,
            num_frames=num_frames,
            success=success,
            garment_category=garment_category,
            seed=seed,
        )
        
        self._events.append(event)
        
        # Evict old events
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
    
    def get_report(self, hours: float = 24) -> Dict[str, Any]:
        cutoff = time.time() - (hours * 3600)
        recent = [e for e in self._events if e.timestamp >= cutoff]
        
        if not recent:
            return {
                "period_hours": hours,
                "total_generations": 0,
                "message": "No data in the selected period",
            }
        
        successful = [e for e in recent if e.success]
        failed = [e for e in recent if not e.success]
        
        # Aggregations
        types = Counter(e.type for e in recent)
        styles = Counter(e.style for e in recent if e.style)
        presets = Counter(e.preset for e in recent if e.preset)
        garments = Counter(e.garment_category for e in recent if e.garment_category)
        
        # Time analysis
        gen_times = [e.generation_time for e in successful if e.generation_time > 0]
        avg_time = sum(gen_times) / len(gen_times) if gen_times else 0
        gen_times_sorted = sorted(gen_times)
        p50_time = gen_times_sorted[len(gen_times_sorted) // 2] if gen_times_sorted else 0
        p95_time = gen_times_sorted[int(len(gen_times_sorted) * 0.95)] if len(gen_times_sorted) > 1 else 0
        
        # Hourly distribution
        hourly: Dict[str, int] = defaultdict(int)
        for e in recent:
            hour = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:00")
            hourly[hour] += 1
        
        # Average time by type
        time_by_type = defaultdict(list)
        for e in successful:
            if e.generation_time > 0:
                time_by_type[e.type].append(e.generation_time)
        avg_time_by_type = {
            t: sum(times) / len(times)
            for t, times in time_by_type.items()
        }
        
        # Prompt length analysis
        prompt_lengths = [e.prompt_length for e in recent if e.prompt_length > 0]
        avg_prompt_length = sum(prompt_lengths) / len(prompt_lengths) if prompt_lengths else 0
        
        return {
            "period_hours": hours,
            "total_generations": len(recent),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(recent) if recent else 0,
            
            "by_type": dict(types.most_common()),
            "by_style": dict(styles.most_common(10)),
            "by_preset": dict(presets.most_common()),
            "by_garment_category": dict(garments.most_common()),
            
            "generation_time": {
                "average": round(avg_time, 1),
                "p50": round(p50_time, 1),
                "p95": round(p95_time, 1),
                "min": round(min(gen_times) if gen_times else 0, 1),
                "max": round(max(gen_times) if gen_times else 0, 1),
            },
            "avg_time_by_type": {k: round(v, 1) for k, v in avg_time_by_type.items()},
            
            "prompt": {
                "average_length": round(avg_prompt_length),
                "total_prompts": len(prompt_lengths),
            },
            
            "hourly_distribution": dict(sorted(hourly.items())),
            
            "total_frames_generated": sum(e.num_frames for e in successful),
            "total_video_seconds": sum(e.num_frames / 16 for e in successful),
            "total_generation_time_minutes": sum(e.generation_time for e in successful) / 60,
        }
    
    def get_top_styles(self, limit: int = 5) -> List[dict]:
        """Generate a comprehensive analytics report."""
        styles = Counter(e.style for e in self._events if e.style)
        return [{"style": s, "count": c} for s, c in styles.most_common(limit)]
    
    def get_top_types(self, limit: int = 5) -> List[dict]:
        """Get the most popular styles."""
        types = Counter(e.type for e in self._events)
        return [{"type": t, "count": c} for t, c in types.most_common(limit)]
    
    @property
    def total_events(self) -> int:
        """Get the most popular generation types."""
        """Total events."""
        return len(self._events)


# Global instance
analytics = AnalyticsEngine()
