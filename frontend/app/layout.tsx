import type { Metadata } from "next";
import { Cinzel } from "next/font/google";
import "./styles.css";

const cinzel = Cinzel({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-cinzel"
});

export const metadata: Metadata = {
  title: "Ion Trap Builder",
  description: "Build ion-trap geometries and inspect RF pseudopotentials."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const deploySha = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7);

  return (
    <html lang="en">
      <body className={cinzel.variable}>
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
