type BrandLogoProps = {
  variant: "sidebar" | "login";
};

export function BrandLogo({ variant }: BrandLogoProps) {
  if (variant === "login") {
    return (
      <div className="mb-8 text-center">
        <div className="text-3xl font-bold tracking-normal text-white">Techpedia</div>
        <div className="mt-1 text-sm font-medium text-slate-300">AI Assistant</div>
      </div>
    );
  }

  return (
    <div className="min-w-0">
      <div className="truncate text-lg font-bold tracking-normal text-white">Techpedia</div>
      <div className="truncate text-xs font-medium text-slate-400">AI Assistant</div>
    </div>
  );
}
