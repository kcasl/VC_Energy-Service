import { useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

export default function Tex({ expr, display = false }: { expr: string; display?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    katex.render(expr, ref.current, { throwOnError: false, displayMode: display });
  }, [expr, display]);
  return <div ref={ref} className={display ? "tex-display" : "tex-inline"} />;
}
