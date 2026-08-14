# Drag-and-drop para reordenar tareas dentro de un `WebKit2.WebView` (GTK3, WebKitGTK 2.52.3)

> **Esta es la mitad documental** de la investigación del ticket
> [#26](https://github.com/dmazzini/pomodoro/issues/26). La mitad empírica —mediciones sobre
> un WebView real— y la recomendación resultante están en
> [`2026-08-14-arrastre-en-webkitgtk.md`](2026-08-14-arrastre-en-webkitgtk.md). Las dos se
> hicieron en paralelo y llegaron a la misma recomendación por caminos distintos.
>
> Tres puntos que este documento dejó abiertos y la medición cerró:
>
> - Su punto 1 («no se ejecutó ninguna prueba empírica… vale la pena hacerla antes de
>   comprometer el diseño, sobre todo para 3.1»): hecho. **El bug 265857 se reprodujo** en
>   comparación emparejada; sin `setData()` no llega ni un `dragover` ni un `drop`.
> - Su punto 4 (si `user-select` sin prefijo está aliasado a `-webkit-user-select`): **no lo
>   está**. `CSS.supports('user-select','none')` devuelve `false` y el estilo computado es
>   `undefined`. Hay que escribir la forma prefijada.
> - El hueco de `dragover` al inicio del arrastre que predice §1.4: se observó desde fuera —
>   18 eventos `drag` frente a 17 `dragover`.
>
> Y un defecto que la medición encontró y que aquí no aparece porque no hay bug upstream que
> lo describa: el arrastre nativo deja atascada la máquina de estados de Pointer Events y se
> come la interacción siguiente.

Investigación contra fuentes primarias: árbol de fuentes de WebKit (tag `webkitgtk-2.52.3`), `Source/WebKit/gtk/NEWS`,
bugs.webkit.org, la referencia de API de WebKitGTK y el HTML Living Standard de WHATWG.

Convención usada en todo el documento:

- **Documentado** = afirmado explícitamente en NEWS, en la referencia de API o en la especificación.
- **Inferido del código** = leído directamente del código fuente en el tag `webkitgtk-2.52.3`; es un hecho sobre el
  código que corre en esa versión, pero no es una garantía de API declarada por upstream.

---

## Respuesta corta

**Recomendación: implementar el reordenamiento con Pointer Events (`pointerdown` / `pointermove` / `pointerup` +
`setPointerCapture()`), no con HTML5 Drag and Drop.**

Razón resumida (el detalle está en las secciones 1, 3 y 4):

1. HTML5 DnD **sí funciona** en `WebKit2.WebView` con GTK3 y no requiere nada del lado GTK del host, pero en el puerto
   GTK **no es un mecanismo puramente interno a la página**: cada arrastre, incluso el que empieza y termina dentro del
   mismo documento, sale al protocolo DnD de GDK (`gtk_drag_begin_with_coordinates`) y vuelve a entrar por las señales
   `drag-motion` / `drag-data-received` del widget
   ([`DragSourceGtk3.cpp` L140](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp#L140),
   [`DropTargetGtk3.cpp` L54-L97](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp#L54)).
   Eso expone la interacción a toda una clase de fallos de plataforma que Pointer Events no tiene.
2. Hay un bug **abierto** que golpea exactamente este caso de uso:
   [bug 265857 — "[GTK] Drag and drop is broken unless `DataTransfer.setData()` is called"](https://bugs.webkit.org/show_bug.cgi?id=265857)
   (NEW, última actividad 2025‑09‑12). El mecanismo es verificable en el código de 2.52.3 y **sigue presente en `main`**.
3. La detección del inicio del arrastre en el puerto GTK es históricamente poco fiable
   ([bug 234850](https://bugs.webkit.org/show_bug.cgi?id=234850), NEW, actividad 2026‑07‑26;
   [bug 64459](https://bugs.webkit.org/show_bug.cgi?id=64459) sobre `gtk-dnd-drag-threshold`), y la vista previa
   del arrastre personalizada aparece desplazada/incorrecta
   ([bug 292058](https://bugs.webkit.org/show_bug.cgi?id=292058), NEW).
4. Asimetría decisiva en cobertura de tests upstream: **el DnD no se puede testear en el puerto GTK**
   ([bug 157179 — "[GTK] Drag and drop can't be tested with WebKitTestRunner"](https://bugs.webkit.org/show_bug.cgi?id=157179),
   REOPENED, actividad 2025‑07‑01), mientras que la suite WPT de `pointerevents` **sí corre en `gtk-wk2`** — por eso
   se archivan fallos de tests individuales concretos como
   [bug 282711](https://bugs.webkit.org/show_bug.cgi?id=282711) y
   [bug 319065](https://bugs.webkit.org/show_bug.cgi?id=319065). Es decir: los bugs de DnD en GTK no tienen red de
   seguridad contra regresiones; los de Pointer Events sí.
5. Pointer Events en 2.52.3 está expuesto **sin ninguna condición de compilación ni flag de preferencia**, incluyendo
   `setPointerCapture()` / `releasePointerCapture()` / `hasPointerCapture()`
   ([`Element+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/Element+PointerEvents.idl),
   [`PointerEvent.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/PointerEvent.idl)).

**Coste de la recomendación.** Pointer Events no da nada gratis: hay que escribir a mano el cálculo del índice de
inserción, el placeholder/hueco visual, el autoscroll cerca de los bordes del contenedor, la cancelación con `Escape`
y el `user-select: none` mientras se arrastra. Estimación: **~100-160 líneas de JS vendorizado sin dependencias**,
frente a ~40-60 líneas con HTML5 DnD. En cambio se elimina toda dependencia del protocolo DnD de GDK, del compositor
(X11/Wayland) y del round-trip asíncrono de datos. Accesibilidad por teclado hay que escribirla igual en ambos
caminos: HTML5 DnD tampoco la da.

**Si de todos modos se elige HTML5 DnD**, la mitigación mínima obligatoria es: en `dragstart` llamar **siempre** a
`event.dataTransfer.setData(...)` con al menos un tipo (`'text/plain'` o un tipo propio tipo
`'application/x-pomodoro-task'`). Sin eso, en WebKitGTK no llegan `dragover` ni `drop` (sección 3.1).

---

## 1. ¿Funciona HTML5 Drag and Drop dentro de un `WebKit2.WebView` embebido en GTK3?

### 1.1 Sí, y está compilado por defecto

`ENABLE_DRAG_SUPPORT` vale 1 por defecto en WebKit
([`Source/WTF/wtf/PlatformEnable.h`, L231-L232](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/PlatformEnable.h#L231);
verificado en `main` — ver "Lo que no se pudo establecer"). El puerto GTK crea la infraestructura de DnD en el
constructor del widget, bajo `#if ENABLE(DRAG_SUPPORT)`
([`WebKitWebViewBase.cpp` L2341](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/WebKitWebViewBase.cpp#L2341)):

```cpp
static void webkitWebViewBaseConstructed(GObject* object)
{
    ...
#if ENABLE(DRAG_SUPPORT)
    priv->dropTarget = makeUnique<DropTarget>(viewWidget);
#endif
```

y el lado origen se crea perezosamente cuando WebCore pide iniciar un arrastre
([`WebKitWebViewBase.cpp` L2600](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/WebKitWebViewBase.cpp#L2600)):

```cpp
void webkitWebViewBaseStartDrag(WebKitWebViewBase* webViewBase, SelectionData&& selectionData, ...)
{
    WebKitWebViewBasePrivate* priv = webViewBase->priv;
    if (!priv->dragSource)
        priv->dragSource = makeUnique<DragSource>(GTK_WIDGET(webViewBase));
    priv->dragSource->begin(...);
```

(Inferido del código, tag `webkitgtk-2.52.3`.)

### 1.2 Desde qué versión

**Documentado** en `Source/WebKit/gtk/NEWS`
([NEWS @ 2.52.3](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/gtk/NEWS)):

| Versión | Entrada de NEWS | Relevancia |
|---|---|---|
| WebKitGTK+ 1.1.13 | "Drag support has landed, meaning you can start playing with HTML5 drag and drop support; drop support is still missing." | WebKit**1**, solo origen |
| WebKitGTK+ 1.7.1 | "Implement drag and drop support in WebKit2." | **Primera versión con DnD en `WebKit2.WebView`** |
| WebKitGTK+ 2.3.3 | "Support custom types for drag and drop data." | `dataTransfer.setData('application/x-mitipo', …)` funciona desde aquí |
| WebKitGTK 2.51.3 | "Fix drag-and-drop when dropping folders from a file manager into a web view." | Arrastre externo; incluido en 2.52.x |

Para el propósito práctico: DnD HTML5 está disponible en `WebKit2.WebView` desde **1.7.1**, y los tipos MIME
personalizados (imprescindibles para un reorder limpio) desde **2.3.3**. 2.52.3 está muy por encima de ambos.

Complemento: `DataTransferItemList` / `DataTransferItem` (la API `dataTransfer.items`) está detrás de la preferencia
`DataTransferItemsEnabled`, cuyo default **es `true` para `PLATFORM(GTK)`**
([`UnifiedWebPreferences.yaml` L2285-L2295](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml#L2285)):

```yaml
DataTransferItemsEnabled:
  type: bool
  status: embedder
  defaultValue:
    WebKit:
      "PLATFORM(COCOA) || PLATFORM(GTK) || PLATFORM(WPE)": true
      default: false
```

Esto deja **obsoleto** el [bug 98940 "[GTK][WPE] Add support for DataTransferItem API"](https://bugs.webkit.org/show_bug.cgi?id=98940)
(sigue NEW pero sin actividad desde 2019, y el default contradice su premisa). De todos modos, para un reorder
`getData()` / `setData()` alcanza y es más portable.

### 1.3 ¿Hay que registrar el widget host como origen/destino GTK? **No — y hacerlo es peligroso**

WebKitGTK **lo hace por sí mismo**. El constructor de `DropTarget` llama a `gtk_drag_dest_set()` sobre el propio widget
de la vista y conecta las cuatro señales GTK de destino
([`DropTargetGtk3.cpp` L54-L97](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp#L54)):

```cpp
gtk_drag_dest_set(m_webView, static_cast<GtkDestDefaults>(0), nullptr, 0,
    static_cast<GdkDragAction>(GDK_ACTION_COPY | GDK_ACTION_MOVE | GDK_ACTION_LINK));
gtk_drag_dest_set_target_list(m_webView, list.get());

g_signal_connect_after(m_webView, "drag-motion", ...);
g_signal_connect_after(m_webView, "drag-leave", ...);
g_signal_connect_after(m_webView, "drag-drop", ...);
g_signal_connect_after(m_webView, "drag-data-received", ...);
```

Y el lado origen llama a `gtk_drag_begin_with_coordinates()` sobre el mismo widget
([`DragSourceGtk3.cpp` L140](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp#L140)).

Coherentemente, la referencia de API de WebKitGTK **no expone ninguna señal ni método de drag/drop en
`WebKitWebView`**: las únicas señales `drag-*` que aparecen son las heredadas de `GtkWidget`
([`class.WebView.html`](https://webkitgtk.org/reference/webkit2gtk/stable/class.WebView.html)). Es decir: **no existe
API pública de DnD que el embebedor deba usar ni configurar** — es todo interno. (Documentado por omisión en la
referencia; confirmado en código.)

**Aviso concreto para `pomodoro.py`: no llamar a `gtk_drag_source_set()` / `gtk_drag_dest_set()` /
`gtk_drag_source_unset()` sobre el `WebKit2.WebView`.** Está reportado que hacerlo rompe el estado interno de WebKit
y dispara un assert/abort:
[bug 200297 — "[GTK] Cannot disable drag-and-drop functionality with `gtk_drag_source_set()`/`gtk_drag_source_unset()`
inside a `WebKitWebView`"](https://bugs.webkit.org/show_bug.cgi?id=200297) (NEW). Del comentario de Michael Catanzaro
en ese bug: *"I guess we didn't consider that applications could use these functions. Of course using GTK public APIs
shouldn't cause WebKit to crash, so we'll need to reconsider these assertions."* El código actual de `pomodoro.py`
no toca esas funciones, así que no hay nada que cambiar; solo no introducirlas.

### 1.4 El punto arquitectónico importante: el DnD intra-página **no** se resuelve dentro de WebKit

Esto es **inferido del código** (tag 2.52.3), y es la razón de fondo de la recomendación.

Cuando la página inicia un arrastre, WebKit no simula nada internamente: llama a `gtk_drag_begin_with_coordinates()`,
publicando un `GtkTargetList` en el protocolo DnD del sistema
([`DragSourceGtk3.cpp` L124-L140](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp#L124)).
Cuando el puntero vuelve a entrar en la propia vista, el arrastre llega como una señal GTK `drag-motion`, y WebKit
tiene que **pedir los datos de vuelta de forma asíncrona** con `gtk_drag_get_data()` antes de poder notificar al web
process ([`DropTargetGtk3.cpp`, `DropTarget::accept()`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp#L104)):

```cpp
// WebCore needs the selection data to decide, so we need to preload the
// data of targets we support. Once all data requests are done we start
// notifying the web process about the DND events.
```

Consecuencias observables para un reorder de lista:

- Los primeros `dragover` tras entrar en la vista **se descartan**: `DropTarget::update()` hace
  `if (m_dataRequestCount || !m_selectionData) return;` mientras la carga asíncrona está en curso. Hay un hueco al
  inicio del arrastre en el que la página no recibe eventos.
- Todo el arrastre depende del protocolo DnD del compositor. Hay un bug abierto de flakiness específico de Wayland:
  [bug 198915 — "[GTK] Drag and drop sometimes not working on wayland"](https://bugs.webkit.org/show_bug.cgi?id=198915) (NEW).
- La imagen de arrastre se genera como bitmap y se instala con `gtk_drag_set_icon_surface()` / `gtk_drag_set_icon_default()`
  ([`DragSourceGtk3.cpp` L141-L147](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp#L141)),
  es decir: el "fantasma" del arrastre es una superficie del sistema, no un elemento DOM que puedas estilar
  libremente. De ahí [bug 292058](https://bugs.webkit.org/show_bug.cgi?id=292058).

### 1.5 GTK3 vs GTK4, y la serie 2.4x/2.5x

Existen implementaciones **separadas** por versión de GTK, seleccionadas en compilación:

- GTK3: [`DropTargetGtk3.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp) /
  [`DragSourceGtk3.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp)
  (este último termina con `#endif // ENABLE(DRAG_SUPPORT) && !USE(GTK4)`), basadas en `GdkDragContext`,
  `GtkTargetList`, `gtk_drag_get_data()`.
- GTK4: `DropTargetGtk4.cpp` / `DragSourceGtk4.cpp`, basadas en `GdkDrop`, `gdk_drop_get_formats()`,
  `gdk_drop_read_value_async()`.

**Esta app usa `gi.require_version('Gtk', '3.0')` + `WebKit2` 4.1 → el binario `libwebkit2gtk-4.1-0` es el
build GTK3, y por lo tanto la ruta de código relevante es `*Gtk3.cpp`.** Corolario práctico: los bugs reportados
específicamente contra GTK4 (p. ej. [bug 320301](https://bugs.webkit.org/show_bug.cgi?id=320301), reportado sobre
"WebKitGTK 2.52.5 + GTK 4.22.4") **no se pueden asumir aplicables tal cual** a esta app, ni al revés.

Sobre las series: NEWS registra arreglos de DnD dispersos y con años de separación (2.29.2, 2.35.3, 2.41.5 —este
último explícitamente "in GTK4"—, 2.51.3). No hay en NEWS ninguna entrada que indique un rework o endurecimiento del
DnD en la serie 2.5x. Las entradas de 2.52.0 → 2.52.3 no mencionan drag and drop en absoluto
([NEWS @ 2.52.3](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/gtk/NEWS)).

---

## 2. ¿Cambia algo cargar desde `file://` para el DnD o para `DataTransfer`?

**Respuesta: no, para el caso (a) arrastre intra-página. Sí, indirectamente, para el caso (b) archivos / cruce de
frontera de aplicación — pero por otras razones, no por la política de origen.**

### 2.a Arrastre intra-página (los datos nunca salen del documento)

La única comprobación de origen en el pipeline de DnD de WebCore está en `DragController::tryDocumentDrag()`
([`DragController.cpp` L434](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/DragController.cpp#L434)):

```cpp
if (m_dragInitiator && !m_documentUnderMouse->protectedSecurityOrigin()->canReceiveDragData(m_dragInitiator->protectedSecurityOrigin()))
    return DragHandlingMethod::None;
```

y `canReceiveDragData` permite explícitamente tanto el mismo origen como **local → local**
([`SecurityOrigin.cpp` L333-L342](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/SecurityOrigin.cpp#L333)):

```cpp
bool SecurityOrigin::canReceiveDragData(const SecurityOrigin& dragInitiator) const
{
    if (this == &dragInitiator)
        return true;

    if (dragInitiator.isLocal() && isLocal())
        return true;

    return isSameOriginDomain(dragInitiator);
}
```

Para un arrastre dentro del mismo documento la primera rama ya devuelve `true`. Y además, en WebKit un documento
`file://` **no** es un origen opaco: `SecurityOriginData::shouldTreatAsOpaqueOrigin()` devuelve `false` para esquemas
"especiales" ([`SecurityOriginData.cpp` L208](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/SecurityOriginData.cpp#L208)),
y `file` es un esquema especial ([`URL.cpp` L114-L123](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WTF/wtf/URL.cpp#L114)):

```cpp
bool URL::hasSpecialScheme() const
{
    // https://url.spec.whatwg.org/#special-scheme
    return protocolIs("ftp"_s) || protocolIsFile() || protocolIs("http"_s)
        || protocolIs("https"_s) || protocolIs("ws"_s) || protocolIs("wss"_s);
}
```

Y se marca como **local**: `m_isLocal = LegacySchemeRegistry::shouldTreatURLSchemeAsLocal(m_data.protocol())`
([`SecurityOrigin.cpp` L115](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/SecurityOrigin.cpp#L115)),
que es precisamente la propiedad que `canReceiveDragData` whitelistea.

**Conclusión (inferida del código, tag 2.52.3): `file://` está en el lado bueno de la única comprobación de origen
que hace el DnD. No hace falta `allow-file-access-from-file-urls` ni `allow-universal-access-from-file-urls` para
que el DnD intra-página funcione.** De hecho **no se encontró ninguna fuente primaria que ate el comportamiento de
DnD o de `DataTransfer` a esos dos settings** — ver "Lo que no se pudo establecer".

Del lado de la especificación, el modelo de DnD de WHATWG tampoco introduce ninguna restricción por origen para
arrastres dentro de un documento. La sección de seguridad
([HTML §6.11.8 "Security risks in the drag-and-drop model"](https://html.spec.whatwg.org/multipage/dnd.html#security-risks-in-the-drag-and-drop-model))
trata otro problema: que los datos no se puedan leer antes del `drop`.

> "User agents must not make the data added to the `DataTransfer` object during the `dragstart` event available to
> scripts until the `drop` event, because otherwise, if a user were to drag sensitive information from one document to
> a second document, crossing a hostile third document in the process, the hostile document could intercept the data."

Esto es el **modo protegido** del drag data store, y es el gotcha número uno de cualquier reorder
([HTML §6.11.2 "The drag data store"](https://html.spec.whatwg.org/multipage/dnd.html#the-drag-data-store)):

> "**Read/write mode** — For the `dragstart` event. New data can be added to the drag data store.
> **Read-only mode** — For the `drop` event. The list of items representing dragged data can be read, including the
> data. No new data can be added.
> **Protected mode** — For all other events. The formats and kinds in the drag data store list of items representing
> dragged data can be enumerated, but the data itself is unavailable and no new data can be added."

Y en `getData()` ([HTML §6.11.3](https://html.spec.whatwg.org/multipage/dnd.html#dom-datatransfer-getdata)):

> "If the drag data store's mode is the protected mode, then return the empty string."

**Implicación de diseño, independiente de WebKitGTK y de `file://`:** durante `dragover` **no se puede leer el id de la
tarea arrastrada**. `dataTransfer.types` sí se puede enumerar, pero `getData()` devuelve `""`. Por eso todo reorder
con HTML5 DnD tiene que guardar el elemento arrastrado en una variable de módulo en `dragstart`. La propia
especificación lo hace así en su ejemplo de reordenar una lista `<ol>`
([HTML §6.11.1 Introduction](https://html.spec.whatwg.org/multipage/dnd.html#dnd)).

### 2.b Arrastres con archivos o que cruzan la frontera de proceso/aplicación

Aquí sí hay diferencias, pero **no dependen del origen `file://` del documento**:

- WebCore revoca el acceso a archivos cuando el frame bajo el puntero no puede aceptar la imagen arrastrada como
  archivo: `DragController::disallowFileAccessIfNeeded()`
  ([`DragController.cpp` L362-L367](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/DragController.cpp#L362)).
- La propiedad `allow-file-access-from-file-urls` de WebKitGTK está documentada como algo sobre **peticiones
  cross-origin a otros recursos file**, no sobre DnD
  ([referencia de API](https://webkitgtk.org/reference/webkit2gtk/stable/property.Settings.allow-file-access-from-file-urls.html)):
  > "Whether file access is allowed from file URLs. By default, when something is loaded in a `WebKitWebView` using a
  > file URI, cross origin requests to other file resources are not allowed." (default: `FALSE`)
- Soltar archivos desde el gestor de archivos hacia una página está **roto y abierto** en la serie 2.52:
  [bug 320301 — "[GTK] Cannot drag and drop (DnD) upload files to a standard HTML file upload drop zone"](https://bugs.webkit.org/show_bug.cgi?id=320301)
  (NEW, reportado sobre WebKitGTK 2.52.5 + GTK 4.22.4). También
  [bug 204281](https://bugs.webkit.org/show_bug.cgi?id=204281) (NEW) y
  [bug 52094](https://bugs.webkit.org/show_bug.cgi?id=52094) (NEW).

**Para este proyecto esto es irrelevante:** un reorder de lista es puramente caso (a). Solo importa como señal de la
salud general del subsistema.

---

## 3. Bugs upstream conocidos que golpearían un reorder de lista

Todo lo siguiente sigue **abierto** (`NEW` / `REOPENED`) al día de hoy; ninguno tiene una entrada de fix en el NEWS
de la serie 2.5x, es decir **2.52.3 no está en el lado bueno de ningún arreglo relevante**, porque no hay arreglo.

| Bug | Estado | Última actividad | Por qué importa para un reorder |
|---|---|---|---|
| [265857](https://bugs.webkit.org/show_bug.cgi?id=265857) "[GTK] Drag and drop is broken unless `DataTransfer.setData()` is called" | NEW | 2025‑09‑12 | **Crítico.** Sin `setData()` no hay `dragover` ni `drop`. Ver 3.1 |
| [234850](https://bugs.webkit.org/show_bug.cgi?id=234850) "[GTK] Drag and drop operations within an Epiphany web app (Google Calendar) are unreliable / fail randomly" | NEW | 2026‑07‑26 | El arrastre se interpreta como **selección de texto** en lugar de arrastre, de forma aleatoria |
| [64459](https://bugs.webkit.org/show_bug.cgi?id=64459) "[GTK] `WebKitWebView` should obey `gtk-dnd-drag-threshold` setting" | UNCONFIRMED | 2017‑03‑11 | El umbral de arrastre de GTK se ignora: causa probable del anterior |
| [292058](https://bugs.webkit.org/show_bug.cgi?id=292058) "[GTK] Incorrect and offset custom drag-and-drop previews on Trello.com and similar implementations" | NEW | 2025‑04‑25 | **Trello es literalmente el caso de uso**: `setDragImage()` sale desplazado |
| [198915](https://bugs.webkit.org/show_bug.cgi?id=198915) "[GTK] Drag and drop sometimes not working on wayland" | NEW | 2019‑06‑17 | Flakiness dependiente del compositor |
| [157179](https://bugs.webkit.org/show_bug.cgi?id=157179) "[GTK] Drag and drop can't be tested with WebKitTestRunner" | REOPENED | 2025‑07‑01 | **Sin cobertura de tests → sin red anti-regresión** |
| [200297](https://bugs.webkit.org/show_bug.cgi?id=200297) "[GTK] Cannot disable DnD with `gtk_drag_source_set()`…" | NEW | 2019‑08‑01 | No mezclar API GTK de DnD con la vista (sección 1.3) |
| [191481](https://bugs.webkit.org/show_bug.cgi?id=191481) "REGRESSION(r223264): [GTK] Unable to drag documents on Google Drive" | NEW | 2018‑11‑13 | Precedente de regresión de DnD no detectada |
| [299694](https://bugs.webkit.org/show_bug.cgi?id=299694) "[GTK] Crash on web.whatsapp.com on drag-and-drop" | NEW | 2025‑09‑29 | El DnD sigue produciendo crashes del proceso en 2025 |
| [318429](https://bugs.webkit.org/show_bug.cgi?id=318429) "WhatsApp Web drag-and-drop feature does not work" | NEW | 2026‑07‑09 | Reporte de 2026 |
| [245783](https://bugs.webkit.org/show_bug.cgi?id=245783) "[GTK] Slow performance issues tracker bug (scrolling, animations, drag & drop, input)" | NEW | 2026‑07‑23 | Meta-bug de jank que menciona explícitamente drag & drop |

Los tres primeros y el 157179 son los que sostienen la recomendación.

### 3.1 Bug 265857 verificado en el código de 2.52.3 (y todavía en `main`)

Este bug tiene el diagnóstico completo y es **confirmable línea por línea** en el tag que corre esta máquina.

**Lado origen.** `DragSource::begin()` solo publica un target GTK por cada tipo de dato que la página realmente puso
en el `DataTransfer` ([`DragSourceGtk3.cpp` L124-L140](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp#L124)):

```cpp
GRefPtr<GtkTargetList> list = adoptGRef(gtk_target_list_new(nullptr, 0));
if (m_selectionData->hasText())       gtk_target_list_add_text_targets(list.get(), DragTargetType::Text);
if (m_selectionData->hasMarkup())     gtk_target_list_add(list.get(), ... "text/html" ...);
if (m_selectionData->hasURIList())    gtk_target_list_add_uri_targets(list.get(), ...);
if (m_selectionData->hasURL())        gtk_target_list_add(list.get(), ... "_NETSCAPE_URL" ...);
if (m_selectionData->hasImage())      gtk_target_list_add_image_targets(list.get(), ...);
if (m_selectionData->canSmartReplace()) gtk_target_list_add(list.get(), ... "smartpaste" ...);
if (m_selectionData->hasCustomData()) gtk_target_list_add(list.get(), ... PasteboardCustomData::gtkType() ...);

m_drag = gtk_drag_begin_with_coordinates(m_webView, list.get(), ...);
```

Si el `dragstart` no llamó a `setData()`, **la lista de targets queda vacía**.

**Lado destino.** `DropTarget::accept()` solo carga datos si el arrastre anuncia al menos uno de seis targets
conocidos, y si no, **abandona**
([`DropTargetGtk3.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp#L104)):

```cpp
static const char* const supportedTargets[] = {
    "text/plain;charset=utf-8", "text/html", "_NETSCAPE_URL",
    "text/uri-list", "application/vnd.webkitgtk.smartpaste",
    "org.webkitgtk.WebKit.custom-pasteboard-data"
};
...
if (targets.isEmpty())
    return;                       // m_selectionData queda en std::nullopt
```

Con `m_selectionData` sin valor, los dos caminos que notificarían a la página se cortan:

```cpp
void DropTarget::update(IntPoint&& position, unsigned time)
{
    if (m_dataRequestCount || !m_selectionData)
        return;                   // → no se emite dragover
    ...
}

void DropTarget::drop(IntPoint&& position, unsigned time)
{
    // If we don't have data at this point, allow the leave timer to fire, ending the drop operation.
    if (!m_selectionData)
        return;                   // → no se emite drop
    ...
}
```

Este `if (targets.isEmpty()) return;` **sigue en `main`**
([`DropTargetGtk3.cpp` @ main, L140-L141](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp#L140)),
y la variante GTK4 tiene el bail equivalente (`if (!data) { didLoadData(); return; }` en
[`DropTargetGtk4.cpp` @ main](https://github.com/WebKit/WebKit/blob/main/Source/WebKit/UIProcess/API/gtk/DropTargetGtk4.cpp#L185)).
**No hay fix ni en 2.52.3 ni en tronco.**

Del bug, comentario #1 (el reportero, tras leer el mismo código):
> "I have tried modifying Mozillas provided example and added a line like
> `event.dataTransfer.setData("text/plain", "vier");` and the drop worked afterwards."

Y comentario #2, de Michael Catanzaro (mantenedor de WebKitGTK): *"But I can reproduce the behavior you've
described."*

**Mitigación (100% en la página, sin build):** en `dragstart` llamar siempre a `setData`. Cualquiera de estas dos
opciones alcanza para que la lista de targets no quede vacía, porque una cae en la rama `hasText()` y la otra en la
rama `hasCustomData()` (que corresponde al target `org.webkitgtk.WebKit.custom-pasteboard-data`, incluido en
`supportedTargets`):

```js
ev.dataTransfer.setData('text/plain', tarea.id);                    // rama hasText()
ev.dataTransfer.setData('application/x-pomodoro-tarea', tarea.id);  // rama hasCustomData()
```

Nota: el segundo funciona "desde 2.3.3" según NEWS ("Support custom types for drag and drop data"), y el ver el
target custom en la lista `supportedTargets` de 2.52.3 lo confirma en código.

### 3.2 Lo que **no** encontré (y es relevante que no exista)

- No hay ninguna entrada en el NEWS de 2.52.0 → 2.52.3 relacionada con drag and drop.
- No hay bug abierto que describa un fallo intra-página de reorder *cuando sí se llama a `setData()`*. Es decir: con
  la mitigación de 3.1 aplicada, no tengo evidencia primaria de un bug bloqueante restante — solo la fiabilidad
  general (234850 / 64459 / 198915) y la ausencia de tests (157179).

---

## 4. Pointer Events como camino recomendado

### 4.1 Soporte en 2.52.3: completo y sin flags

**Inferido del código, tag `webkitgtk-2.52.3` (que es exactamente la versión de esta máquina):**

`setPointerCapture` / `releasePointerCapture` / `hasPointerCapture` se declaran en una `partial interface Element`
**sin `Conditional=` ni `EnabledBySetting=`**
([`Element+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/Element+PointerEvents.idl)):

```webidl
// https://w3c.github.io/pointerevents/#extensions-to-the-element-interface
partial interface Element {
    undefined setPointerCapture (long pointerId);
    undefined releasePointerCapture (long pointerId);
    boolean hasPointerCapture (long pointerId);
};
```

La interfaz `PointerEvent` tampoco tiene condición ni flag; solo tienen `EnabledBySetting` atributos accesorios que
no necesitamos (`altitudeAngle`, `azimuthAngle`, `getCoalescedEvents()`, `getPredictedEvents()`)
([`PointerEvent.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/PointerEvent.idl)).

Los handlers `onpointerdown` / `onpointermove` / `onpointerup` / `onpointercancel` / `onpointerover` / `onpointerout`
/ `onpointerenter` / `onpointerleave` están todos declarados sin condición
([`GlobalEventHandlers+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/GlobalEventHandlers+PointerEvents.idl)).

**Un solo hueco relevante:** `onpointerrawupdate` está **comentado** en ese IDL (línea 33), es decir
`pointerrawupdate` **no está disponible**. No lo necesitamos — `pointermove` alcanza.

Además, `PointerEvents` **no aparece como preferencia** en
[`UnifiedWebPreferences.yaml` @ 2.52.3](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml):
no hay un `PointerEventsEnabled` que un embebedor pueda apagar. La única forma de que se rompa sería un build ad hoc,
y este es el paquete de Ubuntu.

**Documentado** en NEWS, aunque solo lo relativo a *touch*
([NEWS @ 2.52.3, sección WebKitGTK 2.51.3](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/gtk/NEWS)):

- "Enable Pointer Events for touch input."
- "Fix PointerEvent behaviour for mouse events synthesized from touch inputs."

2.51.3 precede a 2.52.0, así que **2.52.3 incluye ambos**. Para un desktop con mouse esto es un extra, no un
requisito. Como consecuencia, el
[bug 204115 "[GTK][WPE][Pointer Events] Support for pointerType touch or pen"](https://bugs.webkit.org/show_bug.cgi?id=204115)
(NEW, sin actividad desde 2021) parece **superado** por esa entrada de NEWS, aunque no fue cerrado.

### 4.2 Caveats específicos del puerto GTK: casi ninguno

Busqué en bugs.webkit.org por `GTK pointer events` y por `setPointerCapture`. Resultado:

- **Los bugs serios de pointer capture son de iOS, no de GTK.** Verifiqué los dos que asustan por el título:
  [bug 270722 "PointerEvents randomly stop firing for mouse events"](https://bugs.webkit.org/show_bug.cgi?id=270722)
  es iOS/iPadOS (se dispara al abrir el dock o Split View), y
  [bug 276287 "First PointerMove event after setPointerCapture is not captured"](https://bugs.webkit.org/show_bug.cgi?id=276287)
  también está reportado sobre iOS 17. **Ninguno menciona el puerto GTK.**
- El único bug GTK+pointer-capture es un **fallo de test en build Debug**:
  [bug 319065 "[GTK] `imported/w3c/web-platform-tests/pointerevents/pointerevent_setpointercapture_relatedtarget.html`
  fails in Debug"](https://bugs.webkit.org/show_bug.cgi?id=319065) (NEW, 2026‑07‑10). Un build Debug de la suite WPT
  no es representativo de un Ubuntu con el paquete Release.
- Otros: [bug 282711](https://bugs.webkit.org/show_bug.cgi?id=282711) es
  `pointerevent_touch-action-keyboard.html` en `gtk-wk2` — un caso de `touch-action` + teclado, ajeno a un drag con
  mouse.

**El hecho estructural es el mejor argumento:** que existan bugs de *tests WPT individuales de pointerevents en
`gtk-wk2`* demuestra que **la suite de Pointer Events corre en CI del puerto GTK**. Contrastar con
[bug 157179](https://bugs.webkit.org/show_bug.cgi?id=157179): el DnD **no se puede testear** en GTK.

### 4.3 `touch-action` y `user-select`

Ambos están implementados en 2.52.3
([`CSSProperties.json`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/css/CSSProperties.json)):

- `touch-action`: valores soportados `auto | none | manipulation | pan-x | pan-y | pinch-zoom`. Los valores
  direccionales finos **`pan-left` / `pan-right` / `pan-up` / `pan-down` están marcados `"status": "unimplemented"`**.
  Para nuestro caso `touch-action: none` sobre el handle de arrastre es suficiente y está soportado.
- `user-select`: se declara como `-webkit-user-select` con `"status": "experimental"` y valores
  `auto | text | none | all` (`contain` sin implementar). **Usar el prefijo `-webkit-user-select: none` además del
  no prefijado**, porque en la fuente de 2.52.3 la entrada que existe es la prefijada — ver "Lo que no se pudo
  establecer" sobre si `user-select` sin prefijo está aliasado.
- `-webkit-user-drag` también existe (`auto | none | element`, `"status": "non-standard"`). Útil como cinturón extra:
  `-webkit-user-drag: none` en los items evita que WebKit inicie un arrastre nativo compitiendo con nuestros
  Pointer Events.

Relevancia para un reorder con Pointer Events: `touch-action: none` + `user-select: none` en el handle evitan que el
gesto se convierta en scroll o en selección de texto. Esto es precisamente el fallo que reporta
[bug 234850](https://bugs.webkit.org/show_bug.cgi?id=234850) para el camino HTML5 DnD, donde **no hay forma
equivalente de suprimirlo desde la página**.

### 4.4 Autoscroll manual (scrollear el contenedor cerca del borde)

**No encontré ninguna fuente primaria que indique que algo en este WebView rompa un autoscroll manual.** Lo que sí es
relevante y está documentado:

- `scroll-behavior` está implementado con valores `auto | smooth`
  ([`CSSProperties.json`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/css/CSSProperties.json)).
  **Consecuencia de diseño:** si el contenedor de la lista tiene `scroll-behavior: smooth`, cada escritura de
  `scrollTop` en un bucle `requestAnimationFrame` arrancará una animación de scroll que pelea con la siguiente
  escritura. Para autoscroll: `scroll-behavior: auto` en el contenedor y escribir `scrollTop` directamente
  (o usar `scrollBy({ behavior: 'instant' })`).
- WebKitGTK 2.52.0 incluye "Ensure that `scrollend` events are correctly emitted after scroll animations" y
  "Make scrolling with touch input smoother for small movements"
  ([NEWS @ 2.52.3](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/gtk/NEWS)) — evidencia de que
  el scroll de 2.52 tiene animaciones asíncronas propias, otra razón para no mezclar `smooth` con autoscroll manual.
- Existe un meta-bug abierto de jank en GTK que menciona scrolling y drag & drop:
  [bug 245783](https://bugs.webkit.org/show_bug.cgi?id=245783) (NEW, 2026‑07‑23). Es un tracker de rendimiento en
  sitios web reales, no una limitación de API. Para una lista de tareas de una app local, el riesgo práctico es bajo.
- Ventaja concreta de Pointer Events aquí: con `setPointerCapture()` los `pointermove` siguen llegando al elemento
  capturado aunque el puntero salga del contenedor o de la ventana, lo que es exactamente lo que un autoscroll de
  borde necesita. Con HTML5 DnD, los `dragover` los emite el destino, y en GTK dependen del round-trip por GDK
  descrito en 1.4.

---

## 5. ¿Algo impide vendorizar una implementación propia de reorder (sin librería, sin build)?

**No.** Todo lo que necesita una implementación a mano existe en 2.52.3 y no requiere build ni red:

| Necesidad | Estado en WebKitGTK 2.52.3 | Fuente |
|---|---|---|
| `pointerdown` / `pointermove` / `pointerup` / `pointercancel` | Disponible, sin flag | [`GlobalEventHandlers+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/GlobalEventHandlers+PointerEvents.idl) |
| `setPointerCapture()` / `releasePointerCapture()` / `hasPointerCapture()` | Disponible, sin flag | [`Element+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/Element+PointerEvents.idl) |
| `touch-action: none`, `-webkit-user-select: none`, `-webkit-user-drag: none` | Implementados | [`CSSProperties.json`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/css/CSSProperties.json) |
| JavaScript habilitado en la vista | `settings.set_enable_javascript(True)` ya está en `/home/damian/dev/pomodoro/pomodoro.py` (línea 31) | código del repo |
| Debug desde terminal | `settings.set_enable_write_console_messages_to_stdout(True)` ya está (línea 32) | código del repo |

Restricciones a respetar, todas ya conocidas por el equipo:

- **Sin ES modules.** El archivo nuevo debe cargarse como script clásico (`<script src="reorder.js"></script>`,
  sin `type="module"`, sin `import` / `export`), igual que el `historial.js` que ya existe en el repo.
- **Sin red.** Nada de CDNs ni `fetch()`. Cero dependencias; todo el estado sale del DOM y se persiste por el mismo
  canal que ya usa la app.
- **No tocar la API GTK de DnD del host** (`gtk_drag_source_set` / `gtk_drag_dest_set`), por
  [bug 200297](https://bugs.webkit.org/show_bug.cgi?id=200297). El `pomodoro.py` actual no las usa.

No se encontró ningún límite adicional impuesto por el WebView: no hay CSP inyectado por WebKitGTK para `file://`, y
ninguna de las APIs listadas está detrás de una preferencia que el embebedor deba habilitar.

---

## Lo que no se pudo establecer

Marcado explícitamente para que nadie construya sobre estos puntos:

1. **No se ejecutó ninguna prueba empírica en la máquina objetivo.** Toda esta investigación es lectura de fuentes
   primarias sobre el tag `webkitgtk-2.52.3`. Las conclusiones de código son sólidas sobre *qué hace el código*, pero
   la verificación de un caso real (arrastrar un `<li>` de la lista de tareas y ver si llega `drop`) sigue pendiente.
   **Es una prueba de 15 minutos y vale la pena hacerla antes de comprometer el diseño**, sobre todo para 3.1.
2. **El valor de `ENABLE_DRAG_SUPPORT` se verificó en `main`, no en el tag 2.52.3**
   ([`PlatformEnable.h` @ main L231](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/PlatformEnable.h#L231)).
   En el tag 2.52.3 sí se verificó que `DropTarget` se construye bajo `#if ENABLE(DRAG_SUPPORT)`, y que los archivos
   `DropTargetGtk3.cpp` / `DragSourceGtk3.cpp` existen en ese tag; el default exacto del flag en ese tag no se releyó.
   En la práctica está fuera de duda (todos los bugs de DnD de la sección 3 son contra builds de distro), pero el dato
   citado es de `main`.
3. **No se pudo establecer en qué versión de WebKitGTK Pointer Events pasó a estar disponible para *mouse*.** NEWS
   solo menciona Pointer Events dos veces, ambas en 2.51.3 y ambas sobre *touch*. Lo que sí está establecido: en el
   tag 2.52.3 el IDL es incondicional y no existe preferencia `PointerEventsEnabled`. Para la decisión de diseño
   alcanza, porque la versión objetivo es exactamente 2.52.3.
4. **No se pudo establecer si `user-select` sin prefijo está aliasado a `-webkit-user-select` en 2.52.3.** En
   `CSSProperties.json` la entrada que existe es `-webkit-user-select`; no se localizó una declaración de alias.
   Mitigación trivial: declarar ambas propiedades.
5. **No se pudo establecer el default de `overscrollBehaviorEnabled` para el puerto GTK.** `overscroll-behavior`
   existe en `CSSProperties.json` pero con `"settings-flag": "overscrollBehaviorEnabled"`, y no se consultó su valor
   por plataforma. No afecta la recomendación; solo significa que no hay que apoyarse en `overscroll-behavior` para el
   autoscroll.
6. **No se encontró ninguna fuente primaria que ate el comportamiento de DnD o de `DataTransfer` a
   `allow-file-access-from-file-urls` o `allow-universal-access-from-file-urls`.** Se buscó en el código de
   `DragController` / `SecurityOrigin` / `SecurityOriginData` y en la referencia de API. Lo que se estableció es lo
   contrario: la única comprobación de origen del DnD (`canReceiveDragData`) permite explícitamente local→local. Pero
   "no encontré evidencia de que importe" no es lo mismo que "está documentado que no importa".
7. **No se investigó por qué fallan los ES modules en esta app.** El brief lo da como dato ("origen `file://` opaco").
   Nota de precisión, no de contradicción: en el código de 2.52.3 un documento `file://` **no** produce un origen
   opaco (`shouldTreatAsOpaqueOrigin()` devuelve `false` para esquemas especiales, y `file` es especial). El fallo de
   los módulos es casi seguro la política CORS sobre fetches `file://` (que es de lo que habla
   `allow-file-access-from-file-urls`), un mecanismo distinto. **No se estableció desde fuentes primarias** cuál es la
   causa exacta, y no cambia ninguna conclusión de este documento.
8. **No se pudo determinar si los bugs reportados contra GTK4 aplican al build GTK3 (`webkit2gtk-4.1`).** Las dos
   implementaciones son archivos separados (`*Gtk3.cpp` vs `*Gtk4.cpp`) con APIs GDK distintas. Los bugs 320301
   (2.52.5 + GTK 4.22.4) y 265857 (reproducido por el mantenedor en Epiphany, que es GTK4) se reportan contra GTK4.
   Para 265857 **sí** se verificó independientemente que el mismo mecanismo existe en el código GTK3 de 2.52.3
   (sección 3.1); para los demás, no.
9. **La referencia de API de WebKitGTK en `webkitgtk.org/reference/webkit2gtk/stable/` documenta la versión 2.42.5**,
   no 2.52.x (no existe `webkitgtk.org/reference/webkit2gtk/2.52.3/`). Las afirmaciones tomadas de ahí (ausencia de
   API pública de DnD en `WebKitWebView`; texto de `allow-file-access-from-file-urls`) se corroboraron contra el
   código del tag 2.52.3, pero conviene saber que la doc publicada va por detrás.

---

## Fuentes principales

Código (tag `webkitgtk-2.52.3`, la versión exacta de esta máquina):

- [`Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DropTargetGtk3.cpp)
- [`Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/DragSourceGtk3.cpp)
- [`Source/WebKit/UIProcess/API/gtk/WebKitWebViewBase.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/UIProcess/API/gtk/WebKitWebViewBase.cpp)
- [`Source/WebCore/page/SecurityOrigin.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/SecurityOrigin.cpp) ·
  [`SecurityOriginData.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/SecurityOriginData.cpp) ·
  [`DragController.cpp`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/page/DragController.cpp)
- [`Source/WebCore/dom/Element+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/Element+PointerEvents.idl) ·
  [`PointerEvent.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/PointerEvent.idl) ·
  [`GlobalEventHandlers+PointerEvents.idl`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/dom/GlobalEventHandlers+PointerEvents.idl)
- [`Source/WebCore/css/CSSProperties.json`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebCore/css/CSSProperties.json) ·
  [`Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WTF/Scripts/Preferences/UnifiedWebPreferences.yaml)
- [`Source/WebKit/gtk/NEWS`](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.3/Source/WebKit/gtk/NEWS) (release notes oficiales)

Bugs: [265857](https://bugs.webkit.org/show_bug.cgi?id=265857) ·
[234850](https://bugs.webkit.org/show_bug.cgi?id=234850) ·
[157179](https://bugs.webkit.org/show_bug.cgi?id=157179) ·
[292058](https://bugs.webkit.org/show_bug.cgi?id=292058) ·
[200297](https://bugs.webkit.org/show_bug.cgi?id=200297) ·
[320301](https://bugs.webkit.org/show_bug.cgi?id=320301) ·
[319065](https://bugs.webkit.org/show_bug.cgi?id=319065)

Especificación: [HTML Living Standard §6.11 Drag and drop](https://html.spec.whatwg.org/multipage/dnd.html)
(§6.11.2 drag data store, §6.11.3 `DataTransfer`, §6.11.8 security risks)

Referencia de API: [`WebKitWebView`](https://webkitgtk.org/reference/webkit2gtk/stable/class.WebView.html) ·
[`Settings:allow-file-access-from-file-urls`](https://webkitgtk.org/reference/webkit2gtk/stable/property.Settings.allow-file-access-from-file-urls.html)
