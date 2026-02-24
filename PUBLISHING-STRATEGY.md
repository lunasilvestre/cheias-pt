# cheias.pt — Publishing & Impact Strategy

## Timing

The crisis window is still open. Portugal declared a state of emergency, municipalities are still in recovery mode, and the public conversation about flood preparedness is active. This is the ideal moment — the piece is retrospective (what happened and why), not speculative.

**Target launch:** Within 1-2 weeks of completing the scroll narrative. Delay costs relevance. A polished v0 with chapters 0-5 + 7-9 (data chapters working, CEMS flood extent + consequence markers as stretch) is publishable. Don't wait for perfection.

**Day of week:** Tuesday or Wednesday morning (PT time, 9-10am). Avoids Monday noise and weekend burial. LinkedIn engagement peaks mid-week.

## Audiences & Channels

### 1. Development Seed (primary portfolio target)

**What they care about:** MapLibre, STAC/COG, cloud-native geospatial, scrollytelling for environmental storytelling. They built incendios.pt with Flipside, they built Global Forest Watch with Vizzuality alumni.

**Channel:** LinkedIn (EN) + direct message to specific people.

**Who to reach:**
- Daniel da Silva (CEO, Lisbon) — search LinkedIn
- Dãniel Kastl (engineering) — active on geo-Twitter
- DevSeed team members who worked on incendios.pt
- Anyone posting about MapLibre or Portugal on their team

**Message angle:** "I built the flood equivalent of what you did with incendios.pt — same stack (MapLibre, Sentinel, scrollytelling), applied to the ongoing flood crisis. Here's the live piece."

### 2. Portuguese civic tech / journalism

**What they care about:** Useful public information during a crisis, data journalism, holding institutions accountable for lack of flood prediction systems.

**Channel:** Twitter/X (PT) + direct outreach to journalists.

**Who to reach:**
- fogos.pt team (João Pina) — the spiritual predecessor, massive audience
- Público data journalism team (P3, data desk)
- Expresso Economia / SIC Notícias data team
- Portuguese GIS community (esriportugal, SNIG)
- Proteção Civil communications team
- LNEC (Laboratório Nacional de Engenharia Civil) — flood research
- APA (Agência Portuguesa do Ambiente) — water resources

**Message angle:** "Portugal não tem um sistema nacional de previsão de cheias. Criei uma plataforma aberta, com dados de satélite e modelos hidrológicos, que mostra o que aconteceu e porquê. Os dados já sabiam."

### 3. International GIS / earth observation community

**What they care about:** Open data, Copernicus ecosystem, civic applications of EO, GloFAS, CEMS.

**Channel:** LinkedIn (EN), Twitter/X (EN), Mastodon (fosstodon.org has geo community).

**Who to reach:**
- Copernicus EMS team (they activated EMSR861/EMSR864 — show them a downstream use)
- Open-Meteo creator (Patrick Zippenfenig) — show their API powering a real civic tool
- MapLibre community
- Cloud-Native Geospatial Foundation
- Vizzuality team (they pioneered this type of storytelling)

**Message angle:** "Built a scrollytelling piece about Portugal's flood crisis using entirely open data: Copernicus EMS polygons, Open-Meteo soil moisture + discharge, MapLibre GL JS. Here's what a precondition-based flood narrative looks like."

## Content Assets (prepare before launch)

### OG Meta Tags (already partially in index.html — verify/update)

```html
<meta property="og:title" content="O Inverno Que Partiu os Rios">
<meta property="og:description" content="Como três tempestades expuseram a fragilidade de Portugal. Uma história contada com dados de satélite e modelos hidrológicos.">
<meta property="og:image" content="https://cheias.pt/assets/og-image.png">
<meta property="og:url" content="https://cheias.pt">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="O Inverno Que Partiu os Rios">
<meta name="twitter:image" content="https://cheias.pt/assets/og-image.png">
```

### OG Image (1200×630px)

Create a striking card: dark navy background, the hero title in Georgia serif, a subtle satellite image or soil moisture map faded behind. Include "cheias.pt" in bottom corner. This is what shows when the link is shared on LinkedIn/Twitter — it needs to stop the scroll.

**Quick option:** Screenshot the title screen from the live site at 1200×630 resolution. The existing hero layout is designed for this.

### Demo GIF/Video (15-30 seconds)

Screen-record scrolling through the narrative. Key moments to capture:
- Hero title appearing over the dark Atlantic
- Camera swooping to Portugal (Chapter 1)
- Soil moisture map animating (Chapter 3, when wired)
- River discharge visualization (Chapter 5, when wired)
- Map unlocking for exploration (Chapter 9)

Use QuickTime screen recording → convert to MP4. LinkedIn supports native video; Twitter prefers short clips.

### README.md for GitHub

The repo should be public at launch. A strong README signals quality to DevSeed. Include: screenshot, one-paragraph description, tech stack list, data sources with attribution, "How to run locally" section (the script we just made), and a link to the methodology page.

## LinkedIn Post Drafts

### English (for DevSeed / international GIS audience)

