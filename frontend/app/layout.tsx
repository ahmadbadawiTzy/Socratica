import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/AuthContext";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "Socratica — Socratic Teaching Assistant",
  description: "Academic AI learning grounded in university course materials.",
};

const bootScript = `
(function () {
  try {
    var d = localStorage.getItem("socratica_theme") === "dark";
    if (!localStorage.getItem("socratica_theme")) {
      d = window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    if (d) document.documentElement.classList.add("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: bootScript }} />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
