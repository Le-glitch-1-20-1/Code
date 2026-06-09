// =============================================
//	MA BIBLIOTHÈQUE — Application principale
// =============================================

const GENRES_PRINCIPAUX = ["Histoire", "Polar", "Société", "Roman", "Art", "Bande dessinée", "Magazine", "Poésie", "Livre de cuisine", "Divers"];

const GENRE_EMOJI = {
	"Histoire":"🏛️", "Polar":"🔍", "Société":"🌍",
	"Roman":"📖", "Science-fiction":"🚀", "Fantasy":"🧙",
	"Thriller":"🕵️", "Biographie":"👤", "Sciences":"🔬",
	"Philosophie":"🧠", "BD":"🎨", "Manga":"⛩️",
	"Jeunesse":"🌟", "Poésie":"🌸", "Développement personnel":"💡",
	"Art":"🎨", "Bande dessinée":"🖼️", "Magazine":"📰", "Livre de cuisine":"🍳", "Divers":"🗂️"
};

const STATUT_CLASS = {
	"Lu":"s-lu", "En cours":"s-encours", "Non lu":"s-nonlu", "Prêté":"s-prete"
};

const SUPPORT_EMOJI = {
	"Papier":"📄", "Liseuse":"📱", "PDF":"🖥", "Audio":"🎧"
};

const GENRE_KEYWORDS = {
	"Histoire": [
		"history","histoire","historical","guerre","war","medieval","ancient","moyen-âge",
		"empire","révolution","colonialism","archaeolog","antique","world war","antiquity",
		"civilization","civilisation","première guerre","seconde guerre"
	],
	"Polar": [
		"detective","mystery","crime","thriller","polar","policier","noir","investigation",
		"murder","meurtrier","enquête","suspense","espionnage","spy","whodunit","forensic",
		"criminal","criminelle","serial killer"
	],
	"Société": [
		"sociology","sociologie","society","social","politique","politics","economics",
		"économie","philosophy","philosophie","essai","essay","contemporary","contemporain",
		"journalism","journalisme","environment","écologie","ecology","anthropolog",
		"psychology","psychologie","self-help","développement","feminism","féminisme",
		"geopolitics","géopolitique","témoignage"
	]
};

// Genres qui s'ajoutent dynamiquement si un livre ne rentre pas dans les 3 principaux
let GENRES_EXTRA = [];

let books = [];
let currentView = 'tous';
let displayMode = 'grid';
let editingId = null;
let pendingCoverPath = null;
let pendingGenreConfirm = null;
let isbnLookupTimeout = null;

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async () => {
	books = await window.api.loadBooks();

	// Reconstruire les genres extra depuis les livres existants
	books.forEach(b => {
		if (b.genre && !GENRES_PRINCIPAUX.includes(b.genre) && !GENRES_EXTRA.includes(b.genre)) {
			GENRES_EXTRA.push(b.genre);
		}
	});

	populateGenreSelects();
	buildGenreNav();
	wireEvents();
	renderBooks();
});

