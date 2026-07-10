const NODE_W = 200, NODE_H = 42;

// État
let scale = 0.48, tx = 60, ty = 40;
let dragging = false, lastMX, lastMY;
let selectedNode = null;
let highlightNodes = new Set();
let searchQuery = '';

// Multi-sélection ordonnée (le 1er cliché = ancre)
// tableau ordonné de noms de fichiers
let multiSel = [];

// Nœuds dont les liens sont masqués (Shift+clic sur nœud sélectionné)
const hiddenEdgeNodes = new Set();

function multiSelHas(f){ return multiSel.includes(f); }

function updateAlignBar(){
	const bar = document.getElementById('align-bar');
	document.getElementById('ab-count').textContent = multiSel.length;
	bar.classList.toggle('visible', multiSel.length >= 2);
}

function clearMultiSel(){
	multiSel = [];
	updateAlignBar();
	draw();
}

// ---- Mise en ligne ----
// Place tous les nœuds sélectionnés à partir de la position du 1er,
// espacés de (NODE_W|H + GAP) dans la direction choisie.
function lineUp(dir){
	if (multiSel.length < 2) return;
	// NODE_GAP_Y / NODE_GAP_X
	const GAP = 30;

	// Position absolue d'un nœud (base + offset groupe)
	function absPos(f){
		const base = positions[f];
		const g		= NODES_DATA[f]?.group;
		const off	= groupOffsets[g] || {dx:0, dy:0};
		return {x: base.x + off.dx, y: base.y + off.dy};
	}
	// Écrire position absolue dans positions[] (relatif à offset groupe)
	function setAbsPos(f, ax, ay){
		const g	 = NODES_DATA[f]?.group;
		const off = groupOffsets[g] || {dx:0, dy:0};
		positions[f].x = ax - off.dx;
		positions[f].y = ay - off.dy;
	}

	const anchor = absPos(multiSel[0]);
	const stepX	= dir==='right' ?	NODE_W + GAP : dir==='left' ? -(NODE_W + GAP) : 0;
	const stepY	= dir==='down'	?	NODE_H + GAP : dir==='up'	 ? -(NODE_H + GAP) : 0;

	multiSel.forEach((f, i) => {
		setAbsPos(f, anchor.x + i * stepX, anchor.y + i * stepY);
	});
	// Résoudre les chevauchements pour chaque nœud déplacé
	for (const f of multiSel) resolveOverlaps(f);
	draw();
}

// Positions des groupes (boîtes déplaçables)
// On calcule les groupes
const groups = {};
for (const [f, n] of Object.entries(NODES_DATA)) {
	if (!groups[n.group]) groups[n.group] = [];
	groups[n.group].push(f);
}
// .h en premier dans chaque groupe
for (const g of Object.keys(groups)) {
	groups[g].sort((a, b) => {
		const aH = a.endsWith('.h') ? 0 : 1;
		const bH = b.endsWith('.h') ? 0 : 1;
		if (aH !== bH) return aH - bH;
		return a.localeCompare(b);
	});
}

// ---- Légende <-> groupes (lien dynamique) ----
// Groupes actifs (visibles). Tous actifs par défaut.
const activeGroups = new Set(Object.keys(groups));
// Groupe survolé dans la légende (mise en avant temporaire)
let hoverGroup = null;

function toggleGroup(g) {
	if (activeGroups.has(g)) activeGroups.delete(g);
	else activeGroups.add(g);
	// Si le nœud sélectionné appartient à un groupe qu'on vient de masquer, on désélectionne
	if (selectedNode && NODES_DATA[selectedNode]?.group === g && !activeGroups.has(g)) {
		selectedNode = null; highlightNodes.clear(); closeSidePanel();
	}
	// Idem pour la multi-sélection
	if (!activeGroups.has(g) && multiSel.length) {
		multiSel = multiSel.filter(f => NODES_DATA[f]?.group !== g);
		updateAlignBar();
	}
	updateLegendUI();
	draw();
}

function setGroupHover(g) {
	if (hoverGroup === g) return;
	hoverGroup = g;
	draw();
}

function clearGroupHover() {
	if (hoverGroup === null) return;
	hoverGroup = null;
	draw();
}

function updateLegendUI() {
	document.querySelectorAll('#legend .leg[data-group]').forEach(row => {
		row.classList.toggle('inactive', !activeGroups.has(row.dataset.group));
	});
}

// Positions des nodes (modifiables par drag) — positions d'origine (INIT_POS)
const positions = {};
for (const [f, p] of Object.entries(INIT_POS)) positions[f] = {x:p.x, y:p.y};

// Compte des appels entrants (qui appelle ce fichier) — types call / calls_h
const incomingCallCount = {};
for (const f of Object.keys(NODES_DATA)) incomingCallCount[f] = 0;
for (const e of EDGES_DATA) {
	if (e.type==='call' || e.type==='calls_h') {
		incomingCallCount[e.tgt] = (incomingCallCount[e.tgt]||0) + 1;
	}
}

// Fichiers orphelins : aucun lien entrant ni sortant, quel que soit le type.
// Souvent un fichier mort, un point d'entrée non détecté, ou un nom mal résolu.
const orphanFiles = new Set();
for (const f of Object.keys(NODES_DATA)) {
	let hasAny = false;
	for (const e of EDGES_DATA) { if (e.src===f || e.tgt===f) { hasAny=true; break; } }
	if (!hasAny) orphanFiles.add(f);
}

// Offset de drag des groupes

// Offset de drag des groupes
const groupOffsets = {};
for (const g of Object.keys(groups)) groupOffsets[g] = {dx:0, dy:0};

// Drag state
// null | {type:'pan'} | {type:'node_drag',name} | {type:'group',name}
let dragState = null;
// direction du hint de grille en cours
let dragHintDir = null;

// Index edges
const nodeEdges = {};
for (const f of Object.keys(NODES_DATA)) nodeEdges[f] = {out:[],in:[]};
for (const e of EDGES_DATA) {
	if (nodeEdges[e.src]) nodeEdges[e.src].out.push(e);
	if (nodeEdges[e.tgt]) nodeEdges[e.tgt].in.push(e);
}

