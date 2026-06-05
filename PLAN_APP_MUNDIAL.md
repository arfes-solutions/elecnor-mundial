# Plan de Evolucion - Porra Mundial 2026

Documento de apoyo para mantener clara la direccion del proyecto, las decisiones tomadas y el orden recomendado de trabajo.

## 1. Contexto

La app actual nace como una porra interna para el Mundial 2026. La idea es buena porque tiene un componente social natural: competir con companeros, mirar el ranking, comentar predicciones y seguir la evolucion del torneo.

El estado actual es un prototipo funcional, pero no una app preparada para entregar a un cliente con una experiencia atractiva, mantenible y segura.

## 2. Estado Actual

Archivos principales:

- `App_Mundial/app.py`: web publica de la porra.
- `App_Mundial/admin.py`: panel de administracion separado.
- `App_Mundial/participantes.json`: predicciones de participantes.
- `App_Mundial/resultados.txt`: resultados reales introducidos por admin.

Funcionalidades existentes:

- Ranking general de participantes.
- Alta de participante.
- Seleccion de predicciones de grupos.
- Seleccion de rondas eliminatorias, campeon, subcampeon y pichichi.
- Vista de prediccion individual.
- Vista de grupos.
- Vista de horarios.
- Panel admin para actualizar resultados reales.
- Calculo de puntos.

## 3. Problemas Detectados

### Producto y experiencia

- La interfaz parece una maqueta basica con Bootstrap, no una experiencia de competicion atractiva.
- El ranking no genera suficiente deseo de volver a entrar.
- El flujo de alta puede ser mas claro, guiado y emocionante.
- Las eliminatorias se eligen con checkboxes, cuando deberian sentirse como un bracket del Mundial.
- Las reglas estan presentes, pero no forman parte natural de la experiencia.
- No hay resumen final antes de guardar la prediccion.
- No hay narrativa visual: podium, favoritos, campeon elegido, progreso, hitos del torneo.

### Tecnica y mantenimiento

- Todo el HTML, CSS y JavaScript esta embebido en strings dentro de Python.
- `app.py` es demasiado grande y mezcla datos, vistas, estilos, rutas y logica.
- `admin.py` duplica datos del torneo.
- No hay `requirements.txt`, asi que el proyecto no arranca de forma reproducible.
- No hay estructura de templates ni static assets.
- No hay tests.
- No hay control de configuracion por entorno.

### Datos y persistencia

- Los participantes se guardan en JSON plano.
- Los resultados reales se guardan en TXT.
- Puede haber problemas si dos personas escriben al mismo tiempo.
- No hay modelo de datos claro.
- Los nombres de equipos se usan como identificadores, lo que complica acentos, duplicados y cambios de texto.
- Hay textos corruptos por codificacion: ejemplos visibles del tipo `M...xico`, `Configuraci...n`, etc.

### Seguridad y operacion

- El panel admin no tiene login.
- Las apps se ejecutan con `debug=True`.
- El servidor escucha en `0.0.0.0`.
- No hay control serio para cerrar inscripciones.
- No hay validacion suficiente de formularios.
- No hay instrucciones claras de despliegue.

## 4. Vision de la Version 2

Convertir el prototipo en una app interna atractiva, sencilla y robusta, donde la gente quiera entrar antes y durante el Mundial para:

- Registrar su prediccion.
- Ver su posicion.
- Compararse con companeros.
- Consultar predicciones de otros.
- Seguir grupos y eliminatorias.
- Ver como cambian los puntos tras cada actualizacion.

La app debe sentirse como una competicion interna de oficina bien cuidada: profesional, energica y facil de usar.

## 5. Principios de Diseno

- Primera pantalla util, no landing page decorativa.
- Ranking y estado de la competicion como centro de la experiencia.
- Visual de torneo: banderas, podium, bracket, tarjetas de participantes.
- Interfaz compacta y escaneable para uso recurrente.
- Flujo de alta guiado, con pasos claros.
- Responsive desde el principio.
- Estetica cuidada, evitando una pagina generica de Bootstrap.
- Textos cortos, naturales y con tono de competicion.

## 6. Propuesta de Funcionalidades

### Web publica

- Dashboard inicial con:
  - Podium top 3.
  - Ranking completo.
  - Numero de participantes.
  - Lider actual.
  - Ultima actualizacion de resultados.
  - Acceso claro a participar.
- Wizard de participacion:
  - Paso 1: datos del participante.
  - Paso 2: prediccion de grupos.
  - Paso 3: bracket de eliminatorias.
  - Paso 4: campeon, subcampeon y pichichi.
  - Paso 5: resumen y confirmacion.
- Perfil de participante:
  - Prediccion completa.
  - Campeon elegido.
  - Pichichi elegido.
  - Puntos por categoria.
  - Aciertos destacados.
- Vista de grupos:
  - Estado real de cada grupo.
  - Clasificados visibles.
  - Banderas y orden claro.
- Vista de calendario:
  - Partidos por fecha/grupo.
  - Horarios en hora peninsular.
- Vista de reglas:
  - Puntuacion explicada de forma breve.
  - Ejemplos de puntuacion.

### Panel admin

- Login admin.
- Dashboard de control:
  - Participantes registrados.
  - Estado de inscripciones.
  - Ultima actualizacion.
- Gestion de resultados:
  - Actualizar grupos.
  - Actualizar rondas.
  - Actualizar campeon, subcampeon y pichichi.
- Cierre/apertura de inscripciones.
- Exportacion de participantes y predicciones.
- Recalculo de puntos.

## 7. Propuesta Tecnica