// ===== WIRE ALL EVENTS =====
function wireEvents() {
	// Sidebar nav items (statuts)
	document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
		btn.addEventListener('click', () => setView(btn.dataset.view, btn));
	});

	// Boutons vue grille/liste
	document.getElementById('vgrid').addEventListener('click', () => setDisplay('grid'));
	document.getElementById('vlist').addEventListener('click', () => setDisplay('list'));

	// Recherche + tri
	document.getElementById('search').addEventListener('input', renderBooks);
	document.getElementById('sort').addEventListener('change', renderBooks);

	// Bouton ajouter
	document.getElementById('btn-add').addEventListener('click', () => openModal());
	document.getElementById('btn-add-empty').addEventListener('click', () => openModal());

	// Export / import / dossier
	document.getElementById('btn-export').addEventListener('click', exportData);
	document.getElementById('btn-import').addEventListener('click', importData);
	document.getElementById('btn-folder').addEventListener('click', openFolder);

	// Modal
	document.getElementById('btn-modal-close').addEventListener('click', closeModal);
	document.getElementById('btn-modal-cancel').addEventListener('click', closeModal);
	document.getElementById('btn-save').addEventListener('click', saveBook);
	document.getElementById('btn-delete').addEventListener('click', deleteBook);
	document.getElementById('modal-overlay').addEventListener('click', e => {
		if (e.target === document.getElementById('modal-overlay')) closeModal();
	});

	// ISBN
	document.getElementById('isbn-btn').addEventListener('click', lookupISBN);
	document.getElementById('f-isbn').addEventListener('keydown', e => {
		if (e.key === 'Enter') lookupISBN();
	});
	document.getElementById('f-isbn').addEventListener('input', e => onIsbnInput(e.target.value));

	// Cover
	document.getElementById('cover-preview').addEventListener('click', pickCover);

	// Note slider
	document.getElementById('f-note').addEventListener('input', e => updateNote(e.target.value));

	// Support buttons
	document.querySelectorAll('.support-btn').forEach(btn => {
		btn.addEventListener('click', () => selectSupport(btn));
	});

	// Genre confirm modal
	document.getElementById('btn-genre-close').addEventListener('click', closeGenreConfirm);
	document.getElementById('btn-genre-ignore').addEventListener('click', closeGenreConfirm);
	document.getElementById('btn-genre-apply').addEventListener('click', applyGenreConfirm);

	// Modal ajout genre
	document.getElementById('btn-add-genre-close').addEventListener('click', closeAddGenreModal);
	document.getElementById('btn-add-genre-cancel').addEventListener('click', closeAddGenreModal);
	document.getElementById('btn-add-genre-confirm').addEventListener('click', confirmAddGenre);
	document.getElementById('add-genre-overlay').addEventListener('click', e => {
		if (e.target === document.getElementById('add-genre-overlay')) closeAddGenreModal();
	});
	document.getElementById('new-genre-input').addEventListener('keydown', e => {
		if (e.key === 'Enter') confirmAddGenre();
		if (e.key === 'Escape') closeAddGenreModal();
	});

	// Keyboard shortcuts
	document.addEventListener('keydown', e => {
		if (e.key === 'Escape') {
			if (document.getElementById('genre-confirm-overlay').classList.contains('open')) {
				closeGenreConfirm();
			} else {
				closeModal();
			}
		}
		if ((e.ctrlKey || e.metaKey) && e.key === 'n') { e.preventDefault(); openModal(); }
		if ((e.ctrlKey || e.metaKey) && e.key === 'f') { e.preventDefault(); document.getElementById('search').focus(); }
	});
}

// ===== GENRES =====
function getAllGenres() {
	return [...GENRES_PRINCIPAUX, ...GENRES_EXTRA];
}

function addExtraGenre(genre) {
	if (!GENRES_PRINCIPAUX.includes(genre) && !GENRES_EXTRA.includes(genre)) {
		GENRES_EXTRA.push(genre);
		populateGenreSelects();
		buildGenreNav();
	}
}

function populateGenreSelects() {
	['f-genre', 'genre-confirm-select'].forEach(id => {
		const sel = document.getElementById(id);
		if (!sel) return;
		const current = sel.value;
		sel.innerHTML = '<option value="">— Choisir —</option>';

		const grpMain = document.createElement('optgroup');
		grpMain.label = 'Principaux';
		GENRES_PRINCIPAUX.forEach(g => {
			const o = document.createElement('option');
			o.value = g; o.textContent = `${GENRE_EMOJI[g] || '📚'} ${g}`;
			grpMain.appendChild(o);
		});
		sel.appendChild(grpMain);

		if (GENRES_EXTRA.length > 0) {
			const grpExtra = document.createElement('optgroup');
			grpExtra.label = 'Autres';
			GENRES_EXTRA.forEach(g => {
				const o = document.createElement('option');
				o.value = g; o.textContent = `${GENRE_EMOJI[g] || '📚'} ${g}`;
				grpExtra.appendChild(o);
			});
			sel.appendChild(grpExtra);
		}

		if (current) sel.value = current;
	});
}

