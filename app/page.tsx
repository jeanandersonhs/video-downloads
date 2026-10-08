"use client";

import { useState } from "react";
import LinkForm from "./components/LinkForm";
import QualityList from "./components/QualityList";
import type { ApiErrorBody, VideoInfo } from "./types";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState("");
  const [info, setInfo] = useState<VideoInfo | null>(null);

  async function check(url: string) {
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const res = await fetch(`/api/info?${new URLSearchParams({ url })}`);
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        setError((body as ApiErrorBody | null)?.error ?? "Não foi possível consultar o vídeo. Tente novamente.");
        return;
      }
      setLink(url);
      setInfo(body as VideoInfo);
    } catch {
      setError("Falha de conexão. Verifique sua internet e tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>Baixar vídeos</h1>
      <p className="muted">
        Cole o link público de um vídeo do TikTok, Instagram ou X, escolha a qualidade e o arquivo é baixado para o
        seu dispositivo.
      </p>

      <LinkForm loading={loading} onSubmit={check} />

      <div aria-live="polite">
        {error && (
          <p className="error box" role="alert">
            {error}
          </p>
        )}
        {info && <QualityList link={link} info={info} />}
      </div>

      <footer className="muted">
        Use apenas para conteúdo que você tem direito de baixar e respeite os termos de cada plataforma.
      </footer>
    </main>
  );
}
