# Baixar vídeos (TikTok, Instagram, Twitter/X)

App web para a Vercel: o usuário cola o link público do vídeo, o servidor lista as qualidades disponíveis e o arquivo
é baixado direto para o dispositivo dele. No TikTok o vídeo vem **sem a marca d'água**.

- Frontend: Next.js (`app/`).
- API: função Python (FastAPI + yt-dlp) em `api/index.py`, com o núcleo em `downloader/`.
  - `GET /api/info?url=…` → título, miniatura e qualidades.
  - `GET /api/download?url=…&format=…` → stream do arquivo com `Content-Disposition: attachment`.

## Rodar localmente
```bash
# API Python (porta 8787)
python3 -m venv .venv && source .venv/bin/activate   # no Debian/Ubuntu: sudo apt install python3-venv
pip install -r requirements-dev.txt
uvicorn api.index:app --port 8787

# Frontend (outro terminal) — o dev server redireciona /api/* para a API acima
npm install
npm run dev
```
Alternativa: `npx vercel dev` roda as duas partes como na produção. A origem da API em dev pode ser trocada com `API_ORIGIN`.

Testes: `pytest`.

## Deploy
`vercel` (ou conectar o repositório). `vercel.json` roteia `/api/*` para a função Python e define `maxDuration`/memória.

Variáveis de ambiente opcionais (úteis quando a plataforma bloqueia IPs de datacenter, comum no Instagram):
- `PROXY_URL` — proxy (de preferência residencial) usado pelo yt-dlp na extração.
- `COOKIES_TXT` — conteúdo de um `cookies.txt` (formato Netscape) de uma conta dedicada.

## Limitações
- Sem ffmpeg na Vercel: só formatos progressivos (vídeo+áudio no mesmo arquivo); não há mp3 nem merge de DASH.
- O download passa pela função (stream), então consome tempo e banda do plano da Vercel. Considere regras de rate limit no Vercel Firewall.
- Instagram costuma bloquear acesso anônimo vindo de datacenter. Verifique em um deploy de preview.
- O fallback do TikTok usa o serviço de terceiros tikwm.com e pode deixar de funcionar.

Use apenas para conteúdo que você tem direito de baixar e respeite os termos de cada plataforma.
