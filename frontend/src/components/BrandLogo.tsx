import Image from "next/image";

/** Canonical logo asset in `/public` (ANDAI artwork) */
export const BRAND_LOGO_SRC = "/andai-logo.png";

type BrandLogoProps = {
  /** Sidebar: compact two-line title. Login: single centered headline. */
  variant: "sidebar" | "login";
};

export function BrandLogo({ variant }: BrandLogoProps) {
  if (variant === "login") {
    return (
      <div className="flex justify-center mb-8">
        <Image
          src={BRAND_LOGO_SRC}
          alt="ANDAI"
          width={560}
          height={186}
          className="object-contain w-full max-w-[min(100%,340px)] h-auto max-h-[120px]"
          priority
        />
      </div>
    );
  }

  return (
    <div className="flex items-center shrink-0 min-w-0">
      <Image
        src={BRAND_LOGO_SRC}
        alt="ANDAI"
        width={160}
        height={53}
        className="object-contain h-9 w-auto max-w-[11rem]"
        priority
      />
    </div>
  );
}
