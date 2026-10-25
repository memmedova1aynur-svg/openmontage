// Flat line illustrations for carousel slides, drawn in the client's brand
// palette: navy outlines, cream/white fills, soft blue and gold accents.
// Every drawing uses a 200x200 viewBox. They are vector, typeset with the
// slide, and contain no generative-AI output.
//
// Each entry is a function (palette) => SVG inner markup. Palette keys:
//   N navy (outline), B soft blue, C cream, G gold, W near-white paper.

const ART = {
  hourglass: ({ N, G, W, C }) => `
    <rect x="52" y="18" width="96" height="14" rx="7" fill="${C}"/>
    <rect x="52" y="168" width="96" height="14" rx="7" fill="${C}"/>
    <path d="M64 32C64 76 94 86 94 100C94 114 64 124 64 168H136C136 124 106 114 106 100C106 86 136 76 136 32Z" fill="${W}"/>
    <path d="M74 58Q100 50 126 58Q118 80 100 92Q82 80 74 58Z" fill="${G}" stroke="none"/>
    <path d="M70 162Q100 124 130 162Z" fill="${G}" stroke="none"/>
    <circle cx="100" cy="108" r="2.5" fill="${G}" stroke="none"/>
    <circle cx="100" cy="120" r="2.5" fill="${G}" stroke="none"/>
    <circle cx="100" cy="132" r="2.5" fill="${G}" stroke="none"/>`,

  dice: ({ N, W, B }) => `
    <g transform="rotate(-8 80 120)">
      <rect x="30" y="72" width="96" height="96" rx="18" fill="${W}"/>
      <circle cx="56" cy="98" r="7" fill="${N}" stroke="none"/>
      <circle cx="78" cy="120" r="7" fill="${N}" stroke="none"/>
      <circle cx="100" cy="142" r="7" fill="${N}" stroke="none"/>
    </g>
    <g transform="rotate(14 150 80)">
      <rect x="112" y="40" width="70" height="70" rx="14" fill="${B}"/>
      <circle cx="132" cy="60" r="5.5" fill="${N}" stroke="none"/>
      <circle cx="162" cy="60" r="5.5" fill="${N}" stroke="none"/>
      <circle cx="132" cy="90" r="5.5" fill="${N}" stroke="none"/>
      <circle cx="162" cy="90" r="5.5" fill="${N}" stroke="none"/>
    </g>`,

  target: ({ N, B, G, W }) => `
    <path d="M70 150L56 190M130 150L144 190" />
    <circle cx="100" cy="100" r="74" fill="${W}"/>
    <circle cx="100" cy="100" r="54" fill="${B}"/>
    <circle cx="100" cy="100" r="34" fill="${N}"/>
    <circle cx="100" cy="100" r="15" fill="${G}"/>
    <path d="M100 100L168 32" stroke="${N}" stroke-width="5"/>
    <path d="M160 26L176 12L180 30L196 34L174 46Z" fill="${G}"/>`,

  cards: ({ N, W, C }) => `
    <g transform="rotate(-12 80 110)">
      <rect x="28" y="44" width="92" height="124" rx="12" fill="${C}"/>
    </g>
    <g transform="rotate(4 120 110)">
      <rect x="72" y="40" width="96" height="128" rx="12" fill="${W}"/>
      <text x="120" y="128" text-anchor="middle" font-family="M, sans-serif" font-weight="800"
        font-size="76" fill="${N}" stroke="none">?</text>
    </g>`,

  chat: ({ N, B, G }) => `
    <path d="M18 38h100a16 16 0 0 1 16 16v38a16 16 0 0 1-16 16H54l-22 20v-20H18A16 16 0 0 1 2 92V54a16 16 0 0 1 16-16z" fill="${B}" transform="translate(10 0)"/>
    <circle cx="52" cy="73" r="6" fill="${N}" stroke="none"/>
    <circle cx="72" cy="73" r="6" fill="${N}" stroke="none"/>
    <circle cx="92" cy="73" r="6" fill="${N}" stroke="none"/>
    <path d="M96 98h76a16 16 0 0 1 16 16v32a16 16 0 0 1-16 16h-8v20l-22-20H96a16 16 0 0 1-16-16v-32a16 16 0 0 1 16-16z" fill="${G}"/>
    <circle cx="116" cy="130" r="6" fill="${N}" stroke="none"/>
    <circle cx="134" cy="130" r="6" fill="${N}" stroke="none"/>
    <circle cx="152" cy="130" r="6" fill="${N}" stroke="none"/>`,

  pawn: ({ C, N }) => `
    <ellipse cx="100" cy="176" rx="46" ry="12" fill="${C}"/>
    <path d="M72 168L86 92H114L128 168Z" fill="${C}"/>
    <rect x="78" y="84" width="44" height="12" rx="6" fill="${C}"/>
    <circle cx="100" cy="58" r="26" fill="${C}"/>`,

  notepad: ({ N, W, C, G }) => `
    <rect x="34" y="34" width="122" height="150" rx="12" fill="${C}" transform="rotate(-6 95 110)"/>
    <rect x="40" y="30" width="122" height="150" rx="12" fill="${W}" transform="rotate(-6 100 105)"/>
    <g transform="rotate(-6 100 105)">
      <path d="M58 22v20M80 22v20M102 22v20M124 22v20M146 22v20"/>
      <path d="M62 72h60M62 100h60M62 128h44"/>
      <path d="M132 64l8 9 14-16M132 92l8 9 14-16" stroke="${G}"/>
    </g>`,

  pencil: ({ N, G, C }) => `
    <g transform="rotate(-38 100 100)">
      <rect x="30" y="86" width="120" height="28" rx="4" fill="${N}"/>
      <rect x="14" y="86" width="20" height="28" rx="6" fill="${G}"/>
      <path d="M150 86L186 100L150 114Z" fill="${C}"/>
      <path d="M174 95L186 100L174 105Z" fill="${N}"/>
    </g>`,

  stopwatch: ({ N, W, B, G }) => `
    <rect x="86" y="14" width="28" height="18" rx="5" fill="${N}"/>
    <path d="M150 46l12-12"/>
    <circle cx="100" cy="110" r="72" fill="${B}"/>
    <circle cx="100" cy="110" r="58" fill="${W}"/>
    <path d="M100 60v10M100 150v10M50 110h10M140 110h10M65 75l7 7M135 75l-7 7M65 145l7-7M135 145l-7-7"/>
    <path d="M100 110L128 80" stroke="${N}"/>
    <circle cx="100" cy="110" r="7" fill="${G}"/>`,

  book: ({ N, W, B }) => `
    <path d="M100 52C80 38 46 36 18 44V164C46 156 80 158 100 172Z" fill="${W}"/>
    <path d="M100 52C120 38 154 36 182 44V164C154 156 120 158 100 172Z" fill="${B}"/>
    <path d="M100 52V172"/>
    <path d="M36 74c18-4 36-2 48 4M36 98c18-4 36-2 48 4M36 122c18-4 36-2 48 4"/>
    <path d="M116 78c12-6 30-8 48-4M116 102c12-6 30-8 48-4"/>`,

  music: ({ N, G, B }) => `
    <path d="M78 140V46l92-20v92" />
    <path d="M78 66l92-20"/>
    <ellipse cx="60" cy="142" rx="22" ry="16" fill="${G}"/>
    <ellipse cx="152" cy="120" rx="22" ry="16" fill="${G}"/>
    <path d="M24 60c8-10 20-10 26 0" stroke="${B}"/>
    <path d="M18 40c14-18 36-18 46 0" stroke="${B}"/>`,

  blocks: ({ N, C, B, G }) => `
    <rect x="20" y="104" width="76" height="76" rx="10" fill="${C}"/>
    <text x="58" y="160" text-anchor="middle" font-family="M, sans-serif" font-weight="800" font-size="46" fill="${N}" stroke="none">A</text>
    <rect x="104" y="104" width="76" height="76" rx="10" fill="${B}"/>
    <text x="142" y="160" text-anchor="middle" font-family="M, sans-serif" font-weight="800" font-size="46" fill="${N}" stroke="none">B</text>
    <rect x="62" y="24" width="76" height="76" rx="10" fill="${G}" transform="rotate(-6 100 62)"/>
    <text x="100" y="80" text-anchor="middle" font-family="M, sans-serif" font-weight="800" font-size="46" fill="${N}" stroke="none" transform="rotate(-6 100 62)">C</text>`,

  star: ({ G }) => `
    <path d="M100 18l22 48 52 6-38 36 10 52-46-26-46 26 10-52-38-36 52-6z" fill="${G}"/>`,

  bulb: ({ N, W, G }) => `
    <path d="M100 30a50 50 0 0 0-30 90c8 7 12 16 12 24h36c0-8 4-17 12-24a50 50 0 0 0-30-90z" fill="${W}"/>
    <path d="M82 160h36M88 178h24"/>
    <path d="M100 6v12M40 30l9 9M160 30l-9 9M18 86h12M170 86h12" stroke="${G}"/>
    <path d="M88 116l12-20 12 20" stroke="${G}"/>`,

  laptop: ({ N, W, B, G }) => `
    <rect x="34" y="40" width="132" height="92" rx="10" fill="${N}"/>
    <rect x="44" y="50" width="112" height="72" rx="4" fill="${B}" stroke="none"/>
    <circle cx="100" cy="78" r="12" fill="${W}" stroke="none"/>
    <path d="M80 112c4-12 36-12 40 0" stroke="${W}"/>
    <path d="M14 140h172l-12 22H26z" fill="${W}"/>
    <path d="M84 150h32" stroke="${G}"/>`,

  board: ({ N, W, G, B }) => `
    <rect x="16" y="30" width="168" height="112" rx="8" fill="${W}"/>
    <path d="M40 62h70M40 86h100M40 110h56" stroke="${B}"/>
    <path d="M146 58l10 10 18-22" stroke="${G}"/>
    <path d="M70 142l-18 40M130 142l18 40M100 142v28"/>`,

  puzzle: ({ N, B, G }) => `
    <path d="M30 60h36a16 16 0 1 1 32 0h36v36a16 16 0 1 0 0 32v36H98a16 16 0 1 0-32 0H30z" fill="${B}"/>
    <path d="M134 96a16 16 0 1 1 0 32" fill="${G}"/>`,

  trophy: ({ N, G, C }) => `
    <path d="M62 30h76v40a38 38 0 0 1-76 0z" fill="${G}"/>
    <path d="M62 44H38c0 26 14 38 28 38M138 44h24c0 26-14 38-28 38"/>
    <path d="M100 108v24"/>
    <rect x="66" y="132" width="68" height="20" rx="4" fill="${C}"/>
    <rect x="54" y="152" width="92" height="24" rx="6" fill="${C}"/>`,

  magnifier: ({ N, W, B, G }) => `
    <circle cx="86" cy="86" r="56" fill="${W}"/>
    <circle cx="86" cy="86" r="40" fill="${B}" stroke="none"/>
    <path d="M128 128l44 44" stroke-width="14"/>
    <path d="M62 76a26 26 0 0 1 22-20" stroke="${G}"/>`,

  headphones: ({ N, G, C }) => `
    <path d="M36 120V100a64 64 0 0 1 128 0v20"/>
    <rect x="24" y="112" width="34" height="58" rx="12" fill="${G}"/>
    <rect x="142" y="112" width="34" height="58" rx="12" fill="${G}"/>`,
};

function art(name, palette, size) {
  const draw = ART[name];
  if (!draw) {
    throw new Error(`unknown illustration: ${name} (have: ${Object.keys(ART).join(', ')})`);
  }
  return `<svg class="art-item" width="${size}" height="${size}" viewBox="0 0 200 200" fill="none"
    stroke="${palette.N}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">${draw(palette)}</svg>`;
}

module.exports = { ART, art };