function buildGenreNav() {
	const nav = document.getElementById('genre-nav');
	nav.innerHTML = '';

	GENRES_PRINCIPAUX.forEach(g => {
		const count = books.filter(b => b.genre === g).length;
		const btn = document.createElement('button');
		btn.className = 'nav-item nav-item-main';
		btn.dataset.view = 'genre:' + g;
		btn.innerHTML = `<span class="nav-icon">${GENRE_EMOJI[g] || '📚'}</span> ${g}${count > 0 ? `<span class="nav-count">${count}</span>` : ''}`;
		btn.addEventListener('click', () => setView('genre:' + g, btn));
		nav.appendChild(btn);
	});

	if (GENRES_EXTRA.length > 0) {
		const sep = document.createElement('div');
		sep.style.cssText = 'padding:8px 14px 2px;font-size:9px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em';
		sep.textContent = 'Mes genres';
		nav.appendChild(sep);

		GENRES_EXTRA.forEach(g => {
			const wrap = document.createElement('div');
			wrap.style.cssText = 'display:flex;align-items:center;';
			const btn = document.createElement('button');
			btn.className = 'nav-item';
			btn.style.flex = '1';
			btn.dataset.view = 'genre:' + g;
			const cnt = books.filter(b => b.genre === g).length;
			btn.innerHTML = `<span class="nav-icon">${GENRE_EMOJI[g] || '📚'}</span> ${g}${cnt > 0 ? `<span class="nav-count">${cnt}</span>` : ''}`;
			btn.addEventListener('click', () => setView('genre:' + g, btn));
			const del = document.createElement('button');
			del.className = 'genre-delete-btn';
			del.title = 'Supprimer ce genre';
			del.textContent = '✕';
			del.addEventListener('click', (e) => { e.stopPropagation(); deleteExtraGenre(g); });
			wrap.appendChild(btn);
			wrap.appendChild(del);
			nav.appendChild(wrap);
		});
	}

	// Bouton "Ajouter un genre"
	const addGenreBtn = document.createElement('button');
	addGenreBtn.className = 'action-btn';
	addGenreBtn.style.cssText = 'margin:6px 8px 0;font-size:12px;color:var(--accent);';
	addGenreBtn.innerHTML = '＋ Nouveau genre';
	addGenreBtn.addEventListener('click', openAddGenreModal);
	nav.appendChild(addGenreBtn);

	// Re-wire active state for current view
	document.querySelectorAll('#genre-nav .nav-item').forEach(btn => {
		if (btn.dataset.view === currentView) btn.classList.add('active');
	});
}

function updateGenreCounts() {
	document.querySelectorAll('#genre-nav .nav-item[data-view]').forEach(btn => {
		const view = btn.dataset.view;
		if (!view.startsWith('genre:')) return;
		const g = view.replace('genre:', '');
		const count = books.filter(b => b.genre === g).length;
		// Update or add the count badge without rebuilding the whole button
		let badge = btn.querySelector('.nav-count');
		if (count > 0) {
			if (!badge) {
				badge = document.createElement('span');
				badge.className = 'nav-count';
				btn.appendChild(badge);
			}
			badge.textContent = count;
		} else if (badge) {
			badge.remove();
		}
	});
}

function deleteExtraGenre(genre) {
	const count = books.filter(b => b.genre === genre).length;
	const msg = count > 0
		? `Supprimer le genre "${genre}" ? (${count} livre${count>1?'s':''} conservé${count>1?'s':''}, genre retiré)`
		: `Supprimer le genre "${genre}" ?`;
	if (!confirm(msg)) return;
	GENRES_EXTRA.splice(GENRES_EXTRA.indexOf(genre), 1);
	if (currentView === 'genre:' + genre) setView('tous', document.querySelector('.nav-item[data-view="tous"]'));
	populateGenreSelects();
	buildGenreNav();
	showToast(`🗑 Genre "${genre}" supprimé`);
}

function openAddGenreModal() {
	document.getElementById('add-genre-overlay').classList.add('open');
	document.getElementById('new-genre-input').value = '';
	document.getElementById('new-genre-emoji').value = '📚';
	document.getElementById('new-genre-error').textContent = '';
	setTimeout(() => document.getElementById('new-genre-input').focus(), 50);
}

function closeAddGenreModal() {
	document.getElementById('add-genre-overlay').classList.remove('open');
}

