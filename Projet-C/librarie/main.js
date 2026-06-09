const { app, BrowserWindow, ipcMain, dialog, shell, session } = require('electron');
const path = require('path');
const fs = require('fs');

const dataDir = path.join(app.getPath('documents'), 'MaBibliotheque');
const dataFile = path.join(dataDir, 'livres.json');
const coversDir = path.join(dataDir, 'couvertures');

function ensureDirs() {
	if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
	if (!fs.existsSync(coversDir)) fs.mkdirSync(coversDir, { recursive: true });
}

function loadBooks() {
	ensureDirs();
	if (!fs.existsSync(dataFile)) return [];
	try { return JSON.parse(fs.readFileSync(dataFile, 'utf8')); }
	catch { return []; }
}

function saveBooks(books) {
	ensureDirs();
	fs.writeFileSync(dataFile, JSON.stringify(books, null, 2), 'utf8');
}

function createWindow() {
	const win = new BrowserWindow({
		width: 1280,
		height: 800,
		minWidth: 900,
		minHeight: 600,
		title: 'Ma Bibliothèque',
		webPreferences: {
			preload: path.join(__dirname, 'preload.js'),
			contextIsolation: true,
			nodeIntegration: false
		},
		backgroundColor: '#1a1a1a',
		show: false
	});

	win.loadFile(path.join(__dirname, 'src', 'index.html'));
	win.once('ready-to-show', () => win.show());
}

app.whenReady().then(() => {
	// Autoriser les requêtes vers Open Library (pour la recherche ISBN)
	session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
		callback({
			responseHeaders: {
				...details.responseHeaders,
				'Content-Security-Policy': [
					"default-src 'self' https://openlibrary.org https://covers.openlibrary.org; " +
					"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
					"font-src 'self' https://fonts.gstatic.com; " +
					"img-src 'self' data: file: https://covers.openlibrary.org; " +
					"connect-src 'self' https://openlibrary.org https://covers.openlibrary.org;"
				]
			}
		});
	});
	createWindow();
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });

// IPC handlers
ipcMain.handle('books:load', () => loadBooks());
ipcMain.handle('books:save', (_, books) => { saveBooks(books); return true; });

ipcMain.handle('books:exportJSON', async () => {
	const { filePath } = await dialog.showSaveDialog({
		title: 'Exporter la bibliothèque',
		defaultPath: 'bibliotheque_export.json',
		filters: [{ name: 'JSON', extensions: ['json'] }]
	});
	if (filePath) { fs.copyFileSync(dataFile, filePath); return true; }
	return false;
});

ipcMain.handle('books:importJSON', async () => {
	const { filePaths } = await dialog.showOpenDialog({
		title: 'Importer une bibliothèque',
		filters: [{ name: 'JSON', extensions: ['json'] }],
		properties: ['openFile']
	});
	if (filePaths && filePaths[0]) {
		try { return JSON.parse(fs.readFileSync(filePaths[0], 'utf8')); }
		catch { return null; }
	}
	return null;
});

ipcMain.handle('cover:pick', async () => {
	const { filePaths } = await dialog.showOpenDialog({
		title: 'Choisir une couverture',
		filters: [{ name: 'Images', extensions: ['jpg','jpeg','png','webp','gif'] }],
		properties: ['openFile']
	});
	if (filePaths && filePaths[0]) {
		const ext = path.extname(filePaths[0]);
		const dest = path.join(coversDir, `cover_${Date.now()}${ext}`);
		fs.copyFileSync(filePaths[0], dest);
		return dest;
	}
	return null;
});

ipcMain.handle('app:openDataFolder', () => shell.openPath(dataDir));
ipcMain.handle('app:getDataPath', () => dataFile);
