import type { Metadata } from "next";
import { Barlow, Barlow_Condensed, Share_Tech_Mono } from "next/font/google";
import "./globals.css";

const condensed = Barlow_Condensed({
  variable: "--font-barlow-condensed",
  subsets: ["latin"],
  weight: ["700", "800"],
});

const barlow = Barlow({
  variable: "--font-barlow",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const mono = Share_Tech_Mono({
  variable: "--font-share-tech",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "Dead Silence",
  description:
    "The last one alive on a ship. Something killed the crew and it hunts by sound. Don't breathe too loud.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${condensed.variable} ${barlow.variable} ${mono.variable} antialiased`}
    >
      <body>{children}</body>
    </html>
  );
}