function confirmAddGenre() {
	const name = document.getElementById('new-genre-input').value.trim();
	const emoji = document.getElementById('new-genre-emoji').value.trim() || '📚';
	const err = document.getElementById('new-genre-error');
	if (!name) { err.textContent = '⚠️ Nom obligatoire'; return; }
	const all = [...GENRES_PRINCIPAUX, ...GENRES_EXTRA];
	if (all.map(g => g.toLowerCase()).includes(name.toLowerCase())) {
		err.textContent = '⚠️ Ce genre existe déjà'; return;
	}
	GENRE_EMOJI[name] = emoji;
	addExtraGenre(name);
	closeAddGenreModal();
	showToast(`✅ Genre "${name}" ajouté !`);
}

// ===== SUPPORT =====
function selectSupport(btn) {
	document.querySelectorAll('.support-btn').forEach(b => b.classList.remove('active'));
	btn.classList.add('active');
}

function getSelectedSupport() {
	const active = document.querySelector('.support-btn.active');
	return active ? active.dataset.val : 'Papier';
}

function setSelectedSupport(val) {
	document.querySelectorAll('.support-btn').forEach(b => {
		b.classList.toggle('active', b.dataset.val === val);
	});
}

// ===== ISBN LOOKUP =====
function onIsbnInput(val) {
	const clean = val.replace(/[-\s]/g, '');
	if (clean.length === 10 || clean.length === 13) {
		clearTimeout(isbnLookupTimeout);
		isbnLookupTimeout = setTimeout(lookupISBN, 700);
	}
}

async function lookupISBN() {
	const raw = document.getElementById('f-isbn').value.trim();
	const isbn = raw.replace(/[-\s]/g, '');
	if (!isbn || (isbn.length !== 10 && isbn.length !== 13)) {
		setIsbnStatus('⚠️ ISBN invalide (10 ou 13 chiffres)', 'warn');
		return;
	}

	setIsbnStatus('🔄 Recherche en cours…', 'loading');
	document.getElementById('isbn-btn').disabled = true;

	try {
		const url = `https://openlibrary.org/api/books?bibkeys=ISBN:${isbn}&format=json&jscmd=details`;
		const res = await fetch(url);
		const data = await res.json();
		const key = `ISBN:${isbn}`;

		if (!data[key]) {
			setIsbnStatus('❌ Livre non trouvé — remplis manuellement', 'error');
			document.getElementById('isbn-btn').disabled = false;
			return;
		}

		const details = data[key].details || {};

		if (details.title) document.getElementById('f-titre').value = details.full_title || details.title;
		if (details.authors?.length) document.getElementById('f-auteur').value = details.authors[0].name || '';
		if (details.publish_date) {
			const year = parseInt(details.publish_date.match(/\d{4}/)?.[0]);
			if (year) document.getElementById('f-annee').value = year;
		}
		if (details.number_of_pages) document.getElementById('f-pages').value = details.number_of_pages;
		if (details.publishers?.length) document.getElementById('f-editeur').value = details.publishers[0];
		if (details.languages?.length) {
			const langMap = {
				'/languages/fre':'Français', '/languages/eng':'Anglais',
				'/languages/spa':'Espagnol', '/languages/ger':'Allemand',
				'/languages/ita':'Italien', '/languages/jpn':'Japonais'
			};
			const lang = langMap[details.languages[0].key];
			if (lang) document.getElementById('f-langue').value = lang;
		}
		if (details.covers?.length) {
			const coverUrl = `https://covers.openlibrary.org/b/id/${details.covers[0]}-M.jpg`;
			document.getElementById('cover-img').src = coverUrl;
			document.getElementById('cover-img').style.display = 'block';
			document.getElementById('cover-placeholder').style.display = 'none';
			pendingCoverPath = coverUrl;
		}

		// Détection genre
		const subjects = [
			...(details.subjects || []),
			...(details.subject_places || []),
			...(details.subject_times || []),
		].map(s => (typeof s === 'string' ? s : s.name || '').toLowerCase());

		const detected = detectGenre(subjects);
		const currentGenre = document.getElementById('f-genre').value;

		if (detected && currentGenre !== detected) {
			proposeGenre(detected, subjects);
		}

		setIsbnStatus('✅ Livre trouvé !', 'ok');
	} catch (e) {
		setIsbnStatus('❌ Erreur réseau', 'error');
		console.error(e);
	}
	document.getElementById('isbn-btn').disabled = false;
}

