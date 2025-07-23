import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";
import Link from "next/link";
import ThemeProviderWrapper from "@/theme/ThemeProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Receptionist Pro",
  description: "Premium AI-powered business phone management platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProviderWrapper>
          <Header />
          {children}
        </ThemeProviderWrapper>
      </body>
    </html>
  );
}

