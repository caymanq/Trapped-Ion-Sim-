import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Ion Trap Builder",
  description: "Build ion-trap geometries and inspect RF pseudopotentials."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
