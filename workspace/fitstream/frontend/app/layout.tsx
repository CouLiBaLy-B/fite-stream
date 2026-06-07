import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "FitStream — AI Video Animation",
  description: "Turn photos into living stories with AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans`}>
        <Sidebar />
        <div className="lg:pl-[240px]">
          <header className="sticky top-0 z-30 h-[56px] border-b border-white/[0.06] bg-bg/80 backdrop-blur-xl">
            <div className="h-full flex items-center justify-between px-4 lg:px-6">
              <div className="flex items-center gap-3 lg:hidden">
                <div className="size-7 rounded-lg bg-gradient-to-br from-purple to-pink flex items-center justify-center">
                  <span className="text-[14px]">🎬</span>
                </div>
                <span className="font-semibold">FitStream</span>
              </div>
              <div className="flex items-center gap-2 ml-auto">
                <a 
                  href="/docs" 
                  target="_blank"
                  className="text-[13px] text-muted hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
                >
                  API Docs
                </a>
                <a 
                  href="https://github.com/CouLiBaLy-B/filestream"
                  target="_blank"
                  className="text-[13px] text-muted hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
                >
                  GitHub
                </a>
              </div>
            </div>
          </header>
          <main className="min-h-[calc(100vh-56px)]">
            {children}
          </main>
        </div>
        <Toaster theme="dark" position="bottom-right" richColors />
      </body>
    </html>
  );
}