(function ()
{
	'use strict';
	function peuplerMenuExtensions()
	{
		const select = document.getElementById('searchExtension');
		const frag = document.createDocumentFragment();
		EXTENSIONS.forEach(ext =>
		{
			const opt = document.createElement('option');
			opt.value = ext;
			opt.textContent = ext;
			frag.appendChild(opt);
		});
		select.appendChild(frag);
	}
	function construireArbre(lignes)
	{
		const racine = {};
		for (const item of lignes)
		{
			const parties = item.p ? item.p.split('/') : [];
			let noeud = racine;
			for (const partie of parties)
			{
				if (!noeud[partie]) noeud[partie] = {};
				noeud = noeud[partie];
			}
			if (!noeud._fichiers) noeud._fichiers = [];
			noeud._fichiers.push(item);
		}
		return racine;
	}
	function creerFichier(item)
	{
		const div = document.createElement('div');
		div.className = 'fichier';
		div.dataset.n = item.n;
		div.dataset.e = item.e;
		div.dataset.t = item.t;
		div.dataset.u = item.u;
		div.title = 'Cliquer pour copier le nom';
		const badge = `<span class="ext-badge" data-ext="${item.e}">${item.e || '—'}</span>`;
		div.innerHTML =
			`<span class="nom">${item.n}</span>` +
			`<span class="copy-hint">📋 copier</span>` +
			`<div class="infos">${badge}<span class="taille">${item.t} ${item.u}</span></div>`;
		div.addEventListener('click', () =>
		{
			const nom = (item.n || '') + (item.e ? '.' + item.e : '');
			navigator.clipboard.writeText(nom).then(() => showToast('✅ Nom copié : ' + nom));
		});
		return div;
	}
	function creerNoeud(arbre, label)
	{
		const fragment = document.createDocumentFragment();
		const divDossier = document.createElement('div');
		divDossier.className = 'dossier';
		divDossier.textContent = label;
		const divContenu = document.createElement('div');
		divContenu.className = 'contenuDossier';
		if (arbre._fichiers)
		{
			for (const item of arbre._fichiers)
			{
				divContenu.appendChild(creerFichier(item));
			}
		}
		const sousDossiers = Object.entries(arbre).filter(([nom]) => nom !== '_fichiers');
		let sousRenduFait = false;
		function rendreSousDossiers()
		{
			if (sousRenduFait) return;
			sousRenduFait = true;
			const frag = document.createDocumentFragment();
			for (const [nom, sous] of sousDossiers)
			{
				frag.appendChild(creerNoeud(sous, '📁 ' + nom));
			}
			divContenu.appendChild(frag);
			const nb = divContenu.querySelectorAll(':scope > .fichier').length;
			if (nb > 0 && !divDossier.querySelector('.dossier-count'))
			{
				const badge = document.createElement('span');
				badge.className = 'dossier-count';
				badge.textContent = nb + (nb > 1 ? ' fichiers' : ' fichier');
				divDossier.appendChild(badge);
			}
		}
		divDossier.addEventListener('click', () =>
		{
			rendreSousDossiers();
			toggleDossier(divDossier);
		});
		fragment.appendChild(divDossier);
		fragment.appendChild(divContenu);
		return fragment;
	}
	function rendreTout()
	{
		const content = document.getElementById('content');
		const entries = Object.entries(DATA);
		let index = 0;
		const loader = document.getElementById('loading-indicator');
		function rendreProchaine()
		{
			if (index >= entries.length)
			{
				if (loader) loader.remove();
				if (typeof afficherStats === 'function') afficherStats();
				return;
			}
			const [label, lignes] = entries[index++];
			const arbre = construireArbre(lignes);
			content.appendChild(creerNoeud(arbre, label));
			if (loader) loader.textContent = `⏳ Chargement… ${index} / ${entries.length}`;
			requestAnimationFrame(rendreProchaine);
		}

		requestAnimationFrame(rendreProchaine);
	}
	document.addEventListener('DOMContentLoaded', () =>
	{
		peuplerMenuExtensions();
		rendreTout();
	});
})();
let sortMode = 'nom';
let sortAsc = true;

