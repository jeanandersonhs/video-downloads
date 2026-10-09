// Navegadores não gravam direto na galeria: um download comum vai para "Arquivos" (no iOS) ou "Downloads".
// No iPhone/iPad o único caminho até o app Fotos é a folha de compartilhamento ("Salvar vídeo"), que exige
// o arquivo já em memória. No Android o download comum já aparece na galeria (pasta Download).

const MIME_TYPES: Record<string, string> = { mp4: "video/mp4", mov: "video/quicktime", webm: "video/webm" };

export function mimeType(ext: string | null): string {
  return MIME_TYPES[(ext ?? "mp4").toLowerCase()] ?? "video/mp4";
}

function isAppleMobile(): boolean {
  const ua = navigator.userAgent;
  // iPadOS se identifica como Mac; a tela touch denuncia.
  return /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
}

export function canSaveToGallery(type: string): boolean {
  if (typeof navigator === "undefined" || !navigator.canShare || !isAppleMobile()) return false;
  try {
    return navigator.canShare({ files: [new File([], "video", { type })] });
  } catch {
    return false;
  }
}

function filenameFrom(disposition: string | null): string | null {
  if (!disposition) return null;
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1]);
    } catch {
      // cai para o filename simples
    }
  }
  return /filename="([^"]+)"/i.exec(disposition)?.[1] ?? null;
}

/** Baixa o vídeo para a memória. `onProgress` recebe 0–1, ou null se o tamanho for desconhecido. */
export async function fetchVideo(href: string, type: string, onProgress: (progress: number | null) => void) {
  const res = await fetch(href);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? "Não foi possível baixar o vídeo. Tente novamente.");
  }
  const name = filenameFrom(res.headers.get("content-disposition")) ?? "video.mp4";
  if (!res.body) return new File([await res.blob()], name, { type });

  const total = Number(res.headers.get("content-length")) || 0;
  const reader = res.body.getReader();
  const chunks: BlobPart[] = [];
  let loaded = 0;
  onProgress(total ? 0 : null);
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.byteLength;
    if (total) onProgress(Math.min(loaded / total, 1));
  }
  return new File(chunks, name, { type });
}

/**
 * Abre a folha de compartilhamento. Retorna "blocked" quando o navegador exige um toque novo
 * (o gesto que iniciou o download expira enquanto o arquivo baixa).
 */
export async function shareVideo(file: File): Promise<"shared" | "cancelled" | "blocked"> {
  try {
    await navigator.share({ files: [file] });
    return "shared";
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return "cancelled";
    if (error instanceof DOMException && error.name === "NotAllowedError") return "blocked";
    throw error;
  }
}

/** Download comum (vai para "Arquivos"/"Downloads"). */
export function saveFile(file: File): void {
  const url = URL.createObjectURL(file);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
