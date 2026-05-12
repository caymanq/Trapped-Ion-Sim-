import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Ion Trap Builder",
  description: "Build ion-trap geometries and inspect RF pseudopotentials."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const deploySha = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7);

  return (
    <html lang="en">
      <body>
        {children}
        {deploySha ? (
          <div className="deploy-stamp" title="Vercel deployment git SHA">
            deploy {deploySha}
          </div>
        ) : null}
      </body>
    </html>
  );
}
