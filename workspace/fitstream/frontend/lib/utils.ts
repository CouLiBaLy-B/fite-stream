import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API = "";

export const STYLES = [
  { id: "cinematic", label: "Cinematic", icon: "🎬" },
  { id: "ghibli", label: "Ghibli", icon: "🏯" },
  { id: "pixar", label: "Pixar", icon: "🧊" },
  { id: "comic", label: "Comic", icon: "💥" },
  { id: "noir", label: "Noir", icon: "🌑" },
  { id: "cyberpunk", label: "Cyberpunk", icon: "🌆" },
  { id: "ukiyo-e", label: "Ukiyo-e", icon: "🎌" },
  { id: "impressionist", label: "Impressionist", icon: "🌸" },
  { id: "watercolor", label: "Watercolor", icon: "🎨" },
  { id: "oil-painting", label: "Oil", icon: "🖼️" },
  { id: "photorealistic", label: "Photo", icon: "📸" },
  { id: "vintage", label: "Vintage", icon: "📼" },
];

export async function fetchHealth() {
  try {
    const r = await fetch("/health", { cache: "no-store" });
    return await r.json();
  } catch {
    return null;
  }
}