```
Portugal has no national flood prediction system.

This winter, three storms in two weeks killed 11 people, displaced
thousands, and collapsed the country's main motorway. The soil was
already saturated from weeks of rain. The rivers were already high.
The data showed it coming.

I built cheias.pt — a scroll-driven narrative that tells the story
of what happened and why, using entirely open data:

→ Copernicus EMS flood extent polygons
→ ERA5-Land soil moisture via Open-Meteo
→ GloFAS river discharge
→ IPMA weather warnings

The stack: MapLibre GL JS, vanilla JavaScript, static deploy.
No backend, no API keys, no build tools.

The key insight: a precondition index combining soil saturation +
forecast rainfall + river discharge anomaly could have flagged the
crisis basins days before the first storm hit.

🌊 https://cheias.pt

Built as a civic tech project and portfolio piece. Inspired by
fogos.pt (Portugal's wildfire monitoring platform, 1M views/day)
and the scrollytelling methodology of Vizzuality and Development Seed.

#geospatial #MapLibre #Copernicus #OpenData #Portugal #floods
#scrollytelling #civictech
```

### Portuguese (for PT audience)

```
Portugal não tem um sistema nacional de previsão de cheias.

O SVARH observa. O EFAS europeu tem capacidade degradada para os
nossos rios regulados por barragens. Ninguém agrega os sinais —
humidade do solo, caudal dos rios, previsão de precipitação — para
dizer: "a vossa bacia está em risco."

Criei cheias.pt — uma narrativa visual sobre o que aconteceu entre
Janeiro e Fevereiro de 2026, contada com dados de satélite e modelos
hidrológicos públicos:

→ Solo progressivamente saturado desde Dezembro
→ Três tempestades em duas semanas (Kristin, Leonardo, Marta)
→ Rios que ultrapassaram limiares históricos
→ 69 municípios em calamidade

Os dados já sabiam. A pergunta é: da próxima vez, podemos
transformar este tipo de análise em aviso prévio?

🌊 https://cheias.pt

Projecto aberto, código público, dados públicos.
Inspirado pelo fogos.pt.

#cheias #Portugal #dadosabertos #protecçãocivil #geoespacial
```

## Direct Outreach Templates

### To Development Seed (LinkedIn DM)

```
Hi [name] — I've been following DevSeed's work on incendios.pt
and your geospatial storytelling projects. I built something in
the same vein for Portugal's ongoing flood crisis: cheias.pt

It's a scroll-driven narrative using MapLibre GL JS, Copernicus
EMS data, and Open-Meteo APIs — the same cloud-native geospatial
stack you work with. The core insight is a precondition index
(soil moisture + discharge + forecast rain) that could have
flagged the crisis basins before the storms hit.

Would love to get your take on it. I'm based in Lisbon and looking
to contribute to this kind of work professionally.

cheias.pt
```

### To fogos.pt / João Pina

```
Olá João — sou o Nelson, moro em Queluz e trabalho em geoespacial.
Inspirado pelo que fizeste com o fogos.pt, criei um projecto para
cheias: cheias.pt

É uma narrativa visual (scrollytelling) sobre a crise de Jan-Fev
2026 — o que aconteceu, porquê, e o que os dados já mostravam.
Usa dados abertos (Copernicus, Open-Meteo, IPMA) e MapLibre.

Gostava de ter a tua opinião. Se fizer sentido, o passo seguinte
seria evoluir de retrospectiva para monitorização em tempo real —
o equivalente do fogos.pt para cheias.

Abraço
```

## Deployment

**Simplest path:** Deploy to Vercel or Netlify from the GitHub repo. Both give preview URLs for testing before pointing the domain.

```bash
# Vercel (if you have it installed)
npx vercel --prod

# Or Netlify
npx netlify deploy --prod --dir=.
```

**Domain:** Point cheias.pt DNS to the deployment. Vercel and Netlify both support custom domains with automatic SSL.

**Alternative:** Deploy to lunasilvestre.systems if you want to keep everything on your server. Simple nginx config:

```nginx
server {
    server_name cheias.pt www.cheias.pt;
    root /var/www/cheias-pt;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Cache static assets
    location ~* \.(json|geojson|png|jpg|svg)$ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

## Pre-Launch Checklist

```
[ ] Chapters 0-5, 7-9 rendering with data
[ ] OG image created and referenced in index.html
[ ] GitHub repo public with README
[ ] Deployed to cheias.pt (SSL working)
[ ] Tested on Chrome, Firefox, Safari (desktop + mobile)
[ ] Demo GIF/video recorded
[ ] LinkedIn posts drafted and ready
[ ] Direct messages drafted for DevSeed contacts
[ ] Methodology page (/methodology) live, even if minimal
```

## Sequencing the Launch

1. **Day -1:** Deploy to cheias.pt. Test all links. Record demo video/GIF.
2. **Day 0 (Tuesday/Wednesday, morning PT):** Post Portuguese version on Twitter/X. Post English version on LinkedIn. Both with OG image + demo video.
3. **Day 0 (afternoon):** Send direct messages to DevSeed contacts, João Pina, and 2-3 journalists.
4. **Day +1:** Share on GIS communities (Mastodon, Reddit r/gis, GeoNet).
5. **Day +3:** Follow up on any DM responses.

## What If It Gets Traction?

If fogos.pt team or journalists pick it up, be ready with:
- A one-paragraph methodology explanation in Portuguese
- Source data links (all open, verifiable)
- The "Portugal has no national flood prediction system" framing
- A clear ask: "This should exist as a public service, not just a portfolio project"