function detectGenre(subjects) {
	const text = subjects.join(' ');
	for (const [genre, keywords] of Object.entries(GENRE_KEYWORDS)) {
		if (keywords.some(kw => text.includes(kw))) return genre;
	}
	return null;
}

function proposeGenre(genre, subjects) {
	pendingGenreConfirm = genre;
	const preview = subjects.slice(0, 4).join(', ') || 'non précisé';
	document.getElementById('genre-confirm-msg').innerHTML =
		`Open Library indique les thèmes : <strong style="color:var(--text)">${preview}</strong><br><br>
		 Genre détecté : <strong style="color:var(--accent)">${GENRE_EMOJI[genre] || ''} ${genre}</strong>`;

	// Re-populate in case of extra genres
	populateGenreSelects();
	document.getElementById('genre-confirm-select').value = genre;
	document.getElementById('genre-confirm-overlay').classList.add('open');
}

function closeGenreConfirm() {
	document.getElementById('genre-confirm-overlay').classList.remove('open');
	pendingGenreConfirm = null;
}

function applyGenreConfirm() {
	const val = document.getElementById('genre-confirm-select').value;
	if (val) document.getElementById('f-genre').value = val;
	closeGenreConfirm();
}

function setIsbnStatus(msg, type) {
	const el = document.getElementById('isbn-status');
	el.textContent = msg;
	el.className = 'isbn-status' + (type ? ' isbn-' + type : '');
}

// ===== VIEWS =====
function setView(view, el) {
	currentView = view;
	document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
	if (el) el.classList.add('active');

	const titles = {
		'tous':'Tous les livres', 'en-cours':'En cours de lecture',
		'lu':'Livres lus', 'non-lu':'Livres non lus',
		'prete':'Livres prêtés', 'favoris':'⭐ Favoris', 'liseuse':'📱 Liseuse',
		'a-relire':'🔁 À relire',
	};
	const title = titles[view] || (view.startsWith('genre:') ? view.replace('genre:', '') : view);
	document.getElementById('view-title').textContent = title;
	renderBooks();
}

function setDisplay(mode) {
	displayMode = mode;
	document.getElementById('vgrid').classList.toggle('active', mode === 'grid');
	document.getElementById('vlist').classList.toggle('active', mode === 'list');
	renderBooks();
}

// ===== FILTERING =====
function getFilteredBooks() {
	const q = (document.getElementById('search').value || '').toLowerCase().trim();
	let result = [...books];

	if (currentView === 'en-cours') result = result.filter(b => b.statut === 'En cours');
	else if (currentView === 'lu') result = result.filter(b => b.statut === 'Lu');
	else if (currentView === 'non-lu') result = result.filter(b => b.statut === 'Non lu');
	else if (currentView === 'prete') result = result.filter(b => b.statut === 'Prêté');
	else if (currentView === 'favoris') result = result.filter(b => b.favori);
	else if (currentView === 'liseuse') result = result.filter(b => b.support === 'Liseuse');
	else if (currentView === 'a-relire') result = result.filter(b => b.aRelire);
	else if (currentView.startsWith('genre:')) {
		result = result.filter(b => b.genre === currentView.replace('genre:', ''));
	}

	if (q) result = result.filter(b =>
		(b.titre||'').toLowerCase().includes(q) ||
		(b.auteur||'').toLowerCase().includes(q) ||
		(b.genre||'').toLowerCase().includes(q) ||
		(b.isbn||'').toLowerCase().includes(q) ||
		(b.editeur||'').toLowerCase().includes(q)
	);
	return result;
}

function sortBooks(arr) {
	const s = document.getElementById('sort').value;
	return [...arr].sort((a, b) => {
		if (s === 'titre') return (a.titre||'').localeCompare(b.titre||'');
		if (s === 'auteur') return (a.auteur||'').localeCompare(b.auteur||'');
		if (s === 'annee') return (b.annee||0) - (a.annee||0);
		if (s === 'note') return (b.note||0) - (a.note||0);
		if (s === 'date_ajout') return (b.date_ajout||0) - (a.date_ajout||0);
		return 0;
	});
}

