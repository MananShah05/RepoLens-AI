"use client";

import React, { useEffect, useState } from "react";

type Props = { lines: string[]; interval?: number };

function TypewriterInner({ lines, interval = 2500 }: Props) {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setIdx((i) => (i + 1) % lines.length), interval);
    return () => clearInterval(t);
  }, [lines.length, interval]);

  return (
    <div className="font-display text-base text-foreground/90">
      <span>{lines[idx]}</span>
      <span className="ml-1 text-foreground/90 animate-blink">|</span>
    </div>
  );
}

export default React.memo(TypewriterInner);
