import Image from "next/image";

export const BRAND_FULL_NAME = "Adaptive Neural Decision AI";

type BrandLogoProps = {
  /** Sidebar: compact two-line title. Login: single centered headline. */
  variant: "sidebar" | "login";
};

export function BrandLogo({ variant }: BrandLogoProps) {
  if (variant === "login") {
    return (
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center mb-4 p-6 bg-white rounded-2xl shadow-xl">
          <Image
            src="/andai_logo_transparent.png"
            alt={BRAND_FULL_NAME}
            width={160}
            height={160}
            className="object-contain h-24 w-auto max-w-[min(100%,280px)]"
            priority
          />
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white leading-snug px-2">
          {BRAND_FULL_NAME}
        </h1>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3">
      <div className="bg-white rounded-lg p-1.5 shrink-0">
        <Image
          src="/andai_logo_transparent.png"
          alt=""
          width={40}
          height={40}
          className="object-contain h-7 w-7"
          priority
        />
      </div>
      <div className="leading-snug min-w-0">
        <span className="block text-[13px] font-bold text-white tracking-tight">
          Adaptive Neural
        </span>
        <span className="block text-[13px] font-bold text-white tracking-tight">
          Decision AI
        </span>
      </div>
    </div>
  );
}
