"use client";

import { FormEvent, useState } from "react";

const SUPPORTED = /(^|\.)(tiktok\.com|instagram\.com|twitter\.com|x\.com)$/i;

export function isSupportedLink(value: string): boolean {
  try {
    const url = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(value) ? value : `https://${value}`);
    return SUPPORTED.test(url.hostname);
  } catch {
    return false;
  }
}

type Props = {
  loading: boolean;
  onSubmit: (url: string) => void;
};

export default function LinkForm({ loading, onSubmit }: Props) {
  const [value, setValue] = useState("");
  const [invalid, setInvalid] = useState(false);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const link = value.trim();
    if (!isSupportedLink(link)) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    onSubmit(link);
  }

  return (
    <form className="link-form" onSubmit={handleSubmit} noValidate>
      <label htmlFor="link">Link público do vídeo</label>
      <div className="row">
        <input
          id="link"
          type="url"
          inputMode="url"
          autoComplete="off"
          placeholder="https://www.tiktok.com/@usuario/video/…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          aria-invalid={invalid}
          aria-describedby={invalid ? "link-error" : undefined}
        />
        <button type="submit" disabled={loading || !value.trim()}>
          {loading ? "Verificando…" : "Verificar"}
        </button>
      </div>
      {invalid && (
        <p id="link-error" className="error" role="alert">
          Use um link do TikTok, Instagram ou Twitter/X.
        </p>
      )}
    </form>
  );
}
