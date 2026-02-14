export const dynamic = 'force-dynamic';
import "./globals.css";
import Header from "@/components/Header";
import ThemeProviderWrapper from "@/theme/ThemeProvider";
import axios from 'axios';

if (typeof window !== 'undefined') {
  axios.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = 'Bearer ' + token;
    }
    return config;
  });
}

export const metadata = {
  title: "AI Receptionist Pro",
  description: "Premium AI-powered business phone management platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ThemeProviderWrapper>
          <Header />
          <main>
            {children}
          </main>
        </ThemeProviderWrapper>
      </body>
    </html>
  );
}