// ---- Panneau latéral (détails complets au clic) ----
const sidePanel = document.getElementById('side-panel');
const spTitle = document.getElementById('sp-title');
const spMeta = document.getElementById('sp-meta');
const spBody = document.getElementById('sp-body');

function fnTagList(fns) {
	if (!fns || !fns.length) return '';
	return `<div class="sp-fns">${fns.map(f=>`<span class="fn-tag">${f}</span>`).join('')}</div>`;
}

function sidePanelRow(otherFile, fns) {
	return `<div class="sp-row" onclick="selectNodeFromPanel('${otherFile.replace(/'/g,"\\'")}')">`
		+ `<div class="sp-file">${otherFile}</div>`
		+ fnTagList(fns)
		+ `</div>`;
}

function renderSidePanel(fname) {
	const n = NODES_DATA[fname];
	if (!n) return;
	const eout = nodeEdges[fname]?.out || [];
	const ein = nodeEdges[fname]?.in || [];

	spTitle.textContent = fname;
	spMeta.textContent = `Module: ${n.group} · ${n.funcs.length} fonctions · ${n.is_header?'Header .h':'Source .c'}`;
	if (hiddenEdgeNodes.has(fname)) {
		spMeta.innerHTML += `<br><span class="hidden-badge">⊘ Liens masqués · Shift+Clic pour réafficher</span>`;
	}
	if (orphanFiles.has(fname)) {
		spMeta.innerHTML += `<br><span style="color:#c04040;font-size:9.5px;">⚠ Orphelin — aucun lien détecté</span>`;
	}

	// Appelé par (qui appelle ce fichier)
	const calledBy = ein.filter(e=>e.type==='call'||e.type==='calls_h');
	// Ce qu'il appelle
	const callsOut = eout.filter(e=>e.type==='call'||e.type==='calls_h');
	// Ses includes (.c→.h ou .h→.h)
	const includesOut = eout.filter(e=>e.type==='include'||e.type==='h_includes_h');
	// Qui l'inclut
	const includedBy = ein.filter(e=>e.type==='include'||e.type==='h_includes_h');

	function section(title, edges, sideKey) {
		const cnt = edges.length;
		let h = `<div class="sp-section"><h4>${title} <span class="cnt">${cnt}</span></h4>`;
		if (!cnt) { h += `<div class="sp-empty">Aucun</div></div>`; return h; }
		for (const e of edges) {
			const other = sideKey==='src' ? e.src : e.tgt;
			h += sidePanelRow(other, e.fns);
		}
		h += `</div>`;
		return h;
	}

	let html = '';
	html += section('← Appelé par', calledBy, 'src');
	html += section('→ Appelle', callsOut, 'tgt');
	html += section('⤵ Inclut', includesOut, 'tgt');
	html += section('⤴ Inclus par', includedBy, 'src');

	spBody.innerHTML = html;

	const wasOpen = sidePanel.classList.contains('open');
	sidePanel.classList.add('open');
	container.classList.add('panel-open');
	updatePanelTop();
	// Si le panel était déjà ouvert, redessiner immédiatement (pas d'animation)
	if (wasOpen) { resize(); draw(); }
	// Sinon, le ResizeObserver prend le relais pendant la transition
}

function closeSidePanel() {
	sidePanel.classList.remove('open');
	container.classList.remove('panel-open');
	selectedNode = null; highlightNodes.clear();
	// Le ResizeObserver redessine en continu pendant la transition
	draw();
}

function selectNodeFromPanel(fname) {
	selectedNode = fname;
	highlightNodes.clear();
	for (const edge of EDGES_DATA) {
		if (edge.src===selectedNode) highlightNodes.add(edge.tgt);
		if (edge.tgt===selectedNode) highlightNodes.add(edge.src);
	}
	renderSidePanel(fname);
	draw();
}

const canvas = document.getElementById('cv');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

function resize() {
	const dpr = devicePixelRatio;
	canvas.width	= canvas.offsetWidth	* dpr;
	canvas.height = canvas.offsetHeight * dpr;
	ctx.scale(dpr, dpr);
	updatePanelTop();
	draw();
}
window.addEventListener('resize', resize);

function updatePanelTop() {
	const header   = document.getElementById('header');
	const controls = document.getElementById('controls');
	const top = (header   ? header.getBoundingClientRect().bottom   : 0)
	          + (controls ? controls.getBoundingClientRect().height  : 0);
	// On prend la position bottom du controls directement
	const bottom = controls ? controls.getBoundingClientRect().bottom : header.getBoundingClientRect().bottom;
	sidePanel.style.top = bottom + 'px';
}

// ---- Helpers ----
function nodePos(fname) {
	const base = positions[fname];
	const g = NODES_DATA[fname]?.group;
	const off = groupOffsets[g] || {dx:0,dy:0};
	return {x: base.x + off.dx, y: base.y + off.dy};
}

function getGroupBounds(gname) {
	let x1=Infinity,y1=Infinity,x2=-Infinity,y2=-Infinity;
	for (const f of (groups[gname]||[])) {
		const p = nodePos(f);
		x1=Math.min(x1,p.x-10); y1=Math.min(y1,p.y-26);
		x2=Math.max(x2,p.x+NODE_W+10); y2=Math.max(y2,p.y+NODE_H+10);
	}
	return {x1,y1,x2,y2};
}

function screenToWorld(sx,sy) { return [(sx-tx)/scale,(sy-ty)/scale]; }
function worldToScreen(wx,wy) { return [wx*scale+tx,wy*scale+ty]; }

function getGroupColors(g) { return COLORS[g]||COLORS['other']; }

// Construit la légende dynamiquement à partir de COLORS (nombre de groupes variable selon le projet)
function applyProjectMeta() {
	if (typeof PROJECT_TITLE !== 'undefined') {
		document.title = PROJECT_TITLE;
		const h1 = document.getElementById('proj-title');
		if (h1) h1.textContent = '🔗 ' + PROJECT_TITLE + ' — Carte des dépendances';
	}
	if (typeof PROJECT_SUBTITLE !== 'undefined') {
		const p = document.getElementById('proj-subtitle');
		if (p) p.textContent = PROJECT_SUBTITLE;
	}
}

