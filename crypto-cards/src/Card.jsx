import React from "react";
import clsx from "clsx";

const foilClass =
  "before:absolute before:inset-0 before:rounded-[18px] before:bg-[conic-gradient(from_180deg,transparent,rgba(255,255,255,.05),transparent_30%)] before:mix-blend-overlay before:pointer-events-none";

export default function Card({ card, onDelete, id }) {
  const { name, subtitle, rarity, power, defense, ability, palette, artDataUrl, hash } = card;

  const safePalette =
    Array.isArray(palette) && palette.length >= 3
      ? palette
      : ["hsl(222deg 47% 11%)", "hsl(230deg 45% 26%)", "hsl(260deg 60% 32%)"];
  const [primary, secondary, tertiary] = safePalette;
  const fallbackArt =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIW2NgYGD4DwABBAEAjLwYVQAAAABJRU5ErkJggg==";
  const artSrc =
    typeof artDataUrl === "string" && artDataUrl.startsWith("data:image/")
      ? artDataUrl
      : fallbackArt;

  const rim =
    rarity === "Mythic"
      ? "from-amber-400 via-fuchsia-400 to-cyan-400"
      : rarity === "Epic"
      ? "from-violet-400 to-indigo-400"
      : rarity === "Rare"
      ? "from-sky-400 to-emerald-400"
      : "from-zinc-300 to-zinc-500";

  const gem =
    rarity === "Mythic"
      ? "bg-gradient-to-br from-amber-300 to-pink-400"
      : rarity === "Epic"
      ? "bg-gradient-to-br from-violet-300 to-indigo-400"
      : rarity === "Rare"
      ? "bg-gradient-to-br from-sky-300 to-emerald-400"
      : "bg-gradient-to-br from-zinc-200 to-zinc-400";

  return (
    <div
      id={id}
      className={clsx(
        "relative w-[300px] h-[420px] rounded-2xl p-[2px] bg-gradient-to-br",
        rim,
        "shadow-[0_8px_40px_rgba(0,0,0,0.45)]"
      )}
    >
      <div
        className={clsx(
          "relative h-full rounded-[18px] overflow-hidden bg-neutral-900 border border-white/10",
          rarity === "Mythic" && foilClass
        )}
      >
        <div className="h-[60%] w-full relative">
          <img
            src={artSrc}
            alt={`Procedural artwork for card named ${name} with rarity ${rarity}`}
            className="absolute inset-0 w-full h-full object-cover"
            decoding="async"
            loading="lazy"
          />
          <div
            className="absolute inset-0 mix-blend-multiply pointer-events-none"
            style={{
              background:
                "radial-gradient(60% 60% at 50% 40%, rgba(0,0,0,0) 30%, rgba(0,0,0,.35) 100%)",
            }}
          />
          <div className="absolute top-2 right-2">
            <div className={clsx("w-8 h-8 rounded-full border border-white/30", gem)} />
          </div>
        </div>

        <div className="p-3 flex flex-col gap-1 h-[40%]">
          <div className="flex items-baseline justify-between">
            <h2 className="font-black tracking-tight text-lg leading-5 truncate" title={name}>
              {name}
            </h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/10 select-none">
              {rarity}
            </span>
          </div>
          <div className="text-[11px] text-white/60 truncate" title={subtitle}>
            {subtitle}
          </div>

          <div className="mt-2 text-sm">
            <div className="italic text-white/80 truncate" title={`Ability: ${ability}`}>
              Ability: {ability}
            </div>
          </div>

          <div className="mt-auto flex items-center justify-between">
            <div className="flex gap-2">
              <Pip label="POW" value={power} />
              <Pip label="DEF" value={defense} />
            </div>
            <button
              onClick={onDelete}
              className="text-xs px-2 py-1 rounded-md bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
              title="Delete card"
              aria-label={`Delete card ${name}`}
              type="button"
            >
              Delete
            </button>
          </div>
        </div>

        <div
          className="pointer-events-none absolute -inset-2 rounded-[22px] blur-2xl opacity-20"
          style={{
            background: `radial-gradient(60% 60% at 50% 0%, ${primary} 0%, transparent 60%), radial-gradient(50% 50% at 90% 10%, ${secondary} 0%, transparent 50%), radial-gradient(40% 40% at 10% 20%, ${tertiary} 0%, transparent 40%)`,
          }}
        />
      </div>

      <div
        className="absolute -bottom-7 left-0 text-[10px] text-white/35 w-full truncate select-text"
        title={`Card hash: ${hash}`}
      >
        #{hash.slice(0, 24)}
      </div>
    </div>
  );
}

function Pip({ label, value }) {
  return (
    <div className="px-2 py-1 rounded-md bg-white/5 border border-white/10 text-xs select-none">
      <span className="text-white/60 mr-1">{label}</span>
      <span className="font-bold tabular-nums">{value}</span>
    </div>
  );
}
