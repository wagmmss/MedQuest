import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import { ClerkProvider, SignIn } from '@clerk/nextjs';
import { ptBR } from '@clerk/localizations';
import { auth } from '@clerk/nextjs/server';
import { cookies } from 'next/headers';
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import TopNav from "@/components/TopNav";
import { Toaster } from "react-hot-toast";
import { CommandPalette } from "@/components/CommandPalette";
import { DemoButton } from "@/components/DemoButton";
import { DemoBanner } from "@/components/DemoBanner";
import { SyncProvider } from "@/components/SyncProvider";
import { OnboardingTour } from "@/components/OnboardingTour";
import { WebVitals } from "@/components/WebVitals";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  themeColor: "#0ea5e9",
  width: "device-width",
  initialScale: 1,
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
  const cookieStore = await cookies();
  const isDemoMode = cookieStore.get("medquest_demo")?.value === "1";

  return (
    <ClerkProvider localization={ptBR}>
      <html
        lang="pt-BR"
        className={`${geist.variable} font-sans h-full antialiased`}
        suppressHydrationWarning
      >
        <head>
          {/* Local Material Symbols injected via globals.css or layout import */}
          <script
            dangerouslySetInnerHTML={{
              __html: `
                try {
                  if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    document.documentElement.classList.add('dark')
                  } else {
                    document.documentElement.classList.remove('dark')
                  }
                } catch (_) {}
              `
            }}
          />
        </head>
        <body className="h-screen flex overflow-hidden bg-background text-on-background selection:bg-primary/20 selection:text-primary">
          <WebVitals />
          <a href="#conteudo-principal" className="skip-link">Pular para o conteúdo principal</a>
          {!userId && !isDemoMode ? (
            <div className="flex w-full h-full items-start justify-center p-8 bg-background relative overflow-y-auto">
              <div className="absolute inset-0 bg-primary/5" style={{ backgroundImage: "radial-gradient(circle, var(--primary) 1px, transparent 1px)", backgroundSize: "32px 32px", opacity: 0.2 }} />
              <div className="relative z-10 flex flex-col items-center max-w-md w-full bg-card p-8 md:p-12 rounded-2xl shadow-xl border border-border">
                <div className="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                  <span className="material-symbols-outlined text-4xl" data-icon="stethoscope">stethoscope</span>
                </div>
                <h1 className="text-2xl font-bold text-center mb-2">Bem-vindo ao MedQuest</h1>
                <p className="text-muted-foreground text-center mb-8 text-sm">Faça login para salvar seu progresso diário ou experimente sem compromisso.</p>
                <div className="w-full flex justify-center border-b border-border pb-8">
                  <SignIn routing="hash" />
                </div>
                <DemoButton />
              </div>
            </div>
          ) : (
            <div className="flex flex-col w-full h-full">
              <DemoBanner />
              <div className="flex flex-1 min-h-0 w-full overflow-hidden">
                <Sidebar />
                <div className="flex-1 flex flex-col w-full min-w-0 bg-background overflow-y-auto">
                  <TopNav />
                  <main id="conteudo-principal" tabIndex={-1} className="flex-1 max-w-[1440px] mx-auto w-full p-4 sm:p-gutter md:p-margin gap-stack-lg flex flex-col pb-24 md:pb-margin relative focus:outline-none">
                    {children}
                  </main>
                </div>
                <CommandPalette />
              </div>
              <OnboardingTour />
            </div>
          )}
          <SyncProvider />
          <Toaster position="top-right" />
        </body>
      </html>
    </ClerkProvider>
  );
}
