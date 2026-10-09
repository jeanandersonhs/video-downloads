"use client";

import { MouseEvent, useState } from "react";
import { canSaveToGallery, fetchVideo, mimeType, saveFile, shareVideo } from "../lib/saveVideo";
import type { Quality, VideoInfo } from "../types";

function formatSize(bytes: number | null): string | null {
  if (!bytes) return null;
  return `~${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDuration(seconds: number | null): string | null {
  if (!seconds) return null;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function downloadHref(link: string, quality: Quality): string {
  return `/api/download?${new URLSearchParams({ url: link, format: quality.id })}`;
}

type Save =
  | { status: "idle" }
  | { status: "downloading"; id: string; progress: number | null }
  | { status: "ready"; id: string; file: File }
  | { status: "error"; message: string };

type Props = {
  link: string;
  info: VideoInfo;
};

export default function QualityList({ link, info }: Props) {
  const [save, setSave] = useState<Save>({ status: "idle" });
  const meta = [info.platform === "twitter" ? "X / Twitter" : info.platform, formatDuration(info.duration)]
    .filter(Boolean)
    .join(" · ");

  async function share(id: string, file: File) {
    try {
      const result = await shareVideo(file);
      setSave(result === "shared" ? { status: "idle" } : { status: "ready", id, file });
    } catch {
      saveFile(file);
      setSave({ status: "idle" });
    }
  }

  // Sem suporte (desktop, Android), o link segue como download comum.
  async function handleClick(event: MouseEvent<HTMLAnchorElement>, quality: Quality) {
    const type = mimeType(quality.ext);
    if (!canSaveToGallery(type)) return;
    event.preventDefault();
    if (save.status === "downloading") return;

    setSave({ status: "downloading", id: quality.id, progress: null });
    let file: File;
    try {
      file = await fetchVideo(downloadHref(link, quality), type, (progress) =>
        setSave({ status: "downloading", id: quality.id, progress }),
      );
    } catch (error) {
      setSave({ status: "error", message: error instanceof Error ? error.message : "Falha no download." });
      return;
    }
    await share(quality.id, file);
  }

  function actionLabel(quality: Quality): string {
    if (save.status !== "downloading" || save.id !== quality.id) return "Baixar";
    return save.progress === null ? "Baixando…" : `${Math.round(save.progress * 100)}%`;
  }

  return (
    <section className="result" aria-labelledby="result-title">
      <div className="video">
        {info.thumbnail && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={info.thumbnail}
            alt=""
            referrerPolicy="no-referrer"
            onError={(e) => (e.currentTarget.style.display = "none")}
          />
        )}
        <div>
          <h2 id="result-title">{info.title || "Vídeo encontrado"}</h2>
          <p className="muted">{meta}</p>
        </div>
      </div>

      <h3>Escolha a qualidade</h3>
      <ul className="qualities">
        {info.qualities.map((quality) => (
          <li key={quality.id}>
            <a
              href={downloadHref(link, quality)}
              download
              onClick={(e) => handleClick(e, quality)}
              aria-busy={save.status === "downloading" && save.id === quality.id}
            >
              <span className="label">{quality.label}</span>
              <span className="muted">
                {[quality.ext?.toUpperCase(), formatSize(quality.size)].filter(Boolean).join(" · ")}
              </span>
              <span className="action">{actionLabel(quality)}</span>
            </a>
          </li>
        ))}
      </ul>

      <div aria-live="polite">
        {save.status === "ready" && (
          <div className="saved">
            <p>Vídeo pronto. Toque em salvar e escolha “Salvar vídeo” para enviá-lo à galeria.</p>
            <div className="row">
              <button type="button" onClick={() => share(save.id, save.file)}>
                Salvar na galeria
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  saveFile(save.file);
                  setSave({ status: "idle" });
                }}
              >
                Salvar em Arquivos
              </button>
            </div>
          </div>
        )}
        {save.status === "error" && (
          <p className="error box" role="alert">
            {save.message}
          </p>
        )}
      </div>

      {info.platform === "tiktok" && <p className="muted">Vídeos do TikTok são baixados sem a marca d’água.</p>}
    </section>
  );
}
