import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { AppProviders } from "@/components/providers/app-providers";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: {
    default: "Readout — Hear what matters in your business data",
    template: "%s · Readout",
  },
  description: "Turn a CSV and a plain-English question into a visual, evidence-backed answer. Find insights, scan anomalies, and inspect the reasoning behind every result.",
  openGraph: {
    title: "Readout — Analytics that answers back",
    description: "Ask your business data a question. Get a visual answer with the evidence attached.",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={geist.variable}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
