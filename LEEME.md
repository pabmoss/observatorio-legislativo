# Observatorio Legislativo · V2

**Despacho del H.S. Carlos Eduardo Enríquez Caicedo**

Reconstrucción documental a partir de las fichas consolidadas del **28 de octubre de 2026**. Incluye 22 expedientes, 192 enlaces documentales y 22 archivos Word editables, más el documento consolidado original. No se reivindica verificación en tiempo real.

## Abrir localmente

Abrir `index.html` con un navegador. No exige instalar nada ni conexión para mostrar los datos (los documentos oficiales enlazados sí requieren conexión). También se puede servir la carpeta con cualquier servidor estático HTTPS.

## Arquitectura

- `index.html`, `assets/estilos.css` y `assets/aplicacion.js`: presentación web y funcionalidades de consulta.
- `data/proyectos.json`: **fuente única de datos** del sitio y campos de trazabilidad.
- `data/novedades.json`, `data/estado_fuentes.json`: detecciones y salud del monitoreo.
- `data/proyectos.js`: compilación del JSON para su uso offline; **no editar manualmente**.
- `documentos/`: 22 fichas `.docx` editables y documento de referencia original.
- `herramientas/compilar_datos.py`: validación y compilación de datos.
- `herramientas/generar_documentos.py`: regeneración de los Word a partir del JSON.
- `herramientas/importar_fichas.py`: importación opcional desde un documento de fichas con estructura equivalente.

## Actualización automática de novedades (preparada, pendiente de despliegue)

El flujo `.github/workflows/publicar.yml` incluye una ejecución programada cuatro veces por hora (minutos 7, 22, 37, 52 UTC) y una ejecución manual desde GitHub Actions. GitHub no garantiza la puntualidad de los cron y puede retrasar o desactivar ejecuciones programadas según sus políticas.

Al ejecutarse, `herramientas/recopilar_novedades.py` consulta direcciones públicas oficiales, conserva enlaces nuevos en `data/novedades.json`, registra cuáles fuentes respondieron en `data/estado_fuentes.json` y genera sendos archivos `.js` de publicación. La actualización se confirma en el repositorio y **en ese mismo flujo se publica GitHub Pages**: los commits realizados con `GITHUB_TOKEN` no activan nuevos flujos `push`, por eso la publicación se hace en el mismo proceso.

Las novedades publicadas son **índices de enlace y detección**, con referencias de números de proyectos extraídas de un máximo de un PDF por publicación cuando sea técnicamente posible. No se afirma que se haya leído todo el PDF ni se cambia el estado de los proyectos o las fichas Word sin revisión. Para que se actualicen esos análisis jurídicos automáticamente será necesario un segundo proceso de descarga, lectura, extracción, contraste de fuentes y aprobación editorial, sujeto a pruebas específicas.

### Cobertura y fallos

Las fuentes iniciales incluyen carpetas de las siete comisiones del Senado, comisiones de la Cámara, agenda de Senado, órdenes de plenaria disponibles, sitemap de eventos de Cámara y portal de Gacetas del Congreso de la Imprenta Nacional. Algunos sitios utilizan HTML, formularios JSF, calendarios dinámicos o bloqueos de acceso. **No se certifica cobertura total**: si una fuente falla, el panel “Estado de las fuentes” registra la incidencia. Si todas fallan, el monitor no sobreescribe los archivos de la última consulta exitosa.

Por seguridad, la recopilación sigue únicamente dominios públicos oficiales. El scraping se limita a páginas HTML; descarga únicamente PDFs públicos de tamaño acotado (máximo 6 MB, hasta seis páginas para extracción inicial) ni incluye información reservada. Los enlaces publicados conservan su procedencia. Hay un límite de 750 enlaces en el archivo de novedades, y por tanto es una bitácora de detección reciente, no un archivo legislativo histórico exhaustivo.

### Habilitar

