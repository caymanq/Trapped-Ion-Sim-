import type { Metadata } from "next";
import { Press_Start_2P, VT323 } from "next/font/google";
import "./styles.css";

const pixel = Press_Start_2P({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-pixel"
});

const terminal = VT323({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-terminal"
});

export const metadata: Metadata = {
  title: "Ion Trap Builder",
  description: "Build ion-trap geometries and inspect RF pseudopotentials."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const deploySha = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7);

  return (
    <html lang="en">
      <body className={`${pixel.variable} ${terminal.variable}`}>
        {children}
        {deploySha ? (
          <div className="deploy-stamp" title="Vercel deployment git SHA (first 7 hex digits)">
            deploy {deploySha}
          </div>
        ) : null}
      </body>
    </html>
  );
}
