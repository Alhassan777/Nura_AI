import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "./calendar.css";
import Header from "@/components/Header";
import { Providers } from "./providers";
import { SafetyNet } from "@/components/SafetyNet";
import { DailyReflection } from "@/components/DailyReflection";
import axios from "axios";
import { cookies } from "next/headers";
import { ReactQueryClientProvider } from "@/components/ReactQueryClientProvider";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/components/ThemeProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Nura App - Call Dashboard",
  description: "View and manage your call history",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();

  const token = cookieStore.get("token")?.value;

  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;

  axios.defaults.baseURL = process.env.NEXT_PUBLIC_API_URL;

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ReactQueryClientProvider>
          <Providers>
            <ThemeProvider
              attribute="class"
              defaultTheme="system"
              enableSystem
              disableTransitionOnChange
            >
              <Header />
              <main>{children}</main>
              <SafetyNet />
              <DailyReflection />
              <Toaster richColors />
            </ThemeProvider>
          </Providers>
        </ReactQueryClientProvider>
      </body>
    </html>
  );
}