1. Subir el contenido de esta carpeta a la rama `main` del repositorio `pabmoss/observatorio-legislativo`.
2. En **Settings → Actions → General → Workflow permissions**, habilitar permisos de lectura y escritura para el token `GITHUB_TOKEN` del repositorio.
3. En **Settings → Pages**, seleccionar GitHub Actions como fuente de publicación.
4. En **Actions**, ejecutar una vez **Recopilar y publicar Observatorio Legislativo** manualmente y revisar que se publique. El estado de cada fuente aparecerá en la sección “Novedades oficiales”.
5. Confirmar que `data/estado_fuentes.json` tenga `ultima_consulta` válida y que se hayan encontrado documentos en las fuentes accesibles. El primer cron puede tardar o fallar.

La cuenta de GitHub fue identificada, pero el conector ChatGPT recibió un error 403 al intentar crear un archivo el 28/10/2026. **Este paquete no ha sido subido mediante la conexión y no está publicado todavía.** Es necesario autorizar acceso de escritura del conector o subir el ZIP manualmente a GitHub; este último método no cambia permisos del propio conector.

## Actualizar contenido

1. Actualice `data/proyectos.json` sobre la base de soporte oficial, sin presumir votaciones o aprobaciones.
2. Actualice `corte_documental` cuando proceda; registre fuentes, fecha de verificación y modificaciones de estado en cada proyecto.
3. Ejecute desde la carpeta del sitio: `python herramientas/generar_documentos.py` y `python herramientas/compilar_datos.py`.
4. Publique los archivos cambiados en el alojamiento escogido (o active un despliegue automático al recibir cambios). La apariencia no requiere alteraciones.

**Importante:** La tarea de seguimiento horario en ChatGPT **no está conectada** por sí misma a esta carpeta ni a un servidor de publicación. Para actualización autónoma hay que configurar un canal de escritura autenticado, verificar permisos y probar un cambio de extremo a extremo. No es correcto afirmar que la web ya se actualiza automáticamente.

## Publicación y migración

Suba la carpeta completa al alojamiento seleccionado, revise que la portada, la búsqueda, los enlaces, los Word y la carga de datos funcionen por HTTPS. Mantenga el sitio anterior publicado hasta validar el reemplazo. El historial antiguo no puede darse por migrado sin exportarlo.

## Alcance

La información del corte proviene del documento consolidado existente. No se han reabierto ni vuelto a verificar los 192 destinos oficiales durante la preparación de esta V2; los enlaces se mantienen tal como aparecían en la fuente. Las diferencias entre textos radicados, ponencias y eventual estado legal se explican en cada ficha. Este material no sustituye certificaciones oficiales.

## GitHub Pages (despliegue preparado)

Se incluye `.github/workflows/publicar.yml`. Al crear un repositorio con rama `main`, subir estos archivos (incluyendo `.github`) y habilitar **Settings → Pages → Source: GitHub Actions**, cada cambio enviado a `main` que afecte los datos o el código ejecutará:

1. Regeneración de las 22 fichas Word desde `data/proyectos.json` (la cantidad cambia según los registros).
2. Validación del JSON y compilación de `data/proyectos.js`.
3. Publicación del sitio estático mediante GitHub Pages. Se muestran únicamente los archivos públicos del observatorio.

El flujo se puede ejecutar manualmente desde **Actions → Publicar Observatorio Legislativo → Run workflow**. Requiere permisos de Actions y Pages y un repositorio autorizado en GitHub. La página resultante normalmente usa la ruta `https://USUARIO.github.io/REPOSITORIO/`, según la configuración real del repositorio y eventual dominio personalizado. **No hay una URL nueva activa hasta que el despliegue termine con éxito**.

### Qué es y qué no es automático

**Sí**: al subir una versión nueva de `data/proyectos.json` a la rama `main`, GitHub recompila y publica la web automáticamente sin cambiar su diseño.

**Todavía no**: la tarea de revisión horaria de ChatGPT no escribe por sí sola en el repositorio. Para que los descubrimientos de las fuentes oficiales aparezcan en la página sin intervención, falta autorizar al asistente para modificar el repositorio y adaptar la tarea existente a esa operación. No se deben presentar fichas de días previos como actualización en vivo.

### Precaución

Por tratarse de una página pública, evite incluir nombres privados, borradores no publicados, información reservada o contraseñas en el JSON y los documentos. El repositorio y el sitio pueden ser públicos según el plan y la configuración. Conserve la versión previa hasta validar el reemplazo.
