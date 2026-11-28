# -*- coding: utf-8 -*-
"""Guion del vídeo "20 DETALLES DE GTA 6 QUE SEGURAMENTE NO CONOCÍAS".

Cada frase lleva una etiqueta:
  "C" = dato confirmado por Rockstar (tráilers, web oficial o comunicados)
  "T" = teoría / especulación de la comunidad
  ""  = narración / observación
Las escenas son recreaciones visuales originales (no gameplay oficial).
"""

TITULO = "20 DETALLES DE GTA 6 QUE SEGURAMENTE NO CONOCÍAS"

SECCIONES = [
    {
        "id": "intro", "titulo": None,
        "escenas": ["aerial", "highway", "beach", "police", "skyline", "swamp", "club", "car", "duo", "rainstreet"],
        "frases": [
            ("", "Rockstar ha escondido muchísimos detalles en GTA 6, y algunos son tan increíbles que probablemente te hayan pasado desapercibidos."),
            ("", "Detrás de cada tráiler, de cada captura y de cada rincón de Leonida, hay pistas que casi nadie ha visto."),
            ("", "Hoy descubrirás veinte detalles que podrían cambiar tu forma de ver este juego."),
            ("", "Y te aviso desde ya: separaremos lo que Rockstar ha confirmado de lo que son solo teorías de la comunidad."),
            ("", "Las imágenes que verás son recreaciones visuales originales, no gameplay oficial."),
        ],
    },
    {
        "id": "d1", "titulo": "EL REALISMO DE SUS GRÁFICOS",
        "escenas": ["skyline", "rainstreet", "aerial", "ocean", "car"],
        "frases": [
            ("", "Empezamos por lo que todo el mundo vio, pero muy pocos analizaron a fondo: los gráficos."),
            ("C", "Rockstar confirmó que el segundo tráiler, publicado en mayo de 2025, se capturó íntegramente en una PlayStation 5."),
            ("C", "Es decir, no hablamos de un ordenador de gama alta, sino de una consola que millones de personas ya tienen en casa."),
            ("", "Los reflejos en el asfalto mojado, la luz del atardecer entre las palmeras y la piel de los personajes muestran un salto técnico enorme."),
            ("T", "Muchos analistas creen que el juego usa iluminación por trazado de rayos, aunque Rockstar no ha detallado su tecnología."),
        ],
    },
    {
        "id": "d2", "titulo": "LAS ANIMACIONES DE LOS PERSONAJES",
        "escenas": ["duo", "club", "shops", "beach"],
        "frases": [
            ("", "Pero el realismo no está solo en la luz. Fíjate en cómo se mueven los personajes."),
            ("", "En los tráilers, los cuerpos transmiten peso, la ropa se arruga y el pelo reacciona al viento y al movimiento."),
            ("", "Incluso se aprecian gestos faciales sutiles: miradas, tensión en la mandíbula, pequeñas sonrisas."),
            ("C", "Rockstar trabaja con captura de movimiento de actores reales, como ya hizo en Red Dead Redemption 2."),
            ("T", "La comunidad especula con transiciones todavía más fluidas entre animaciones, pero eso habrá que comprobarlo mando en mano."),
        ],
    },
    {
        "id": "d3", "titulo": "LA INTELIGENCIA ARTIFICIAL DE LOS NPC",
        "escenas": ["shops", "beach", "rainstreet", "aerial"],
        "frases": [
            ("", "Y si los protagonistas impresionan, espera a ver a la gente que llena las calles."),
            ("C", "En el primer tráiler aparecen multitudes enormes en la playa y en las fiestas, y cada persona parece estar haciendo algo distinto."),
            ("C", "En septiembre de 2022 se filtraron vídeos de una versión temprana del juego, y Rockstar confirmó que el material era auténtico, aunque muy preliminar."),
            ("T", "A partir de esa filtración, muchos fans creen que los NPC tendrán rutinas más complejas. Pero ojo: es material antiguo y pudo cambiar."),
        ],
    },
    {
        "id": "d4", "titulo": "LOS ANIMALES Y LA NATURALEZA",
        "escenas": ["swamp", "mountains", "ocean", "swamp"],
        "frases": [
            ("", "Ahora salimos de la ciudad, porque Leonida también está viva fuera del asfalto."),
            ("C", "Uno de los momentos más comentados del primer tráiler muestra un caimán entrando en una tienda, una referencia a un vídeo viral real grabado en Florida."),
            ("C", "En los pantanos de Grassrivers, Rockstar presenta humedales salvajes donde los caimanes forman parte del paisaje."),
            ("T", "Después de la fauna de Red Dead Redemption 2, muchos esperan un ecosistema muy detallado, aunque no sabemos hasta dónde llegará."),
        ],
    },
    {
        "id": "d5", "titulo": "LOS VEHÍCULOS",
        "escenas": ["highway", "car", "swamp", "ocean", "bridge"],
        "frases": [
            ("", "Y hablando de moverse por Leonida, los vehículos esconden más de lo que parece."),
            ("C", "En los tráilers aparecen descapotables, deportivos, camionetas cubiertas de barro y embarcaciones surcando el agua."),
            ("", "Las camionetas embarradas en reuniones al aire libre reflejan una cultura muy concreta del sur de Estados Unidos."),
            ("T", "Lo que no está confirmado es el nivel de daños o de personalización. Eso son, de momento, expectativas de la comunidad."),
        ],
    },
    {
        "id": "d6", "titulo": "EL FUNCIONAMIENTO DE LA POLICÍA",
        "escenas": ["police", "highway", "aerial", "police"],
        "frases": [
            ("", "Claro, en un GTA tarde o temprano aparece la policía."),
            ("C", "El primer tráiler termina con Jason y Lucia atracando una tienda y huyendo en una persecución que se retransmite por las noticias."),
            ("C", "También vemos a Lucia con uniforme de presa en un centro penitenciario de Leonida."),
            ("T", "Se rumorea un sistema de búsqueda más realista, con testigos y agentes que investigan, pero Rockstar no lo ha explicado oficialmente."),
        ],
    },
    {
        "id": "d7", "titulo": "EL MAPA DE LEONIDA",
        "escenas": ["map", "aerial", "bridge", "map", "swamp"],
        "frases": [
            ("", "Ahora veamos el escenario: el estado de Leonida."),
            ("C", "Es una versión ficticia inspirada en Florida, y Rockstar ha presentado varias regiones: Vice City, los Cayos de Leonida, Grassrivers, Port Gellhorn, Ambrosia y el Monte Kalaga."),
            ("", "Cada zona tiene personalidad propia: playas, pantanos, zonas industriales y naturaleza salvaje."),
            ("T", "El tamaño exacto del mapa no es oficial. Las cifras que circulan son estimaciones de los fans."),
        ],
    },
    {
        "id": "d8", "titulo": "LOS DETALLES DE JASON Y LUCIA",
        "escenas": ["duo", "bridge", "duo", "highway"],
        "frases": [
            ("", "Y en el centro de todo, una pareja."),
            ("C", "Los protagonistas son Jason Duval y Lucia Caminos. Lucia es la primera protagonista femenina de la saga en su era moderna."),
            ("C", "Según la web oficial, Jason creció rodeado de estafadores, pasó por el ejército y acabó en los Cayos. Lucia, por su parte, terminó en prisión por luchar por su familia."),
            ("", "Su historia recuerda a las clásicas parejas criminales, y ese vínculo parece el corazón del juego."),
        ],
    },
    {
        "id": "d9", "titulo": "LAS INTERACCIONES CON EL ENTORNO",
        "escenas": ["rainstreet", "beach", "shops", "club"],
        "frases": [
            ("", "El mundo no es solo un decorado. Los tráilers sugieren que el entorno reacciona."),
            ("", "La ciudad se refleja en charcos y cristales, y casi cualquier escena parece tener testigos grabando con el móvil."),
            ("C", "Rockstar incluso parodia las redes sociales: buena parte del primer tráiler está montada como vídeos virales grabados por los habitantes de Leonida."),
            ("T", "¿Podremos interactuar con muchos más objetos que en GTA 5? Es lo que espera la comunidad, pero no hay una lista oficial."),
        ],
    },
    {
        "id": "d10", "titulo": "TIENDAS Y RESTAURANTES",
        "escenas": ["shops", "rainstreet", "club", "shops"],
        "frases": [
            ("", "Y ese realismo se nota especialmente en los negocios."),
            ("", "Tiendas de conveniencia, gasolineras, clubes nocturnos y locales de comida aparecen con estanterías llenas y carteles luminosos."),
            ("C", "Rockstar mantiene su tradición de parodiar marcas y la cultura de consumo estadounidense."),
            ("T", "Si podremos entrar en muchos de estos locales o solo en algunos es, por ahora, una incógnita."),
        ],
    },
    {
        "id": "d11", "titulo": "EL COMPORTAMIENTO DE LOS PEATONES",
        "escenas": ["shops", "beach", "rainstreet", "club"],
        "frases": [
            ("", "Los peatones merecen un capítulo aparte."),
            ("", "Leonida bebe claramente del fenómeno de los titulares de Florida Man, esas noticias absurdas que se hicieron virales en internet."),
            ("C", "En el primer tráiler aparecen escenas que imitan vídeos reales de Florida, desde fiestas descontroladas hasta situaciones de lo más surrealistas."),
            ("T", "Muchos creen que esta mezcla de humor y caos estará en cada esquina del mapa."),
        ],
    },
    {
        "id": "d12", "titulo": "LOS EFECTOS DEL CLIMA",
        "escenas": ["storm", "rainstreet", "skyline", "storm"],
        "frases": [
            ("", "Ahora miremos al cielo."),
            ("", "Los tráilers muestran atardeceres anaranjados, cielos despejados y noches de lluvia con calles brillantes."),
            ("T", "Una de las teorías más repetidas es que habrá huracanes o tormentas tropicales, algo muy ligado a Florida. Pero hasta ahora es solo especulación."),
            ("", "Lo que sí está claro es que la luz y el clima son clave para la atmósfera del juego."),
        ],
    },
    {
        "id": "d13", "titulo": "LAS PLAYAS",
        "escenas": ["beach", "ocean", "beach", "skyline"],
        "frases": [
            ("", "Y si hay un lugar que representa Vice City, son sus playas."),
            ("C", "En el primer tráiler vemos una playa abarrotada, con cientos de personas tomando el sol, jugando y bailando al mismo tiempo."),
            ("", "Agua turquesa, arena clara, palmeras y edificios frente al mar recrean un ambiente de vacaciones permanentes."),
            ("T", "Hay quien cree que la cantidad de gente cambiará según la hora y el día, como en una ciudad real."),
        ],
    },
    {
        "id": "d14", "titulo": "LOS INTERIORES DE LOS EDIFICIOS",
        "escenas": ["club", "shops", "club", "rainstreet"],
        "frases": [
            ("", "Cuando entramos en los edificios, el detalle no baja."),
            ("C", "Los tráilers enseñan interiores de tiendas, discotecas, viviendas e incluso una prisión."),
            ("T", "Lo que no sabemos es cuántos edificios serán accesibles. Algunos fans esperan muchos más interiores que en entregas anteriores, pero Rockstar no ha dado cifras."),
        ],
    },
    {
        "id": "d15", "titulo": "LAS POSIBILIDADES DE EXPLORACIÓN",
        "escenas": ["mountains", "swamp", "bridge", "ocean"],
        "frases": [
            ("", "Y fuera de la ciudad, Leonida invita a perderse."),
            ("C", "Rockstar describe zonas como el Monte Kalaga o los pantanos de Grassrivers, muy diferentes al ambiente urbano de Vice City."),
            ("", "Agua, carreteras interminables entre islas y naturaleza salvaje: todo apunta a que explorar será parte de la experiencia."),
            ("T", "Se especula con zonas submarinas o actividades como la pesca, pero son ideas de la comunidad, no anuncios oficiales."),
        ],
    },
    {
        "id": "d16", "titulo": "LOS DETALLES DE LOS VEHÍCULOS",
        "escenas": ["car", "rainstreet", "highway", "car"],
        "frases": [
            ("", "Volvamos a los coches, porque hay pequeños detalles que se escapan a primera vista."),
            ("", "En los tráilers, la pintura refleja el neón, las carrocerías se ensucian y los faros atraviesan la lluvia de forma muy realista."),
            ("C", "Además, la saga mantiene su estética: coches inventados que recuerdan claramente a modelos reales."),
            ("T", "Los fans analizan cada fotograma buscando pistas sobre nuevas mecánicas de conducción, pero de momento son suposiciones."),
        ],
    },
    {
        "id": "d17", "titulo": "LOS ELEMENTOS DE VICE CITY",
        "escenas": ["skyline", "aerial", "beach", "club", "highway"],
        "frases": [
            ("", "Ahora sí, hablemos de la joya de la corona: Vice City."),
            ("C", "La ciudad vuelve como escenario principal por primera vez desde GTA Vice City, de 2002, y Vice City Stories, de 2006."),
            ("", "El neón, el art déco, las avenidas frente al mar y la vida nocturna siguen ahí, pero en una versión moderna, llena de redes sociales y cultura actual."),
            ("", "Es la mezcla perfecta entre nostalgia y presente."),
        ],
    },
    {
        "id": "d18", "titulo": "LO QUE SE DESCUBRIÓ EN LOS TRÁILERS",
        "escenas": ["highway", "beach", "police", "duo", "skyline"],
        "frases": [
            ("", "Los tráilers también tienen su propia historia."),
            ("C", "El primero se publicó el 4 de diciembre de 2023, antes de lo previsto, porque se había filtrado en internet."),
            ("C", "En sus primeras 24 horas superó los 90 millones de visualizaciones en YouTube, una cifra récord."),
            ("C", "Y la música también cuenta: el primer tráiler usa Love Is a Long Road, de Tom Petty, y el segundo, Hot Together, de The Pointer Sisters."),
        ],
    },
    {
        "id": "d19", "titulo": "REFERENCIAS Y POSIBLES SECRETOS",
        "escenas": ["map", "rainstreet", "club", "aerial"],
        "frases": [
            ("", "Y aquí entramos en terreno de detectives."),
            ("C", "Junto al segundo tráiler, Rockstar estrenó una web oficial con biografías de personajes y decenas de capturas nuevas."),
            ("T", "Los fans han analizado esas imágenes píxel a píxel buscando referencias a juegos anteriores, posibles misiones o lugares ocultos."),
            ("T", "Algunas teorías son brillantes y otras bastante locas. Mientras Rockstar no lo confirme, es solo especulación."),
        ],
    },
    {
        "id": "d20", "titulo": "LO MÁS SORPRENDENTE DEL MUNDO ABIERTO",
        "escenas": ["aerial", "bridge", "skyline", "mountains", "beach"],
        "frases": [
            ("", "Y llegamos al último detalle, quizá el más sorprendente de todos: el propio viaje hasta aquí."),
            ("C", "GTA 6 se anunció para 2025, se retrasó al 26 de mayo de 2026 y después al 19 de noviembre de 2026, la fecha elegida para su lanzamiento en PlayStation 5 y Xbox Series."),
            ("", "Más de una década después de GTA 5, Rockstar ha levantado un mundo donde la ciudad, la naturaleza, la gente y la cultura de internet conviven en un solo lugar."),
            ("T", "La versión para PC no tiene fecha oficial, aunque varios informes apuntan a 2027."),
        ],
    },
    {
        "id": "outro", "titulo": None,
        "escenas": ["skyline", "duo", "highway", "aerial"],
        "frases": [
            ("", "Veinte detalles, un solo estado y una pareja dispuesta a todo."),
            ("", "Y lo más interesante es que, probablemente, todavía queden muchos secretos por descubrir."),
            ("", "¿Cuál de estos 20 detalles te ha sorprendido más? ¿Conocías alguno?"),
            ("", "Déjamelo en los comentarios y suscríbete, porque pronto descubriremos más secretos de GTA 6."),
        ],
    },
]