function buildLegend() {
	const el = document.getElementById('legend');
	if (!el) return;
	el.innerHTML = '';
	const groupsPresent = new Set(Object.values(NODES_DATA).map(n => n.group));
	const order = Object.keys(COLORS).filter(g => g !== 'other' && groupsPresent.has(g));
	for (const g of order) {
		const c = COLORS[g];
		const n = (groups[g] || []).length;
		const row = document.createElement('div');
		row.className = 'leg' + (activeGroups.has(g) ? '' : ' inactive');
		row.dataset.group = g;
		row.title = `${n} fichier${n>1?'s':''} · clic pour afficher/masquer le module`;
		row.innerHTML = `<div class="leg-dot" style="background:${c.bg};border:1px solid ${c.border}"></div><span>${g}</span>`;
		row.addEventListener('click', () => toggleGroup(g));
		row.addEventListener('mouseenter', () => setGroupHover(g));
		row.addEventListener('mouseleave', () => clearGroupHover());
		el.appendChild(row);
	}
}

// ---- DRAW ----
function drawArrow(x1,y1,x2,y2,color,width,dashed,label,alpha=1,bowSeed) {
	if (alpha < 0.01) return;
	const dx=x2-x1,dy=y2-y1,len=Math.sqrt(dx*dx+dy*dy);
	if (len<2) return;
	ctx.save();
	ctx.globalAlpha = alpha;
	ctx.strokeStyle = color;
	ctx.lineWidth = width;
	ctx.lineCap = 'round';
	if (dashed) ctx.setLineDash([5,3]);
	else ctx.setLineDash([]);
	if (!dashed && alpha > 0.7) {
		ctx.shadowColor = color;
		ctx.shadowBlur = 6 * alpha;
	}

	// ── 1) Place la flèche : taille et angle, calculés en premier ───────────
	// Trait court → ligne droite (une courbe serait inutile et inesthétique).
	// Trait long → courbe, avec une magnitude propre à chaque arête (bowSeed)
	// pour qu'aucun lien ne suive exactement le même tracé qu'un autre.
	const NEAR=90, FAR=220;
	const fullBow = bowSeed!==undefined ? bowSeed : 14;
	let bow = 0;
	if (len>NEAR) bow = fullBow * Math.min(1,(len-NEAR)/(FAR-NEAR));

	const mx=(x1+x2)/2, my=(y1+y2)/2;
	const px=-dy/len*bow, py=dx/len*bow;
	const cx=mx+px, cy=my+py;

	// Angle d'arrivée : direction droite si pas de courbe, tangente de la
	// courbe sinon — c'est l'angle final de la flèche, fixé dès le départ.
	const ang = bow===0
		? Math.atan2(dy,dx)
		: Math.atan2(2*(cy-y1)+2*(y2-cy), 2*(cx-x1)+2*(x2-cx));

	const as = 7 + Math.min(width, 2.5)*1.4;

	// ── 2) Point de jonction exact : milieu de la base du triangle ──────────
	// (les deux coins arrière sont symétriques autour de `ang`, donc leur
	// milieu = tip - as*cos(0.42)*direction(ang) — un point du triangle).
	const backDist = as*Math.cos(0.42);
	const lx = x2 - backDist*Math.cos(ang);
	const ly = y2 - backDist*Math.sin(ang);

	// ── 3) Trace le trait — droit ou courbé — jusqu'à ce point de contact ──
	ctx.beginPath();
	ctx.moveTo(x1,y1);
	if (bow===0) ctx.lineTo(lx,ly);
	else ctx.quadraticCurveTo(cx,cy,lx,ly);
	ctx.stroke();
	ctx.shadowBlur = 0;

	// ── 4) Dessine la flèche, exactement à l'endroit où le trait s'arrête ──
	ctx.fillStyle=color;
	ctx.setLineDash([]);
	ctx.beginPath();
	ctx.moveTo(x2,y2);
	ctx.lineTo(x2-as*Math.cos(ang-0.42),y2-as*Math.sin(ang-0.42));
	ctx.lineTo(x2-as*Math.cos(ang+0.42),y2-as*Math.sin(ang+0.42));
	ctx.closePath();
	ctx.fill();
	// Fin contour sombre : permet de distinguer les triangles entre eux
	// quand plusieurs flèches se superposent au même endroit.
	ctx.lineWidth = 1;
	ctx.strokeStyle = '#080812';
	ctx.globalAlpha = Math.min(1, alpha + 0.3);
	ctx.stroke();

	// Label count
	if (label && scale>0.45) {
		ctx.fillStyle='#aab8';
		ctx.font=`${Math.max(7,8*scale)}px monospace`;
		ctx.textAlign='center';
		ctx.fillText(label, mx+px*0.5, my+py*0.5-2);
	}
	ctx.restore();
}

// Trouve le point d'intersection entre le centre d'un rectangle (cx,cy,w,h)
// et un rayon partant vers (dirx,diry) — attache l'arête exactement sur le bord
// (haut/bas/gauche/droite) au lieu d'un simple décalage circulaire qui pouvait
// déborder des coins du nœud.
function rectBorderPoint(cx,cy,w,h,dirx,diry) {
	const hw=w/2, hh=h/2;
	if (dirx===0 && diry===0) return {x:cx,y:cy};
	const scaleX = dirx!==0 ? hw/Math.abs(dirx) : Infinity;
	const scaleY = diry!==0 ? hh/Math.abs(diry) : Infinity;
	const k = Math.min(scaleX,scaleY);
	return {x:cx+dirx*k, y:cy+diry*k};
}

function hashStr(s) {
	let h=0;
	for (let i=0;i<s.length;i++) h=((h<<5)-h+s.charCodeAt(i))|0;
	return h;
}