Mantener Flask como base, pero reestructurar el proyecto.

Estructura recomendada:

```text
App_Mundial/
  app/
    __init__.py
    routes/
      public.py
      admin.py
    services/
      scoring.py
      standings.py
      predictions.py
    data/
      tournament.py
    templates/
      base.html
      public/
      admin/
    static/
      css/
      js/
      img/
  instance/
    mundial.db
  tests/
  requirements.txt
  run.py
```

Persistencia recomendada:

- SQLite para la primera version seria.
- Tablas basicas:
  - `participants`
  - `predictions`
  - `results`
  - `settings`

Identificadores:

- Usar codigos internos para equipos, no nombres.
- Ejemplo: `ESP`, `MEX`, `ARG`.
- Mostrar nombres traducidos solo en UI.

## 8. Fases de Trabajo

### Fase 0 - Preparacion

Objetivo: que el proyecto sea reproducible y entendible.

- Crear `requirements.txt`.
- Crear estructura base limpia.
- Corregir codificacion de textos.
- Centralizar datos del torneo en un unico modulo.
- Separar templates y static assets.

Criterio de cierre:

- La app arranca con instrucciones claras.
- No hay mojibake en textos visibles.
- No hay HTML gigante embebido en Python.

### Fase 1 - Base funcional robusta

Objetivo: conservar lo que funciona, pero con datos y rutas ordenadas.

- Migrar participantes/resultados a SQLite. En progreso: creada la base `participants`, `results` y `settings`.
- Crear servicios de puntuacion. En progreso: servicio `scoring` separado y cubierto por tests.
- Anadir validaciones de formularios.
- Evitar participantes duplicados.
- Preparar cierre de inscripciones.
- Anadir tests del calculo de puntos. En progreso: tests base anadidos.

Criterio de cierre:

- El ranking se calcula correctamente.
- Las predicciones se guardan de forma estable.
- Los resultados se actualizan sin tocar TXT manualmente.

### Fase 2 - Experiencia publica atractiva

Objetivo: transformar la app en una experiencia que apetezca usar.

- Redisenar dashboard inicial.
- Crear podium top 3.
- Mejorar ranking.
- Crear wizard de prediccion.
- Crear bracket visual.
- Crear perfil publico de participante.
- Mejorar reglas y calendario.

Criterio de cierre:

- La app se siente como producto final, no como formulario.
- Mobile y desktop estan cuidados.
- El flujo de participar es claro de principio a fin.

### Fase 3 - Admin serio

Objetivo: que el cliente pueda operar la porra sin tocar codigo.

- Login admin.
- Panel de estado.
- Gestion visual de resultados.
- Cierre/apertura de inscripciones.
- Exportacion de datos.
- Confirmaciones antes de cambios importantes.

Criterio de cierre:

- El admin puede actualizar el torneo sin riesgo evidente.
- La web publica refleja los cambios correctamente.

### Fase 4 - Pulido y entrega

Objetivo: dejar la app presentable y lista para uso real.

- Revisar responsive.
- Revisar textos.
- Revisar accesibilidad basica.
- Anadir README de instalacion/despliegue.
- Preparar datos iniciales.
- Pruebas manuales del flujo completo.

Criterio de cierre:

- Una persona nueva puede instalar, arrancar y usar la app siguiendo el README.
- El cliente puede gestionar la porra sin ayuda tecnica continua.

## 9. Riesgos y Decisiones Pendientes

- Confirmar si la app sera solo local/intranet o accesible por internet.
- Confirmar si hace falta login para participantes o solo nombre publico.
- Confirmar si los participantes pueden editar su prediccion antes del cierre.
- Confirmar si hay premio, departamentos o equipos internos.
- Confirmar nombre/marca final: Elecnor, departamento, oficina, etc.
- Confirmar si se quiere usar imagen corporativa estricta o una identidad propia para la porra.
- Confirmar formato final de despliegue: servidor local, hosting, Docker, intranet.

Decision provisional:

- Desarrollo local con Flask y almacenamiento local/SQLite.
- Produccion orientada a Vercel + Supabase/Postgres.
- Supabase usara `SUPABASE_URL` y una clave secreta server-side `sb_secret_...` guardada solo como variable de entorno.
- La capa de almacenamiento debe mantenerse separada para que el cambio a Supabase sea controlado.

## 10. Roadmap Recomendado

Orden sugerido:

1. Arreglar reproducibilidad y codificacion.
2. Separar estructura tecnica.
3. Migrar datos a SQLite.
4. Rehacer dashboard publico.
5. Rehacer flujo de participacion.
6. Rehacer admin.
7. Pulir visualmente y documentar entrega.

## 11. Checklist de Calidad

Antes de considerar una version entregable:

- La app arranca desde cero con instrucciones claras.
- No hay textos corruptos.
- El admin esta protegido.
- Las inscripciones pueden cerrarse.
- No se puede duplicar participante por accidente.
- El ranking se recalcula correctamente.
- El wizard no permite predicciones incoherentes.
- El bracket es visual y comprensible.
- La app funciona en movil.
- Existe README.
- Hay tests para puntuacion.
- Hay copia/exportacion de datos.

## 12. Norte del Proyecto

La clave no es solo que la gente pueda meter una prediccion. La clave es que la porra tenga vida durante el Mundial.

Cada mejora deberia empujar en una de estas direcciones:

- Hacer mas facil participar.
- Hacer mas emocionante consultar el ranking.
- Hacer mas seguro actualizar resultados.
- Hacer mas clara la competicion.
- Hacer mas presentable la app ante el cliente.