function toggleTheme()
{
	const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
	document.documentElement.setAttribute('data-theme', isDark ? '' : 'dark');
	document.querySelector('.theme-toggle').textContent = isDark ? '🌙' : '☀️';
	localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

function applyStoredTheme()
{
	const saved = localStorage.getItem('theme') || 'light';
	if (saved === 'dark')
	{
		document.documentElement.setAttribute('data-theme', 'dark');
		const btn = document.querySelector('.theme-toggle');
		if (btn) btn.textContent = '☀️';
	}
}

function expandAll()
{
	document.querySelectorAll('.contenuDossier').forEach(c => c.classList.add('visible'));
	document.querySelectorAll('.dossier').forEach(d => d.classList.add('expanded'));
}

function collapseAll()
{
	document.querySelectorAll('.contenuDossier').forEach(c => c.classList.remove('visible'));
	document.querySelectorAll('.dossier').forEach(d => d.classList.remove('expanded'));
}

function toggleDossier(element)
{
	const contenu = element.nextElementSibling;
	if (!contenu) return;
	const isVisible = contenu.classList.contains('visible');
	if (isVisible)
	{
		contenu.classList.remove('visible');
		element.classList.remove('expanded');
	}
	else
	{
		contenu.classList.add('visible');
		element.classList.add('expanded');
	}
}

function showToast(msg)
{
	const toast = document.getElementById('toast');
	toast.textContent = msg;
	toast.classList.add('show');
	setTimeout(() => toast.classList.remove('show'), 2500);
}

function filterFiles()
{
	const nameFilter = document.getElementById('searchName').value.toLowerCase();
	const extFilter  = document.getElementById('searchExtension').value.toLowerCase();
	let visibles = 0;
	let total = 0;
	document.querySelectorAll('.fichier').forEach(fichier =>
	{
		const nom = (fichier.dataset.n || '').toLowerCase();
		const ext = (fichier.dataset.e || '').toLowerCase();
		const matchNom = nom.includes(nameFilter);
		const matchExt = extFilter === ''
			? true
			: extFilter === '__noext__'
			? ext === ''
			: ext === extFilter;
		const show = matchNom && matchExt;
		fichier.style.display = show ? '' : 'none';
		if (show) visibles++;
		total++;
	});
	const countEl = document.getElementById('statVisibles');
	if (nameFilter || extFilter)
	{
		countEl.textContent = `🔎 ${visibles} / ${total} fichiers affichés`;
		countEl.style.display = '';
	}
	else
	{
		countEl.style.display = 'none';
	}
}

function setSortMode(mode, btn)
{
	sortMode = mode;
	document.querySelectorAll('.sort-btn[data-sort]').forEach(b => b.classList.remove('active'));
	btn.classList.add('active');
	applySortToAll();
}

function toggleSortDir()
{
	sortAsc = !sortAsc;
	document.getElementById('sortDirBtn').textContent = sortAsc ? '▲' : '▼';
	applySortToAll();
}

function applySortToAll()
{
	document.querySelectorAll('.contenuDossier').forEach(container =>
	{
		sortFichiersInContainer(container);
	});
}

function sortFichiersInContainer(container)
{
	const fichiers = Array.from(container.querySelectorAll(':scope > .fichier'));
	if (fichiers.length < 2) return;
	fichiers.sort((a, b) =>
	{
		if (sortMode === 'nom')
		{
			const va = (a.dataset.n || '').toLowerCase();
			const vb = (b.dataset.n || '').toLowerCase();
			return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
		}
		else if (sortMode === 'ext')
		{
			const va = (a.dataset.e || '').toLowerCase();
			const vb = (b.dataset.e || '').toLowerCase();
			return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
		}
		else if (sortMode === 'taille')
		{
			const va = toMo(a.dataset.t, a.dataset.u);
			const vb = toMo(b.dataset.t, b.dataset.u);
			return sortAsc ? va - vb : vb - va;
		}
		return 0;
	});
	fichiers.forEach(f => f.parentElement.appendChild(f));
}

function toMo(val, unite)
{
	const n = parseFloat((val || '0').replace(',', '.'));
	switch ((unite || '').toLowerCase())
	{
		case 'o':  return n / (1024 * 1024);
		case 'ko': return n / 1024;
		case 'mo': return n;
		case 'go': return n * 1024;
		case 'to': return n * 1024 * 1024;
		default:   return n;
	}
}

function afficherStats()
{
	let totalFichiers = 0;
	let totalDossiers = 0;
	let totalMo = 0;
	function compterArbre(arbre)
	{
		if (arbre._fichiers)
		{
			for (const item of arbre._fichiers)
			{
				totalFichiers++;
				totalMo += toMo(item.t, item.u);
			}
		}
		for (const [nom, sous] of Object.entries(arbre))
		{
			if (nom === '_fichiers') continue;
			totalDossiers++;
			compterArbre(sous);
		}
	}
	for (const lignes of Object.values(DATA))
	{
		const arbre = {};
		for (const item of lignes)
		{
			totalFichiers++;
			totalMo += toMo(item.t, item.u);
			const parties = item.p ? item.p.split('/') : [];
			let noeud = arbre;
			for (const partie of parties)
			{
				if (!noeud[partie]) { noeud[partie] = {}; totalDossiers++; }
				noeud = noeud[partie];
			}
		}
	}
	let tailleStr;
	if (totalMo < 1)              tailleStr = (totalMo * 1024).toFixed(1) + ' Ko';
	else if (totalMo < 1024)      tailleStr = totalMo.toFixed(1) + ' Mo';
	else if (totalMo < 1024*1024) tailleStr = (totalMo / 1024).toFixed(2) + ' Go';
	else                           tailleStr = (totalMo / (1024*1024)).toFixed(2) + ' To';
	document.getElementById('statFichiers').textContent = `📄 ${totalFichiers} fichiers`;
	document.getElementById('statDossiers').textContent = `📂 ${totalDossiers} dossiers`;
	document.getElementById('statTaille').textContent   = `💾 ${tailleStr} total`;
}

document.addEventListener('DOMContentLoaded', () =>
{
	applyStoredTheme();
});
