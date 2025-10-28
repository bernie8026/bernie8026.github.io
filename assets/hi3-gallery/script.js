
const el = (sel, root=document)=>root.querySelector(sel);
const IMG_BASE = (document.currentScript.dataset.imgBase || '/assets/hi3/characters/');
const JSON_URL = (document.currentScript.dataset.json || '/data/characters.json');

function slugToSrc(slug){
  const exts = ['webp','png','jpg','jpeg','avif'];
  return exts.map(ext => `${IMG_BASE}${slug}.${ext}`);
}

function createCard(c){
  const card = document.createElement('article');
  card.className = 'card';
  const img = document.createElement('img');
  img.className = 'thumb';
  img.alt = `${c.en} ${c.zh?"/ "+c.zh:""} | Honkai Impact 3rd`;
  img.loading = 'lazy';

  const sources = slugToSrc(c.slug);
  let idx = 0;
  const placeholder = '/assets/placeholder.png';
  const tryNext = () => {
    if(idx >= sources.length){ img.src = placeholder; return; }
    img.src = sources[idx++];
  };
  img.onerror = tryNext;
  tryNext();

  const meta = document.createElement('div'); meta.className = 'meta';
  const name = document.createElement('div'); name.className = 'name';
  name.innerHTML = `${c.en}${c.zh ? '<span class="zh">（'+c.zh+'）</span>' : ''}`;

  const tag = document.createElement('div'); tag.className = 'tag'; tag.textContent = 'Valkyrie';
  meta.appendChild(name); meta.appendChild(tag);
  card.appendChild(img); card.appendChild(meta);

  card.addEventListener('click', () => openLightbox(img.currentSrc || img.src, name.textContent));
  return card;
}

let LIGHTBOX;
function ensureLightbox(){
  if(LIGHTBOX) return;
  LIGHTBOX = document.createElement('dialog'); LIGHTBOX.className = 'lightbox';
  LIGHTBOX.innerHTML = `<img class="lb-img" alt=""><div class="hidden" id="lbCaption"></div>`;
  document.body.appendChild(LIGHTBOX);
  LIGHTBOX.addEventListener('click', (e)=>{ if(e.target === LIGHTBOX) LIGHTBOX.close(); })
  document.addEventListener('keydown', (e)=>{ if(e.key === 'Escape' && LIGHTBOX.open) LIGHTBOX.close(); })
}
function openLightbox(src, alt){
  ensureLightbox();
  const img = document.querySelector('.lb-img'); img.src = src; img.alt = alt;
  LIGHTBOX.showModal();
}

async function load(){
  const res = await fetch(JSON_URL).catch(()=>null);
  let list = [];
  if(res && res.ok){ list = await res.json(); }
  const grid = document.querySelector('#grid');
  const input = document.querySelector('#search');

  const normalize = s => (s||'').toLowerCase().replace(/\s+/g,'');
  const hay = list.map(c => ({...c, _h: normalize(c.en + (c.zh||'') + (c.slug||''))}));

  const render = (items)=>{
    grid.innerHTML='';
    const frag = document.createDocumentFragment();
    items.forEach(c => frag.appendChild(createCard(c)));
    grid.appendChild(frag);
  };
  render(hay);

  input.addEventListener('input', ()=>{
    const q = normalize(input.value);
    render( hay.filter(c => c._h.includes(q)) );
  });
}

document.addEventListener('DOMContentLoaded', load);