// ===== RENDER =====
function renderBooks() {
	const filtered = getFilteredBooks();
	const sorted = sortBooks(filtered);
	const container = document.getElementById('books-container');
	const emptyState = document.getElementById('empty-state');

	const total = books.length;
	const lus = books.filter(b => b.statut === 'Lu').length;
	const encours = books.filter(b => b.statut === 'En cours').length;
	const pretes = books.filter(b => b.statut === 'Prêté').length;
	const liseuse = books.filter(b => b.support === 'Liseuse').length;
	const totalPages = books.reduce((s, b) => s + (b.pages || 0), 0);

	document.getElementById('stat-total').innerHTML = `<b>${total}</b> livre${total>1?'s':''}`;
	document.getElementById('stat-lu').innerHTML = `✅ <b>${lus}</b> lu${lus>1?'s':''}`;
	document.getElementById('stat-encours').innerHTML = `📖 <b>${encours}</b> en cours`;
	document.getElementById('stat-prete').innerHTML = `🤝 <b>${pretes}</b> prêté${pretes>1?'s':''}`;
	document.getElementById('stat-liseuse').innerHTML = liseuse > 0 ? `📱 <b>${liseuse}</b> liseuse` : '';
	document.getElementById('stat-pages').innerHTML = totalPages > 0 ? `📄 <b>${totalPages.toLocaleString()}</b> pages` : '';
	document.getElementById('book-count').textContent = `${filtered.length} livre${filtered.length>1?'s':''}`;

	if (sorted.length === 0) {
		container.style.display = 'none';
		emptyState.style.display = 'flex';
		return;
	}
	emptyState.style.display = 'none';
	container.style.display = 'block';

	if (displayMode === 'grid') {
		container.innerHTML = `<div class="grid-view">${sorted.map(bookCardHTML).join('')}</div>`;
	} else {
		let html = `<div class="list-header">
			<span></span><span>Titre / Auteur</span><span>Genre</span>
			<span>Statut</span><span>Support</span><span>Année</span><span>Note</span>
		</div><div class="list-view">${sorted.map(bookRowHTML).join('')}</div>`;
		container.innerHTML = html;
	}

	// Update genre counts dynamically
	updateGenreCounts();

	// Wire card clicks
	container.querySelectorAll('[data-book-id]').forEach(el => {
		el.addEventListener('click', () => openModal(parseInt(el.dataset.bookId)));
	});
}

function bookCardHTML(b) {
	const emoji = GENRE_EMOJI[b.genre] || '📚';
	const stars = b.note > 0 ? '★'.repeat(Math.floor(b.note)) + (b.note % 1 ? '½' : '') : '';
	const supportBadge = b.support && b.support !== 'Papier'
		? `<span class="support-badge">${SUPPORT_EMOJI[b.support] || ''} ${b.support}</span>` : '';
	const coverContent = b.cover
		? `<img src="${b.cover}" onerror="this.style.display='none'">`
		: `<span class="book-cover-placeholder">${emoji}</span>`;
	const progressBar = (b.statut === 'En cours' && b.pages && b.pagesLues)
		? `<div class="progress-bar-wrap"><div class="progress-bar" style="width:${Math.min(100,Math.round(b.pagesLues/b.pages*100))}%"></div></div>`
		: '';
	return `<div class="book-card" data-book-id="${b.id}">
		<div class="book-cover">
			${coverContent}
			${b.favori ? '<span class="favori-star">⭐</span>' : ''}
			${b.aRelire ? '<span class="relire-badge">🔁</span>' : ''}
			${supportBadge}
		</div>
		<div class="book-card-body">
			<div class="book-card-title">${esc(b.titre)}</div>
			<div class="book-card-author">${esc(b.auteur||'')}</div>
			${progressBar}
			<div class="book-card-footer">
				<span class="badge-statut ${STATUT_CLASS[b.statut]||'s-nonlu'}">${b.statut||'Non lu'}</span>
				<span class="star-rating">${stars}</span>
			</div>
		</div>
	</div>`;
}

