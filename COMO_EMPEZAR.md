# Cómo poner esto en marcha (sin programar)

Vas a hacer 4 cosas, todas de clicar botones. Tardan unos 10-15 minutos en total
y solo se hacen una vez.

## 1. Crear el repositorio en GitHub

1. Entra en https://github.com (crea una cuenta gratis si no tienes).
2. Botón verde "New" (repositorio nuevo).
3. Nómbralo, por ejemplo, `audiencias-tv-espana`. Puede ser público o privado.
4. Sube dentro todos los archivos de esta carpeta (`index.html`, `scraper_audiencias.py`,
   `COMO_EMPEZAR.md` y la carpeta `.github/`). En la página del repo verás un enlace
   que dice "uploading an existing file" — arrastra ahí los archivos.

## 2. Dar permiso de escritura a las Actions

Esto es imprescindible para que el robot pueda guardar los datos cada día.

1. En tu repositorio, ve a **Settings** → **Actions** → **General**.
2. Baja hasta "Workflow permissions".
3. Marca **"Read and write permissions"**.
4. Guarda.

## 3. Lanzar la primera recogida de datos a mano

1. Ve a la pestaña **Actions** de tu repositorio.
2. Verás un workflow llamado "Scrape diario de audiencias".
3. Pulsa **"Run workflow"** (botón desplegable a la derecha) para probarlo ya,
   sin esperar a mañana.
4. Espera 1-2 minutos y comprueba que aparece una carpeta `data/` con un archivo
   `history.json` dentro.

A partir de aquí, se ejecutará solo cada mañana sobre las 11:30h (hora de España),
sin que tengas que volver a tocar nada.

## 4. Conectar Netlify para ver el dashboard en una web de verdad

1. Entra en https://app.netlify.com (la misma cuenta que usaste para la web de notas).
2. "Add new site" → "Import an existing project" → conecta tu cuenta de GitHub.
3. Elige el repositorio `audiencias-tv-espana`.
4. Deja los campos de "build" en blanco (no hace falta ningún comando de compilación,
   es una web estática) y pulsa **Deploy**.
5. Netlify te dará una URL (algo como `audiencias-tv-espana.netlify.app`). Esa es tu
   dashboard, ya público.

Como el repositorio se actualiza solo cada día, y Netlify redespliega automáticamente
cada vez que hay un cambio en el repositorio, el dashboard se mantendrá al día sin que
hagas nada más.

## Si algo no cuadra

- Si `history.json` sale vacío después de correr el workflow a mano: probablemente
  FormulaTV cambió la estructura de su página. Dímelo y ajusto el scraper.
- Si quieres rellenar el histórico de golpe con días pasados (por ejemplo, todo julio),
  dímelo y te preparo una versión del workflow que lo haga con un rango de fechas.
