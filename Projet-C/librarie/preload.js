const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
	loadBooks: () => ipcRenderer.invoke('books:load'),
	saveBooks: (books) => ipcRenderer.invoke('books:save', books),
	exportJSON: () => ipcRenderer.invoke('books:exportJSON'),
	importJSON: () => ipcRenderer.invoke('books:importJSON'),
	pickCover: () => ipcRenderer.invoke('cover:pick'),
	openDataFolder: () => ipcRenderer.invoke('app:openDataFolder'),
	getDataPath: () => ipcRenderer.invoke('app:getDataPath'),
});