function bookRowHTML(b) {
	const emoji = GENRE_EMOJI[b.genre] || '📚';
	const stars = b.note > 0 ? '★'.repeat(Math.floor(b.note)) + (b.note % 1 ? '½' : '') : '—';
	const coverContent = b.cover
		? `<img src="${b.cover}" style="width:100%;height:100%;object-fit:cover" onerror="this.style.display='none'">`
		: emoji;
	return `<div class="book-row" data-book-id="${b.id}">
		<div class="book-row-cover">${coverContent}</div>
		<div><div class="row-title">${esc(b.titre)}</div><div class="row-author">${esc(b.auteur||'')}</div></div>
		<div class="row-genre">${b.genre ? (GENRE_EMOJI[b.genre]||'') + ' ' + b.genre : '—'}</div>
		<div><span class="badge-statut ${STATUT_CLASS[b.statut]||'s-nonlu'}">${b.statut||'Non lu'}</span></div>
		<div class="row-support">${SUPPORT_EMOJI[b.support]||'📄'} ${b.support||'Papier'}</div>
		<div class="row-annee">${b.annee||'—'}</div>
		<div class="row-note" style="color:var(--accent)">${stars}</div>
	</div>`;
}

// ===== MODAL =====
function openModal(id) {
	editingId = id || null;
	pendingCoverPath = null;

	document.getElementById('modal-title').textContent = id ? 'Modifier le livre' : 'Ajouter un livre';
	document.getElementById('btn-delete').style.display = id ? 'block' : 'none';

	// Reset
	['titre','auteur','annee','pages','editeur','notes','prete-a'].forEach(f => {
		const el = document.getElementById('f-'+f);
		if (el) el.value = '';
	});
	document.getElementById('f-isbn').value = '';
	document.getElementById('f-pages-lues').value = '';
	document.getElementById('f-date-lu').value = '';
	document.getElementById('f-genre').value = '';
	document.getElementById('f-statut').value = 'Non lu';
	document.getElementById('f-langue').value = 'Français';
	document.getElementById('f-note').value = 0;
	document.getElementById('f-favori').checked = false;
	document.getElementById('f-a-relire').checked = false;
	setSelectedSupport('Papier');
	updateNote(0);
	setIsbnStatus('', '');
	document.getElementById('cover-img').style.display = 'none';
	document.getElementById('cover-placeholder').style.display = 'block';

	if (id) {
		const b = books.find(x => x.id === id);
		if (b) {
			document.getElementById('f-titre').value = b.titre || '';
			document.getElementById('f-auteur').value = b.auteur || '';
			document.getElementById('f-annee').value = b.annee || '';
			document.getElementById('f-pages').value = b.pages || '';
			document.getElementById('f-isbn').value = b.isbn || '';
			document.getElementById('f-editeur').value = b.editeur || '';
			document.getElementById('f-notes').value = b.notes || '';
			document.getElementById('f-prete-a').value = b.preteA || '';
			document.getElementById('f-genre').value = b.genre || '';
			document.getElementById('f-statut').value = b.statut || 'Non lu';
			document.getElementById('f-langue').value = b.langue || 'Français';
			document.getElementById('f-note').value = b.note || 0;
			document.getElementById('f-favori').checked = !!b.favori;
			document.getElementById('f-a-relire').checked = !!b.aRelire;
			document.getElementById('f-pages-lues').value = b.pagesLues || '';
			document.getElementById('f-date-lu').value = b.dateLu || '';
			setSelectedSupport(b.support || 'Papier');
			updateNote(b.note || 0);
			if (b.cover) {
				pendingCoverPath = b.cover;
				document.getElementById('cover-img').src = b.cover;
				document.getElementById('cover-img').style.display = 'block';
				document.getElementById('cover-placeholder').style.display = 'none';
			}
		}
	}

	document.getElementById('modal-overlay').classList.add('open');
	setTimeout(() => document.getElementById('f-isbn').focus(), 50);
}

function closeModal() {
	document.getElementById('modal-overlay').classList.remove('open');
	editingId = null;
	pendingCoverPath = null;
}