function edgePts(e) {
	const s = NODES_DATA[e.src], t = NODES_DATA[e.tgt];
	if (!s||!t) return null;
	const sp = nodePos(e.src), tp = nodePos(e.tgt);
	const sx=sp.x+NODE_W/2, sy=sp.y+NODE_H/2;
	const tx2=tp.x+NODE_W/2, ty2=tp.y+NODE_H/2;
	const dx=tx2-sx,dy=ty2-sy,len=Math.sqrt(dx*dx+dy*dy)||1;
	const ux=dx/len, uy=dy/len;
	// Petit espace pour ne pas coller pile sur le bord du nœud
	const desiredOffs=6;
	const p1 = rectBorderPoint(sx,sy,NODE_W+4,NODE_H+4,ux,uy);
	const p2 = rectBorderPoint(tx2,ty2,NODE_W+4,NODE_H+4,-ux,-uy);

	// Quand les boîtes sont collées (ou presque), l'écart fixe peut faire
	// dépasser le point de départ par rapport au point d'arrivée, ce qui
	// inverse visuellement le sens de la flèche. On limite donc l'écart à la
	// moitié de l'espace réellement disponible entre les deux bords.
	const rawLen = Math.hypot(p2.x-p1.x, p2.y-p1.y);
	const offs = Math.min(desiredOffs, Math.max(0, rawLen/2 - 1));

	return {
		x1:p1.x+ux*offs, y1:p1.y+uy*offs,
		x2:p2.x-ux*offs, y2:p2.y-uy*offs,
	};
}

// ── Détection et résolution de chevauchements en cascade ─────────────────────
// Tourne sur TOUS les nœuds du groupe en plusieurs passes, propageant en cascade.
const NODE_GAP = 30;

function resolveOverlaps(movedFile) {
	const g = NODES_DATA[movedFile]?.group;
	if (!g) return;
	resolveGroupOverlaps(g, movedFile);
}

function resolveGroupOverlaps(g, pinnedFile) {
	const files = groups[g] || [];
	if (files.length < 2) return;

	const MAX_PASSES = 20;
	for (let pass = 0; pass < MAX_PASSES; pass++) {
		let anyMoved = false;
		for (let i = 0; i < files.length; i++) {
			for (let j = i + 1; j < files.length; j++) {
				const fa = files[i], fb = files[j];
				const pa = positions[fa], pb = positions[fb];
				const overlapX = (NODE_W + NODE_GAP) - Math.abs(pb.x - pa.x);
				const overlapY = (NODE_H + NODE_GAP) - Math.abs(pb.y - pa.y);
				if (overlapX <= 0 || overlapY <= 0) continue;

				const aPin = (fa === pinnedFile), bPin = (fb === pinnedFile);

				if (overlapX < overlapY) {
					// Séparation horizontale
					// Décider dans quel sens pousser : pb va dans la direction où il est déjà par rapport à pa
					// Si parfaitement alignés (dx==0) on pousse à droite par défaut
					const dx = pb.x - pa.x;
					// pb est à droite (ou aligné) → on le pousse encore à droite
					const pushRight = dx >= 0;
					const targetB = pa.x + (pushRight ? 1 : -1) * (NODE_W + NODE_GAP);
					const targetA = pb.x + (pushRight ? -1 : 1) * (NODE_W + NODE_GAP);
					if (aPin)	  { pb.x = targetB; }
					else if (bPin) { pa.x = targetA; }
					else		   { pb.x = targetB; }
				} else {
					// Séparation verticale
					const dy = pb.y - pa.y;
					const pushDown = dy >= 0;
					const targetB = pa.y + (pushDown ? 1 : -1) * (NODE_H + NODE_GAP);
					const targetA = pb.y + (pushDown ? -1 : 1) * (NODE_H + NODE_GAP);
					if (aPin)	  { pb.y = targetB; }
					else if (bPin) { pa.y = targetA; }
					else		   { pb.y = targetB; }
				}
				anyMoved = true;
			}
		}
		if (!anyMoved) break;
	}
}

const activeEdgeTypes = new Set(['include','call','calls_h','implements','h_includes_h']);
function toggleEdgeType(t){
	if (activeEdgeTypes.has(t)) activeEdgeTypes.delete(t);
	else activeEdgeTypes.add(t);
	const el = document.querySelector(`.el[data-etype="${t}"]`);
	if (el) el.classList.toggle('active', activeEdgeTypes.has(t));
	draw();
}
function getVisibleEdges() {
	return EDGES_DATA.filter(e=>activeEdgeTypes.has(e.type));
}

function edgeStyle(e) {
	if (e.type==='call')				return {color:'#ffcc55',w:1.4+Math.min(e.count*0.15,2),dash:false,label:null};
	if (e.type==='include')		 return {color:'#6699ff',w:1.1,dash:true,label:null};
	if (e.type==='calls_h')		 return {color:'#ff88aa',w:1.5,dash:false,label:null};
	if (e.type==='implements')	return {color:'#44ee99',w:1.8,dash:false,label:null};
	if (e.type==='h_includes_h')return {color:'#bb99ff',w:1.1,dash:true,label:null};
	return {color:'#888',w:0.8,dash:false,label:null};
}

