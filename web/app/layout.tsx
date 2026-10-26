import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KaamKitPro Finance | Project Financial Planning",
  description: "Build project projections, funding plans and investor-ready financial reports.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
