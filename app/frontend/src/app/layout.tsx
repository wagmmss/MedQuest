import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider, SignIn } from '@clerk/nextjs';
import { auth } from '@clerk/nextjs/server';
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import TopNav from "@/components/TopNav";

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
        <head>
          <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
        </head>
        <body className="font-body-md text-body-md h-screen flex overflow-hidden bg-background text-on-background selection:bg-primary-fixed selection:text-on-primary-fixed">
          {!userId ? (
            <div className="flex w-full h-full items-center justify-center p-8">
              <SignIn routing="hash" />
            </div>
          ) : (
            <>
              <Sidebar />
              <div className="flex-1 flex flex-col w-full min-w-0 bg-background overflow-y-auto">
                <TopNav />
                <main className="flex-1 max-w-[1440px] mx-auto w-full p-gutter md:p-margin gap-stack-lg flex flex-col pb-24 md:pb-margin relative">
                  {children}
                </main>
              </div>
            </>
          )}
        </body>
      </html>
    </ClerkProvider>
  );
}
