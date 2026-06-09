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
