import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 32,
          height: 32,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#14161b",
          borderRadius: 8,
        }}
      >
        <svg width="24" height="24" viewBox="0 0 40 40" fill="none">
          <circle cx="20" cy="20" r="3" fill="#c4a882" />
          <path
            d="M20 6 A18 18 0 0 1 35.6 28"
            stroke="#c4a882"
            strokeWidth="2"
            fill="none"
          />
          <path
            d="M35.6 28 A18 18 0 0 1 4.4 28"
            stroke="#c4a882"
            strokeWidth="2"
            fill="none"
            opacity="0.7"
          />
          <path
            d="M4.4 28 A18 18 0 0 1 20 6"
            stroke="#c4a882"
            strokeWidth="2"
            fill="none"
            opacity="0.5"
          />
        </svg>
      </div>
    ),
    { ...size }
  );
}