function updateNote(val) {
	const n = parseFloat(val);
	document.getElementById('note-val').textContent = n > 0
		? '★'.repeat(Math.floor(n)) + (n % 1 ? '½' : '') + ` (${n}/5)`
		: '—';
}

async function pickCover() {
	const p = await window.api.pickCover();
	if (p) {
		pendingCoverPath = p;
		document.getElementById('cover-img').src = p;
		document.getElementById('cover-img').style.display = 'block';
		document.getElementById('cover-placeholder').style.display = 'none';
	}
}

function saveBook() {
	const titre = document.getElementById('f-titre').value.trim();
	if (!titre) {
		showToast('⚠️ Le titre est obligatoire');
		document.getElementById('f-titre').focus();
		return;
	}

	const genre = document.getElementById('f-genre').value;

	// Si genre hors des 3 principaux → l'ajouter à la liste extra et à la sidebar
	if (genre && !GENRES_PRINCIPAUX.includes(genre)) {
		addExtraGenre(genre);
	}

	const book = {
		id: editingId || Date.now(),
		titre,
		auteur: document.getElementById('f-auteur').value.trim(),
		genre,
		statut: document.getElementById('f-statut').value,
		support: getSelectedSupport(),
		langue: document.getElementById('f-langue').value,
		annee: parseInt(document.getElementById('f-annee').value) || null,
		pages: parseInt(document.getElementById('f-pages').value) || null,
		isbn: document.getElementById('f-isbn').value.trim(),
		editeur: document.getElementById('f-editeur').value.trim(),
		notes: document.getElementById('f-notes').value.trim(),
		preteA: document.getElementById('f-prete-a').value.trim(),
		note: parseFloat(document.getElementById('f-note').value) || 0,
		favori: document.getElementById('f-favori').checked,
		aRelire: document.getElementById('f-a-relire').checked,
		pagesLues: parseInt(document.getElementById('f-pages-lues').value) || 0,
		dateLu: document.getElementById('f-date-lu').value || null,
		cover: pendingCoverPath || null,
		date_ajout: editingId
			? (books.find(b => b.id === editingId)?.date_ajout || Date.now())
			: Date.now(),
	};

	if (editingId) {
		const idx = books.findIndex(b => b.id === editingId);
		if (idx !== -1) books[idx] = book;
	} else {
		books.push(book);
	}

	window.api.saveBooks(books);
	closeModal();
	renderBooks();
	showToast(editingId ? '✅ Livre modifié' : '📚 Livre ajouté !');
}

function deleteBook() {
	if (!editingId) return;
	if (!confirm('Supprimer ce livre définitivement ?')) return;
	books = books.filter(b => b.id !== editingId);
	window.api.saveBooks(books);
	closeModal();
	renderBooks();
	showToast('🗑 Livre supprimé');
}

// ===== IMPORT / EXPORT =====
async function exportData() {
	const ok = await window.api.exportJSON();
	if (ok) showToast('✅ Bibliothèque exportée !');
}

async function importData() {
	const data = await window.api.importJSON();
	if (data && Array.isArray(data)) {
		if (confirm(`Importer ${data.length} livre(s) ? Cela remplacera votre bibliothèque actuelle.`)) {
			books = data;
			// Reconstruire genres extra
			GENRES_EXTRA.length = 0;
			books.forEach(b => {
				if (b.genre && !GENRES_PRINCIPAUX.includes(b.genre) && !GENRES_EXTRA.includes(b.genre)) {
					GENRES_EXTRA.push(b.genre);
				}
			});
			populateGenreSelects();
			buildGenreNav();
			await window.api.saveBooks(books);
			renderBooks();
			showToast(`📥 ${data.length} livres importés`);
		}
	} else if (data !== null) {
		showToast('❌ Fichier invalide');
	}
}

async function openFolder() {
	await window.api.openDataFolder();
}

// ===== UTILS =====
function esc(str) {
	return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

let toastTimer;
function showToast(msg) {
	const t = document.getElementById('toast');
	t.textContent = msg;
	t.classList.add('show');
	clearTimeout(toastTimer);
	toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
}
