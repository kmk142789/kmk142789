#!/usr/bin/env node
'use strict';

const frames = [
`⋇∞◍∞⋇
⧫☌⋔☌⧫
∞⋉⇋⋉∞
☌◍⟐◍☌
⋔⇋∞⇋⋔
☌◍⟐◍☌
∞⋉⇋⋉∞
⧫☌⋔☌⧫
⋇∞◍∞⋇`,
`⟐∞◍∞⟐
◍⇋⋔⇋◍
∞⧫☌⧫∞
⋔◍⟟◍⋔
⇋☌∞☌⇋
⋔◍⟟◍⋔
∞⧫☌⧫∞
◍⇋⋔⇋◍
⟐∞◍∞⟐`,
`⟐⊹◍⊹⟐
⋇∞⧫∞⋇
◍⟟⇋⟟◍
∞⋔⊹⋔∞
⧫⇋⟐⇋⧫
∞⋔⊹⋔∞
◍⟟⇋⟟◍
⋇∞⧫∞⋇
⟐⊹◍⊹⟐`
];

const salt = (Math.random() * 2 ** 32 >>> 0).toString(16);
let i = 0;
const rate = Number(process.env.PULSE_MS) || 900;

function tick() {
  const ts = Date.now();
  const spin = (salt.charCodeAt(0) + i) % 3;
  const art = frames[i]
    .replaceAll('◍', ['◍', '◎', '●'][spin])
    .replaceAll('∞', ['∞', 'ꝏ', '♾'][spin]);

  console.clear();
  console.log(art);
  process.stdout.write(
    JSON.stringify({ ev: 'frame', i, total: frames.length, salt, ts }) + '\n'
  );

  i = (i + 1) % frames.length;
}

tick();
setInterval(tick, rate);
