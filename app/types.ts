export type Quality = {
  id: string;
  label: string;
  height: number | null;
  ext: string | null;
  size: number | null;
};

export type VideoInfo = {
  platform: "tiktok" | "instagram" | "twitter";
  title: string | null;
  thumbnail: string | null;
  duration: number | null;
  qualities: Quality[];
};

export type ApiErrorBody = { error: string; code: string };
