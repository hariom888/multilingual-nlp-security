import "./globals.css";

export const metadata = {
  title: "NLP Guardrails | Prompt Injection Security",
  description: "A multilingual prompt-injection security demonstration.",
};

export default function RootLayout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
