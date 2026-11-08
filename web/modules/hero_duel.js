/**
 * Cena vetorial decorativa do banner (sem GIF, rede ou dependências).
 * Permanecem as mesmas cinco camadas de parallax do banner original.
 * O movimento só começa após a introdução cinematográfica ser encerrada.
 */
export function heroDuelMarkup(waitForIntro = false) {
  const mode = waitForIntro ? 'is-waiting' : 'is-playing';
  return `<div class="hero-duel-stage ${mode}" aria-hidden="true">
    <svg class="hero-duel-svg" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
      <defs>
        <linearGradient id="cm-duel-gold" x1="0" y1="0" x2=".93" y2=".25">
          <stop stop-color="#A96305"/><stop offset=".20" stop-color="#FFF4B2"/>
          <stop offset=".39" stop-color="#FFDA34"/><stop offset=".55" stop-color="#926007"/>
          <stop offset=".76" stop-color="#FFDE62"/><stop offset="1" stop-color="#8C4F08"/>
        </linearGradient>
        <linearGradient id="cm-duel-onyx" x1=".02" y1="0" x2=".91" y2=".28">
          <stop stop-color="#111419"/><stop offset=".3" stop-color="#737C88"/>
          <stop offset=".52" stop-color="#14171E"/><stop offset=".78" stop-color="#4C5360"/>
          <stop offset="1" stop-color="#090C11"/>
        </linearGradient>
        <radialGradient id="cm-duel-light">
          <stop stop-color="#FFD600" stop-opacity=".48"/>
          <stop offset=".55" stop-color="#D4A017" stop-opacity=".13"/>
          <stop offset="1" stop-color="#D4A017" stop-opacity="0"/>
        </radialGradient>
        <pattern id="cm-duel-board" width="70" height="70" patternUnits="userSpaceOnUse">
          <rect width="70" height="70" fill="#101217"/>
          <path d="M0 0H35V35H0Z M35 35H70V70H35Z" fill="#373022"/>
        </pattern>
      </defs>
      <ellipse cx="490" cy="315" rx="295" ry="92" fill="url(#cm-duel-light)"/>
      <path d="M85 316H694L789 396H13Z" fill="url(#cm-duel-board)" stroke="#B88D2C" stroke-width="2" stroke-opacity=".5"/>
      <path d="M80 319H710M31 370H769M246 317L189 395M380 317L376 395M520 317L566 395M645 317L748 395" stroke="#D4A017" stroke-opacity=".32" stroke-width="2"/>
      <ellipse cx="308" cy="322" rx="94" ry="15" fill="#060708" opacity=".75"/>
      <ellipse cx="530" cy="324" rx="72" ry="13" fill="#07080A" opacity=".65"/>
      <g class="hero-duel-king" fill="url(#cm-duel-onyx)" stroke="#AEB9C3" stroke-width="2.4" stroke-linejoin="round">
        <path d="M522 130V96H538V130H561V143H538V169H522V143H499V130Z" fill="#C5A052" stroke="#181B20"/>
        <path d="M489 171L501 192H555L567 171L551 177L530 156L511 177Z"/>
        <path d="M498 195H561L553 224H506Z"/>
        <path d="M512 225H544L546 245Q554 275 568 297H487Q506 270 509 245Z"/>
        <path d="M484 294H571V307H484Z"/>
        <path d="M474 307H581L588 321H468Z" fill="#555D68" />
        <path d="M499 214H559M494 305H568" fill="none" stroke="#FFD36A" stroke-opacity=".52" stroke-width="2"/>
      </g>
      <g class="hero-duel-impact">
        <ellipse cx="509" cy="273" rx="91" ry="62" fill="url(#cm-duel-light)"/>
        <path d="M459 248L434 227M463 264L427 259M457 283L430 307M491 230L488 204M502 295L498 330"
          fill="none" stroke="#FFDE58" stroke-width="5" stroke-linecap="round"/>
        <circle cx="467" cy="260" r="8" fill="#FFF8C9"/>
      </g>
      <g class="hero-duel-pawn" fill="url(#cm-duel-gold)" stroke="#E7B73E" stroke-width="2.3" stroke-linejoin="round">
        <ellipse cx="292" cy="322" rx="63" ry="10" fill="#0B0D11" opacity=".8" stroke="none"/>
        <circle cx="290" cy="178" r="33"/>
        <ellipse cx="290" cy="216" rx="36" ry="11"/>
        <path d="M269 225H310Q302 269 332 300H248Q278 270 269 225Z"/>
        <rect x="245" y="298" width="90" height="13" rx="5"/>
        <path d="M241 309H339L347 323H232Z"/>
        <path d="M273 159Q283 147 293 148" stroke="#FFF9C9" stroke-width="5" fill="none" stroke-linecap="round"/>
        <text x="290" y="287" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="900" stroke="none" fill="#291A06">CM</text>
      </g>
    </svg>
  </div>`;
}