# Sustituciones solo para la voz (los subtítulos muestran el texto original)
PRONUNCIACION = [
    ("GTA 6", "GTA seis"), ("GTA 5", "GTA cinco"),
    ("PlayStation 5", "PlayStation cinco"), ("Xbox Series", "Xbox Séries"),
    ("4 de diciembre de 2023", "cuatro de diciembre de dos mil veintitrés"),
    ("26 de mayo de 2026", "veintiséis de mayo de dos mil veintiséis"),
    ("19 de noviembre de 2026", "diecinueve de noviembre de dos mil veintiséis"),
    ("septiembre de 2022", "septiembre de dos mil veintidós"),
    ("mayo de 2025", "mayo de dos mil veinticinco"),
    ("para 2025", "para dos mil veinticinco"),
    ("a 2027", "a dos mil veintisiete"),
    ("de 2002", "de dos mil dos"), ("de 2006", "de dos mil seis"),
    ("24 horas", "veinticuatro horas"), ("90 millones", "noventa millones"),
    ("20 detalles", "veinte detalles"),
    ("NPC", "ene pe cés"),
    ("YouTube", "Yutub"),
    ("Love Is a Long Road", "Lov is a long roud"),
    ("Hot Together", "Jot tuguéder"),
    ("The Pointer Sisters", "de Póinter Sísters"),
    ("Tom Petty", "Tom Péti"),
    ("Red Dead Redemption 2", "Red Ded Redémpshon dos"),
    ("Florida Man", "Flórida Man"),
    ("Grassrivers", "Grasrívers"),
    ("Port Gellhorn", "Port Guélhorn"),
    ("Jason", "Yéison"),
    ("Vice City", "Vais Siti"),
    ("Stories", "Stóris"),
    ("art déco", "ar decó"),
]
