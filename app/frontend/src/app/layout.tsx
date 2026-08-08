import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider, SignIn } from '@clerk/nextjs'
import { auth } from '@clerk/nextjs/server'
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { CommandPalette } from "@/components/CommandPalette";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  themeColor: "#0ea5e9",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "MedQuest | Preparação USP",
  description: "A melhor plataforma de estudos para a Residência Médica da USP, com planejamento anual inteligente.",
  manifest: "/manifest.json",
  openGraph: {
    title: "MedQuest | Preparação USP",
    description: "A melhor plataforma de estudos para a Residência Médica da USP, com planejamento anual inteligente.",
    url: "https://medquest.com.br",
    siteName: "MedQuest",
    locale: "pt_BR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "MedQuest | Preparação USP",
    description: "A melhor plataforma de estudos para a Residência Médica da USP, com planejamento anual inteligente.",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "MedQuest",
  },
  formatDetection: {
    telephone: false,
  },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { userId } = await auth();

  return (
    <ClerkProvider>
      <html
        lang="pt-BR"
        className={`${inter.variable} h-full antialiased`}
        suppressHydrationWarning
      >
        <body className="min-h-full flex bg-background text-foreground overflow-hidden">
          {!userId ? (
            <div className="flex w-full h-full items-center justify-center p-8">
              <SignIn routing="hash" />
            </div>
          ) : (
            <>
              <Sidebar />
              <main className="flex-1 flex flex-col h-screen overflow-y-auto relative">
                <div className="flex-1 max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8">
                  {children}
                </div>
              </main>
              <CommandPalette />
            </>
          )}
        </body>
      </html>
    </ClerkProvider>
  );
}
