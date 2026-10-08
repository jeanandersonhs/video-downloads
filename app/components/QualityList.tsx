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

type Props = {
  link: string;
  info: VideoInfo;
};

export default function QualityList({ link, info }: Props) {
  const meta = [info.platform === "twitter" ? "X / Twitter" : info.platform, formatDuration(info.duration)]
    .filter(Boolean)
    .join(" · ");

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
            <a href={downloadHref(link, quality)} download>
              <span className="label">{quality.label}</span>
              <span className="muted">
                {[quality.ext?.toUpperCase(), formatSize(quality.size)].filter(Boolean).join(" · ")}
              </span>
              <span className="action">Baixar</span>
            </a>
          </li>
        ))}
      </ul>
      {info.platform === "tiktok" && <p className="muted">Vídeos do TikTok são baixados sem a marca d’água.</p>}
    </section>
  );
}