function draw() {
	const W=canvas.offsetWidth, H=canvas.offsetHeight;
	ctx.clearRect(0,0,W,H);
	ctx.fillStyle='#080812';
	ctx.fillRect(0,0,W,H);

	// Grille de fond
	if (scale>0.2) {
		ctx.strokeStyle='#0e0e22';
		ctx.lineWidth=0.5;
		const gs=100*scale, ox=tx%gs, oy=ty%gs;
		for (let x=ox;x<W;x+=gs){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
		for (let y=oy;y<H;y+=gs){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
	}

	ctx.save();
	ctx.translate(tx,ty);
	ctx.scale(scale,scale);

	// ---- Boîtes de groupes (fond) ----
	for (const [gname, fnames] of Object.entries(groups)) {
		const b = getGroupBounds(gname);
		const c = getGroupColors(gname);
		const gActive = activeGroups.has(gname);
		const gHover	= hoverGroup === gname;
		// Coefficient global lié à la légende : estompé si masqué, renforcé si survolé
		const mul = gActive ? (gHover ? 1.6 : 1) : 0.18;
		ctx.save();
		// Fond très transparent
		ctx.globalAlpha=0.06*mul;
		ctx.fillStyle=c.bg;
		roundRect(b.x1,b.y1,b.x2-b.x1,b.y2-b.y1,14);
		ctx.fill();
		// Bordure dashed (pleine si survolée)
		ctx.globalAlpha=Math.min(1,0.4*mul);
		ctx.strokeStyle=c.border;
		ctx.lineWidth=gHover?2.2:1.5;
		if (!gHover) ctx.setLineDash([5,4]);
		roundRect(b.x1,b.y1,b.x2-b.x1,b.y2-b.y1,14);
		ctx.stroke();
		ctx.setLineDash([]);
		// Label groupe
		ctx.globalAlpha=Math.min(1,0.75*mul);
		ctx.fillStyle=c.border;
		ctx.font='bold 12px Segoe UI,sans-serif';
		ctx.textAlign='left';
		ctx.fillText('Module '+gname+(gActive?'':' (masqué)'), b.x1+12, b.y1+16);
		ctx.restore();

		// Icône drag (petit ✥ en haut à droite)
		if (scale>0.3 && gActive) {
			ctx.save();
			ctx.globalAlpha=0.4;
			ctx.fillStyle=c.border;
			ctx.font='13px sans-serif';
			ctx.textAlign='right';
			ctx.fillText('⠿', b.x2-8, b.y1+15);
			ctx.restore();
		}
	}

	// ---- Hint grille (case de snap au drop) ----
	if (dragState && dragState.type==='node_drag' && dragging) {
		drawGridHint(dragState.name);
	}

	// ---- Arêtes ----
	const visEdges = getVisibleEdges();
	for (const e of visEdges) {
		// Masquer si l'un des bouts est dans hiddenEdgeNodes
		if (hiddenEdgeNodes.has(e.src) || hiddenEdgeNodes.has(e.tgt)) continue;
		const pts = edgePts(e);
		if (!pts) continue;
		const st = edgeStyle(e);
		// Détecter si l'arête est intra-groupe
		const srcGroup = NODES_DATA[e.src]?.group;
		const tgtGroup = NODES_DATA[e.tgt]?.group;
		const isIntraGroup = (srcGroup && tgtGroup && srcGroup === tgtGroup);
		// Un des deux groupes masqué depuis la légende → on ignore complètement l'arête
		if (!activeGroups.has(srcGroup) || !activeGroups.has(tgtGroup)) continue;
		let alpha, dash, overrideWidth;
		if (selectedNode) {
			// Sélection simple : focus sur le nœud sélectionné
			const connected = (e.src === selectedNode || e.tgt === selectedNode);
			alpha = connected ? 1 : 0;
			dash = !connected;
		} else if (multiSel.length > 0) {
			// Multi-sélection : aucun lien affiché
			alpha = 0;
		} else {
			alpha = isIntraGroup ? 0.18 : 0.3;
			dash = true;
		}
		// Groupe survolé dans la légende → estompe les liens qui n'y touchent pas
		if (hoverGroup && srcGroup !== hoverGroup && tgtGroup !== hoverGroup) alpha *= 0.15;
		// 8..20, varie par arête
		const bowSeed = 8 + (Math.abs(hashStr(e.src+'>'+e.tgt+'b'+e.type))%13);
		drawArrow(pts.x1, pts.y1, pts.x2, pts.y2, st.color, overrideWidth || st.w, dash, st.label, alpha, bowSeed);
	}

	// ---- Noeuds ----
	const allNodes = Object.keys(NODES_DATA);
	// Trier: .h au-dessus (dessinés après donc visibles)
	const sorted = [...allNodes].sort((a,b) => {
		const ah=a.endsWith('.h'), bh=b.endsWith('.h');
		return ah===bh ? 0 : (ah?1:-1);
	});

	for (const fname of sorted) {
		const n = NODES_DATA[fname];
		const p = nodePos(fname);
		const c = getGroupColors(n.group);
		const isSel	 = fname===selectedNode;
		const isHi		= highlightNodes.has(fname)||isSel;
		const isSrch	= searchQuery && fname.toLowerCase().includes(searchQuery.toLowerCase());
		const multiIdx= multiSel.indexOf(fname);
		const isMulti = multiIdx !== -1;
		const groupHidden	 = !activeGroups.has(n.group);
		const groupUnfocused = hoverGroup && n.group !== hoverGroup;
		const dimmed	= (selectedNode && !isHi && !isMulti) ||
										(multiSel.length>0 && !isMulti) ||
										groupHidden || groupUnfocused;
		const isH		 = fname.endsWith('.h');

		const isHidden = hiddenEdgeNodes.has(fname);
		ctx.save();
		ctx.globalAlpha = dimmed ? 0.09 : 1;

		if (isMulti){ ctx.shadowColor='#44aaff'; ctx.shadowBlur=18; }
		else if (isSel||isSrch){ ctx.shadowColor=isSrch?'#ffdd44':c.border; ctx.shadowBlur=16; }
		else if (isHidden){ ctx.shadowColor='#cc3060'; ctx.shadowBlur=12; }

		// Fond noeud
		const isOrphan = orphanFiles.has(fname);
		roundRect(p.x,p.y,NODE_W,NODE_H,7);
		ctx.fillStyle = isMulti ? (multiIdx===0?'#0c2240':'#0e1e3a')
														 : (isSel?'#12183a':(isHidden?'#1e0a14':(isSrch?'#221800':'#0f0f22')));
		ctx.fill();
		ctx.strokeStyle = isMulti ? (multiIdx===0?'#88ddff':'#44aaff')
															 : (isSrch?'#ffdd44':(isSel?'#6aa8e8':(isHidden?'#cc3060':(isOrphan?'#aa3333':c.border))));
		ctx.lineWidth	 = isMulti||isSel||isSrch||isHidden ? 2 : (isOrphan?1.5:0.8);
		if (isMulti) ctx.setLineDash([4,3]);
		else if (isOrphan && !isSel && !isSrch && !isHidden) ctx.setLineDash([3,2]);
		ctx.stroke();
		ctx.setLineDash([]);
		ctx.shadowBlur	= 0;

		// Barre latérale couleur
		ctx.globalAlpha = dimmed ? 0.15 : 0.88;
		ctx.fillStyle = isHidden ? '#cc3060' : c.border;
		ctx.fillRect(p.x, p.y+4, isH?4:3, NODE_H-8);
		ctx.globalAlpha = dimmed ? 0.12 : 1;

		// Icône type
		ctx.font='9px monospace';
		ctx.fillStyle = isHidden ? '#ee5588' : c.border;
		ctx.textAlign='left';
		ctx.textBaseline='middle';
		ctx.fillText(isHidden?'⊘':(isH?'◇':'◆'), p.x+8, p.y+NODE_H/2);

		// Nom fichier
		ctx.font=`${isSel||isHidden?'bold ':''}${isH?'italic ':''}10.5px 'Cascadia Code','Fira Code','Segoe UI',monospace`;
		ctx.fillStyle=isSrch?'#ffdd44':(isSel?'#e0f0ff':(isHidden?'#ee8aaa':'#bbc'));
		ctx.fillText(fname, p.x+20, p.y+NODE_H/2);

		// Badge numéro multi-sélection
		if (isMulti) {
			const r = 9;
			const bx = p.x + r + 2, by = p.y - r + 5;
			ctx.fillStyle = multiIdx===0 ? '#88ddff' : '#44aaff';
			ctx.beginPath(); ctx.arc(bx, by, r, 0, Math.PI*2); ctx.fill();
			ctx.fillStyle = '#001833';
			ctx.font = `bold ${r<9?7:8}px sans-serif`;
			ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
			ctx.fillText(multiIdx===0 ? '★' : String(multiIdx+1), bx, by+0.5);
		}

		// Badge fonctions (retiré sur demande)

		ctx.restore();
	}

	ctx.restore();

}

function roundRect(x,y,w,h,r) {
	ctx.beginPath();
	ctx.moveTo(x+r,y);ctx.lineTo(x+w-r,y);
	ctx.quadraticCurveTo(x+w,y,x+w,y+r);
	ctx.lineTo(x+w,y+h-r);
	ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
	ctx.lineTo(x+r,y+h);
	ctx.quadraticCurveTo(x,y+h,x,y+h-r);
	ctx.lineTo(x,y+r);
	ctx.quadraticCurveTo(x,y,x+r,y);
	ctx.closePath();
}

// ---- HIT TESTS ----
function getNodeAt(sx,sy) {
	const [wx,wy]=screenToWorld(sx,sy);
	// Tester dans l'ordre inverse (.h en dernier = priorité)
	const allFiles = Object.keys(NODES_DATA);
	const sorted = [...allFiles].sort((a,b)=>{
		const ah=a.endsWith('.h'),bh=b.endsWith('.h');
		return ah===bh?0:(ah?1:-1);
	}).reverse();
	for (const f of sorted) {
		if (!activeGroups.has(NODES_DATA[f]?.group)) continue;
		const p=nodePos(f);
		if (wx>=p.x&&wx<=p.x+NODE_W&&wy>=p.y&&wy<=p.y+NODE_H) return f;
	}
	return null;
}

function getGroupAt(sx,sy) {
	const [wx,wy]=screenToWorld(sx,sy);
	for (const gname of Object.keys(groups)) {
		const b=getGroupBounds(gname);
		// Clic dans la bande titre seulement (haut de la boîte)
		if (wx>=b.x1&&wx<=b.x2&&wy>=b.y1&&wy<=b.y1+22) return gname;
	}
	return null;
}


// ════════════════════════════════════════════════════════════════════════════
// GRILLE DISCRÈTE — déplacement case par case
// ════════════════════════════════════════════════════════════════════════════
// Pas de la grille (doit coïncider avec l'espacement initial des nœuds)
// 230
const GRID_X = NODE_W + NODE_GAP;
// 72
const GRID_Y = NODE_H + NODE_GAP;

// Retourne la cellule de grille (col, row) d'un nœud, en coordonnées
// RELATIVES au groupe (on soustrait l'offset du groupe).
function nodeCell(fname) {
	const g   = NODES_DATA[fname]?.group;
	const off = groupOffsets[g] || {dx:0, dy:0};
	// position sans offset
	const p   = positions[fname];
	return {
		col: Math.round(p.x / GRID_X),
		row: Math.round(p.y / GRID_Y),
	};
}

// Récupère le nœud occupant la cellule (col, row) dans le groupe g, ou null.
// excludeFile : ignorer ce fichier dans la recherche (le nœud en cours de drag)
function nodeAtCell(g, col, row, excludeFile) {
	for (const f of (groups[g] || [])) {
		if (f === excludeFile) continue;
		const c = nodeCell(f);
		if (c.col === col && c.row === row) return f;
	}
	return null;
}

// Trouve la case libre la plus proche de la position actuelle du nœud fname.
// Retourne {col, row} ou null si aucune case libre dans un rayon raisonnable.
function nearestFreeCell(fname) {
	const g   = NODES_DATA[fname]?.group;
	const p   = positions[fname];
	// Case "idéale" en coordonnées RELATIVES au groupe (comme nodeCell/nodeAtCell,
	// et comme snapToNearestFree/drawGridHint qui rajoutent l'offset séparément
	// ensuite). p.x/p.y sont déjà "sans offset" pendant le drag (voir mousemove :
	// positions[...].x = wx - NODE_W/2 - off.dx). Ne PAS rajouter off.dx/off.dy
	// ici, sinon l'offset du groupe est compté deux fois et le nœud est snappé
	// loin de sa position réelle dès que le module a été déplacé hors grille.
	const idealCol = Math.round(p.x / GRID_X);
	const idealRow = Math.round(p.y / GRID_Y);

	// Chercher en spirale la case libre la plus proche
	const MAX_R = 8;
	let best = null, bestDist = Infinity;
	for (let r = 0; r <= MAX_R; r++) {
		for (let dc = -r; dc <= r; dc++) {
			for (let dr = -r; dr <= r; dr++) {
				// périmètre seulement
				if (Math.abs(dc) !== r && Math.abs(dr) !== r) continue;
				const tc = idealCol + dc, tr = idealRow + dr;
				if (!nodeAtCell(g, tc, tr, fname)) {
					const dist = dc*dc + dr*dr;
					if (dist < bestDist) { bestDist=dist; best={col:tc,row:tr}; }
				}
			}
		}
		// on ne trouvera rien de mieux
		if (best && bestDist <= r*r) break;
	}
	// {col,row} ou null
	return best;
}

// Snape le nœud fname sur la case libre la plus proche.
// Retourne true si réussi, false si aucune case disponible.
function snapToNearestFree(fname) {
	const cell = nearestFreeCell(fname);
	if (!cell) return false;
	positions[fname].x = cell.col * GRID_X;
	positions[fname].y = cell.row * GRID_Y;
	return true;
}

// Indicateur visuel : surbrillance de la case cible pendant le drag
function drawGridHint(fname) {
	if (!fname) return;
	const cell = nearestFreeCell(fname);
	if (!cell) return;
	const g   = NODES_DATA[fname]?.group;
	const off = groupOffsets[g] || {dx:0, dy:0};
	const wx  = cell.col * GRID_X + off.dx;
	const wy  = cell.row * GRID_Y + off.dy;

	// Vérifier si c'est la case actuelle (pas de déplacement)
	const cur = nodeCell(fname);
	const same = (cell.col === cur.col && cell.row === cur.row);

	ctx.save();
	ctx.globalAlpha = same ? 0.1 : 0.22;
	ctx.fillStyle   = same ? '#888888' : '#44aaff';
	roundRect(wx, wy, NODE_W, NODE_H, 7);
	ctx.fill();
	ctx.globalAlpha = same ? 0.3 : 0.7;
	ctx.strokeStyle = same ? '#aaaaaa' : '#66ccff';
	ctx.lineWidth   = 1.5;
	ctx.setLineDash([4, 3]);
	roundRect(wx, wy, NODE_W, NODE_H, 7);
	ctx.stroke();
	ctx.setLineDash([]);
	ctx.restore();
}
// ---- EVENTS ----
const container=document.getElementById('canvas-container');

container.addEventListener('wheel',e=>{
	e.preventDefault();
	const rect=container.getBoundingClientRect();
	const mx=e.clientX-rect.left,my=e.clientY-rect.top;
	const d=e.deltaY<0?1.12:0.88;
	tx=mx-(mx-tx)*d; ty=my-(my-ty)*d;
	scale=Math.max(0.08,Math.min(5,scale*d));
	draw();
},{passive:false});

container.addEventListener('mousedown',e=>{
	const rect=container.getBoundingClientRect();
	const sx=e.clientX-rect.left, sy=e.clientY-rect.top;
	lastMX=e.clientX; lastMY=e.clientY;

	const fname=getNodeAt(sx,sy);
	const gname=fname?null:getGroupAt(sx,sy);

	if (e.shiftKey) {
		// Shift → sélection uniquement, pas de drag
		dragState={type:'shift_sel', fname};
	} else if (fname) {
		// Clic sur nœud : on prépare le drag libre
		const g   = NODES_DATA[fname]?.group;
		const off = groupOffsets[g] || {dx:0, dy:0};
		dragState={type:'node_drag', name:fname, startSX:sx, startSY:sy,
		           originX:positions[fname].x, originY:positions[fname].y};
		canvas.classList.add('grabbing');
	} else if (gname) {
		dragState={type:'group',name:gname};
		canvas.classList.add('grab-group');
	} else {
		dragState={type:'pan'};
		canvas.classList.add('grabbing');
	}
	dragging=false;
});

window.addEventListener('keydown',e=>{
	if (e.key==='Escape') {
		if (multiSel.length>0) { multiSel=[]; updateAlignBar(); }
		closeSidePanel();
	}
});

window.addEventListener('mousemove',e=>{
	if (!dragState) return;
	const dx=e.clientX-lastMX, dy=e.clientY-lastMY;
	if (Math.abs(dx)+Math.abs(dy)>3) dragging=true;

	if (dragState.type==='node_drag') {
		const rect2 = container.getBoundingClientRect();
		const [wx, wy] = screenToWorld(e.clientX - rect2.left, e.clientY - rect2.top);
		// Le nœud suit le curseur librement (centré sur le curseur)
		const g   = NODES_DATA[dragState.name]?.group;
		const off = groupOffsets[g] || {dx:0, dy:0};
		positions[dragState.name].x = wx - NODE_W/2 - off.dx;
		positions[dragState.name].y = wy - NODE_H/2 - off.dy;
		// Case la plus proche libre → hint
		dragHintDir = nearestFreeCell(dragState.name);
		draw();
	}

	if (dragState.type==='shift_sel') {
		// Shift maintenu + mouvement → lasso
		if (dragging) {
			dragState={type:'lasso'};
			selectedNode=null; highlightNodes.clear();
			sidePanel.classList.remove('open'); container.classList.remove('panel-open');
			canvas.style.cursor='crosshair';
		}
	} else if (dragState.type==='lasso') {
		const rect=container.getBoundingClientRect();
		const sx=e.clientX-rect.left, sy=e.clientY-rect.top;
		const fname=getNodeAt(sx,sy);
		if (fname && !multiSelHas(fname)) {
			multiSel.push(fname);
			updateAlignBar();
			draw();
		}
	} else if (dragState.type==='pan') {
		tx+=dx; ty+=dy;
	} else if (dragState.type==='group' && dragging) {
		groupOffsets[dragState.name].dx+=dx/scale;
		groupOffsets[dragState.name].dy+=dy/scale;
	}
	lastMX=e.clientX; lastMY=e.clientY;
	draw();
	updateHover(e);
});

window.addEventListener('mouseup',e=>{
	if (!dragState) return;

	if (dragState.type==='lasso') {
		canvas.style.cursor='';
		dragState=null; dragging=false;
		return;
	}

	if (dragState.type==='node_drag') {
		const fname = dragState.name;
		if (dragging) {
			// Drag réel → snapper sur la case libre la plus proche
			const snapped = snapToNearestFree(fname);
			if (!snapped) {
				// Aucune case libre → retour à la position d'origine
				positions[fname].x = dragState.originX;
				positions[fname].y = dragState.originY;
			}
		} else {
			// Simple clic → sélection
			positions[fname].x = dragState.originX;
			positions[fname].y = dragState.originY;
			if (multiSel.length > 0) { multiSel = []; updateAlignBar(); }
			selectedNode = (fname===selectedNode) ? null : fname;
			highlightNodes.clear();
			if (selectedNode) {
				for (const edge of EDGES_DATA) {
					if (edge.src===selectedNode) highlightNodes.add(edge.tgt);
					if (edge.tgt===selectedNode) highlightNodes.add(edge.src);
				}
				renderSidePanel(selectedNode);
			} else {
				closeSidePanel();
			}
		}
		dragHintDir = null;
		canvas.classList.remove('grabbing','grab-group');
		dragState=null; dragging=false;
		draw();
		return;
	}

	if (dragState.type==='shift_sel') {
		// Shift+clic sans drag
		const rect=container.getBoundingClientRect();
		const sx=e.clientX-rect.left, sy=e.clientY-rect.top;
		const fname=getNodeAt(sx,sy);
		if (fname) {
			// Si un nœud était sélectionné seul, il devient l'ancre (multiSel[0])
			if (selectedNode && multiSel.length === 0) {
				multiSel = [selectedNode];
				selectedNode = null; highlightNodes.clear();
				sidePanel.classList.remove('open'); container.classList.remove('panel-open');
			}
			// Toggle le nœud cliqué dans la multi-sélection
			const idx = multiSel.indexOf(fname);
			if (idx === -1) multiSel.push(fname);
			else			 multiSel.splice(idx, 1);
			selectedNode = null; highlightNodes.clear();
			sidePanel.classList.remove('open'); container.classList.remove('panel-open');
			updateAlignBar();
		}
		dragState=null; dragging=false;
		draw();
		return;
	}

	if (!dragging) {
		const rect=container.getBoundingClientRect();
		const sx=e.clientX-rect.left, sy=e.clientY-rect.top;
		const fname=getNodeAt(sx,sy);

		if (e.shiftKey) {
			// Shift+clic (fallback)
			if (fname) {
				if (selectedNode && multiSel.length === 0) {
					multiSel = [selectedNode];
					selectedNode = null; highlightNodes.clear();
					sidePanel.classList.remove('open'); container.classList.remove('panel-open');
				}
				const idx = multiSel.indexOf(fname);
				if (idx === -1) multiSel.push(fname);
				else			 multiSel.splice(idx, 1);
				selectedNode = null; highlightNodes.clear();
				sidePanel.classList.remove('open'); container.classList.remove('panel-open');
				updateAlignBar();
			}
		} else {
			// Clic normal → vide multi-sel, sélection simple
			if (multiSel.length > 0) { multiSel = []; updateAlignBar(); }
			if (fname) {
				selectedNode = (fname===selectedNode) ? null : fname;
				highlightNodes.clear();
				if (selectedNode) {
					for (const edge of EDGES_DATA) {
						if (edge.src===selectedNode) highlightNodes.add(edge.tgt);
						if (edge.tgt===selectedNode) highlightNodes.add(edge.src);
					}
					renderSidePanel(selectedNode);
				} else {
					closeSidePanel();
				}
			} else {
				selectedNode=null; highlightNodes.clear();
				closeSidePanel();
			}
		}
		draw();
	}
	canvas.classList.remove('grabbing','grab-group');
	dragState=null; dragging=false;
	dragHintDir=null;
});

container.addEventListener('mousemove',e=>updateHover(e));
container.addEventListener('mouseleave',()=>{tooltip.style.display='none';});

function updateHover(e) {
	const rect=container.getBoundingClientRect();
	const sx=e.clientX-rect.left, sy=e.clientY-rect.top;
	if (sx<0||sy<0||sx>rect.width||sy>rect.height) {tooltip.style.display='none';return;}
	const fname=getNodeAt(sx,sy);
	if (!fname) {tooltip.style.display='none';return;}
	const n=NODES_DATA[fname];

	let html=`<strong>${fname}</strong>`;
	html+=`<div class="meta">Module: ${n.group} · ${n.funcs.length} fonctions · ${n.is_header?'Header .h':'Source .c'}</div>`;

	if (n.funcs.length) {
		const shown=n.funcs.slice(0,16);
		html+=`<div class="fn-list">`;
		for (const fn of shown) html+=`<span class="fn-tag">${fn}</span>`;
		if (n.funcs.length>16) html+=`<span style="color:#557"> +${n.funcs.length-16}</span>`;
		html+=`</div>`;
	}
	html += `<div class="meta" style="margin-top:6px;color:#3a4a6a;font-size:9px;">Clic → détails · Shift+Clic sélectionné → masquer liens</div>`;

	tooltip.innerHTML=html;
	tooltip.style.display='block';
	const tw=tooltip.offsetWidth, th=tooltip.offsetHeight;
	let lx=e.clientX+16, ly=e.clientY+10;
	if (lx+tw>window.innerWidth-10) lx=e.clientX-tw-16;
	if (ly+th>window.innerHeight-10) ly=window.innerHeight-th-10;
	tooltip.style.left=lx+'px'; tooltip.style.top=ly+'px';
	return;
}


// ---- VUE ----
function resetView() {
	scale=0.48; tx=60; ty=40;
	selectedNode=null; highlightNodes.clear();
	multiSel=[]; updateAlignBar();
	hiddenEdgeNodes.clear();
	sidePanel.classList.remove('open');
	// Reset group offsets
	for (const g of Object.keys(groupOffsets)) groupOffsets[g]={dx:0,dy:0};
	// Reset node positions (calées sur la grille)
	for (const [f,p] of Object.entries(INIT_POS)) positions[f]={x:p.x,y:p.y};
	dragHintDir=null;
	draw();
}

function onSearch(q) {
	searchQuery=q.trim();
	if (searchQuery) {
		const match=Object.keys(NODES_DATA).find(f=>f.toLowerCase().includes(searchQuery.toLowerCase()));
		if (match) {
			const p=nodePos(match);
			const W=canvas.offsetWidth, H=canvas.offsetHeight;
			tx=W/2-(p.x+NODE_W/2)*scale;
			ty=H/2-(p.y+NODE_H/2)*scale;
		}
	}
	draw();
}

// ResizeObserver : redessine en continu pendant la transition CSS du panneau
// (déclaré ici après 'container' pour éviter le ReferenceError)
const _ro = new ResizeObserver(() => { resize(); });
_ro.observe(container);

// ── Point d'entrée ────────────────────────────────────────────────────────
function main() {
	applyProjectMeta();
	buildLegend();
	resize();
	updatePanelTop();
}

main();
