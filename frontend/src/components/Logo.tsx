export function Logo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative h-9 w-9 border-[1.5px] border-foreground flex items-center justify-center">
        <div className="h-3 w-3 bg-primary" />
        <span className="absolute -top-px -left-px h-1.5 w-1.5 border-t-[1.5px] border-l-[1.5px] border-foreground" />
        <span className="absolute -bottom-px -right-px h-1.5 w-1.5 border-b-[1.5px] border-r-[1.5px] border-foreground" />
      </div>
      <div className="flex flex-col leading-none">
        <span className="font-display font-semibold text-[15px] tracking-tight">
          Demeo
        </span>
        <span className="label-mono mt-0.5">№ 001 · Operator</span>
      </div>
    </div>
  );
}
