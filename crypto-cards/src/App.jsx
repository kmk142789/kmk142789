import React, { useEffect, useRef, useState } from "react";
import CryptoJS from "crypto-js";
import Card from "./Card.jsx";
import { hashArtDataUrl, pickColorsFromHash, titleFromHash } from "./hashArt.js";

const RARITIES = ["Common", "Rare", "Epic", "Mythic"];
const ABILITIES = [
  "Hash Surge",
  "Block Forged",
  "Nonce Shift",
  "Genesis Echo",
  "Merkle Bloom",
  "Satoshi’s Whim",
  "Patoshi Pulse",
  "Ordinals Twist",
];

export default function App() {
  const [input, setInput] = useState("");
  const [cards, setCards] = useState([]);
  const fileRef = useRef(null);

  // load collection
  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem("cards_v2")) || [];
    setCards(stored);
  }, []);

  const save = (next) => {
    setCards(next);
    localStorage.setItem("cards_v2", JSON.stringify(next));
  };

  const mint = () => {
    if (!input.trim()) return;
    const raw = input.trim();

    const hash = CryptoJS.SHA256(raw).toString();
    const id = hash;

    // If card exists, focus it rather than duplicate
    const i = cards.findIndex((c) => c.id === id);
    if (i >= 0) {
      const el = document.getElementById(`card-${id}`);
      if (el) {
        el.classList.remove("animate-pulse");
        void el.offsetWidth;
        el.classList.add("animate-pulse");
        setTimeout(() => el.classList.remove("animate-pulse"), 600);
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      setInput("");
      return;
    }

    // Attribute slices
    // Weighted rarity: Common 60%, Rare 25%, Epic 10%, Mythic 5%
    const rarityRoll = parseInt(hash.slice(0, 2), 16) / 255;
    let rarity;
    if (rarityRoll < 0.6) rarity = "Common";
    else if (rarityRoll < 0.85) rarity = "Rare";
    else if (rarityRoll < 0.95) rarity = "Epic";
    else rarity = "Mythic";

    const power = (parseInt(hash.slice(2, 4), 16) % 10) + 1;
    const defense = (parseInt(hash.slice(4, 6), 16) % 10) + 1;
    const ability = ABILITIES[parseInt(hash.slice(6, 8), 16) % ABILITIES.length];

    const palette = pickColorsFromHash(hash);
    const artDataUrl = hashArtDataUrl(hash, { width: 480, height: 672, palette });

    const card = {
      id,
      name: titleFromHash(hash),
      subtitle: `Genesis ${hash.slice(0, 6).toUpperCase()}`,
      hash,
      rarity,
      power,
      defense,
      ability,
      palette,
      artDataUrl,
      createdAt: Date.now(),
      source: raw,
    };

    save([card, ...cards]);
    setInput("");
  };

  const remove = (id) => {
    save(cards.filter((c) => c.id !== id));
  };

  const clearAll = () => {
    if (!confirm("Clear your entire collection?")) return;
    save([]);
  };

  const doExport = () => {
    const blob = new Blob([JSON.stringify(cards, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), {
      href: url,
      download: "crypto-cards-export.json",
    });
    a.click();
    URL.revokeObjectURL(url);
  };

  const doImportClick = () => fileRef.current?.click();

  const doImportFile = async (e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    try {
      const text = await f.text();
      const incoming = JSON.parse(text);
      if (!Array.isArray(incoming)) throw new Error("Invalid file");
      const map = new Map(cards.map((c) => [c.id, c]));
      incoming.forEach((c) => map.set(c.id, c));
      save(Array.from(map.values()).sort((a, b) => b.createdAt - a.createdAt));
    } catch (err) {
      alert("Import failed: " + err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-neutral-950 text-neutral-100">
      <header className="sticky top-0 backdrop-blur bg-neutral-950/70 border-b border-white/10 z-20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-4">
          <h1 className="text-2xl md:text-3xl font-black tracking-tight select-none">
            ⚡ Magic Crypto Cards
          </h1>
          <span className="ml-auto hidden sm:inline text-xs text-white/60 select-none">
            Deterministic hash-forged trading cards
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 flex-grow">
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3 mb-8">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter any text (mock key, phrase, etc.)"
            className="px-4 py-3 rounded-xl bg-white text-black w-full md:w-[520px] shadow-inner focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Input text to generate card"
            onKeyDown={(e) => {
              if (e.key === "Enter") mint();
            }}
          />
          <button
            onClick={mint}
            className="bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 px-5 py-3 rounded-xl font-bold shadow-lg transition-colors"
            aria-label="Generate card"
            type="button"
          >
            Generate
          </button>

          <div className="flex gap-2 md:ml-auto flex-wrap">
            <button
              onClick={doExport}
              className="px-4 py-3 rounded-xl border border-white/15 hover:bg-white/5 transition-colors whitespace-nowrap"
              title="Export your collection to JSON"
              type="button"
            >
              Export JSON
            </button>
            <button
              onClick={doImportClick}
              className="px-4 py-3 rounded-xl border border-white/15 hover:bg-white/5 transition-colors whitespace-nowrap"
              title="Import a previously exported JSON"
              type="button"
            >
              Import JSON
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="application/json"
              className="hidden"
              onChange={doImportFile}
              aria-hidden="true"
              tabIndex={-1}
            />
            <button
              onClick={clearAll}
              className="px-4 py-3 rounded-xl border border-rose-500/40 text-rose-300 hover:bg-rose-500/10 transition-colors whitespace-nowrap"
              title="Clear all cards"
              type="button"
            >
              Clear All
            </button>
          </div>
        </div>

        {cards.length === 0 ? (
          <p className="text-white/60 max-w-xl leading-relaxed">
            No cards yet—mint one with any text. The art, name, stats and ability
            are all derived from the SHA-256 hash of your input.
          </p>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 justify-center">
            {cards.map((c) => (
              <Card key={c.id} id={`card-${c.id}`} card={c} onDelete={() => remove(c.id)} />
            ))}
          </div>
        )}
      </main>

      <footer className="max-w-7xl mx-auto px-4 py-10 text-sm text-white/50 select-none">
        <p>
          Deterministic generator • Local-only • No network calls • Your data stays
          in your browser (localStorage).
        </p>
      </footer>
    </div>
  );
}
