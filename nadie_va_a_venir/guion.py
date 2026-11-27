# -*- coding: utf-8 -*-
"""
Guion: NADIE VA A VENIR A SALVARTE
Estilo: motivacional cinematográfico (segunda persona, frases cortas, pausas largas).

Formato de cada entrada:
  ("CH", "CAPÍTULO I", "TÍTULO")            -> tarjeta de capítulo
  (narración, texto_en_pantalla, fondo)    -> línea narrada
    - en texto_en_pantalla, *palabra* = resaltada en dorado, "|" = salto de línea
    - texto_en_pantalla vacío "" = solo fondo
    - fondo: dust | rays | stars | rain | horizon | ember | void
  ("PAUSE", segundos)                      -> silencio extra
"""

TITLE = "NADIE VA A VENIR A SALVARTE"

GUION = [
    # ---------------- COLD OPEN ----------------
    ("Escúchame bien.", "ESCÚCHAME *BIEN*", "void"),
    ("Nadie va a venir a salvarte.", "NADIE VA A VENIR|A *SALVARTE*", "rain"),
    ("Ni tus padres. Ni tus amigos. Ni esa persona que te prometió que siempre estaría ahí.", "NI TUS PADRES.|NI TUS AMIGOS.", "rain"),
    ("Nadie.", "*NADIE*", "void"),
    ("PAUSE", 0.8),
    ("Y sé que duele escucharlo. Pero cuanto antes lo aceptes, antes empezará tu verdadera vida.", "CUANTO ANTES LO ACEPTES|ANTES EMPIEZA TU *VERDADERA VIDA*", "dust"),
    ("Porque el día que entiendes que nadie va a hacerlo por ti, es el día en que por fin empiezas a hacerlo tú.", "EL DÍA QUE LO ENTIENDES|EMPIEZAS A HACERLO *TÚ*", "rays"),
    ("Este vídeo no es para todo el mundo.", "ESTE VÍDEO NO ES|PARA *TODO EL MUNDO*", "void"),
    ("Es para el que está cansado de ser quien es. Para el que sabe, en lo más profundo, que nació para algo más.", "ES PARA EL QUE SABE|QUE NACIÓ PARA *ALGO MÁS*", "ember"),
    ("Si ese eres tú, quédate hasta el final.", "QUÉDATE HASTA|EL *FINAL*", "dust"),
    ("PAUSE", 1.0),
    ("", TITLE.replace("SALVARTE", "*SALVARTE*").replace("VENIR ", "VENIR|"), "title"),
    ("PAUSE", 1.5),

    # ---------------- CAPÍTULO I ----------------
    ("CH", "CAPÍTULO I", "LA MENTIRA"),
    ("Desde pequeño te contaron una historia.", "TE CONTARON|UNA *HISTORIA*", "dust"),
    ("Que si eras bueno, si obedecías, si esperabas tu turno, la vida te recompensaría.", "SI ESPERABAS TU TURNO|LA VIDA TE *RECOMPENSARÍA*", "dust"),
    ("Que el momento perfecto llegaría solo.", "EL MOMENTO *PERFECTO*|LLEGARÍA SOLO", "stars"),
    ("Que la motivación aparecería un día, como un rayo, y lo cambiaría todo.", "LA MOTIVACIÓN|APARECERÍA *SOLA*", "stars"),
    ("Mentira.", "*MENTIRA*", "void"),
    ("PAUSE", 0.6),
    ("El momento perfecto no existe. La motivación no viene a buscarte. Y la vida no le debe nada a nadie.", "LA VIDA NO TE|*DEBE NADA*", "rain"),
    ("Mira a tu alrededor. Hay millones de personas esperando.", "MILLONES DE PERSONAS|*ESPERANDO*", "dust"),
    ("Esperando el lunes. Esperando el año nuevo. Esperando sentirse preparados.", "ESPERANDO EL *LUNES*", "dust"),
    ("Y mientras esperan, los años pasan. En silencio. Sin pedir permiso.", "LOS AÑOS PASAN|*EN SILENCIO*", "horizon"),
    ("Un día te despiertas, te miras al espejo, y no reconoces a la persona que te devuelve la mirada.", "NO RECONOCES|A LA PERSONA DEL *ESPEJO*", "void"),
    ("No porque hayas fracasado. Sino porque nunca lo intentaste de verdad.", "NUNCA LO INTENTASTE|*DE VERDAD*", "rain"),
    ("Y esa, créeme, es la peor sensación del mundo.", "LA PEOR SENSACIÓN|DEL *MUNDO*", "void"),
    ("PAUSE", 1.0),

    # ---------------- CAPÍTULO II ----------------
    ("CH", "CAPÍTULO II", "EL PRECIO DE QUEDARTE IGUAL"),
    ("Todo el mundo habla del precio de cambiar.", "EL PRECIO|DE *CAMBIAR*", "ember"),
    ("Del esfuerzo. Del sacrificio. De las noches sin dormir.", "ESFUERZO. SACRIFICIO.|*NOCHES SIN DORMIR*", "ember"),
    ("Pero casi nadie habla del precio de quedarte exactamente donde estás.", "¿Y EL PRECIO DE|*QUEDARTE IGUAL*?", "void"),
    ("Ese precio no se paga de golpe. Se paga poco a poco. Cada día.", "SE PAGA|*CADA DÍA*", "rain"),
    ("Lo pagas cada vez que pospones lo que sabes que tienes que hacer.", "CADA VEZ QUE|*POSPONES*", "rain"),
    ("Lo pagas cada vez que eliges la comodidad en lugar del crecimiento.", "COMODIDAD|O *CRECIMIENTO*", "dust"),
    ("Lo pagas con tu autoestima. Con tu energía. Con tus sueños, que se van apagando uno a uno, como velas al final de la noche.", "TUS SUEÑOS SE APAGAN|*UNO A UNO*", "ember"),
    ("El dolor de la disciplina pesa gramos.", "LA DISCIPLINA|PESA *GRAMOS*", "rays"),
    ("El dolor del arrepentimiento pesa toneladas.", "EL ARREPENTIMIENTO|PESA *TONELADAS*", "void"),
    ("PAUSE", 0.6),
    ("Vas a sufrir de todas formas. Eso no lo puedes elegir.", "VAS A SUFRIR|*DE TODAS FORMAS*", "rain"),
    ("Lo único que puedes elegir es por qué sufres.", "ELIGE|*POR QUÉ* SUFRES", "dust"),
    ("Puedes sufrir construyendo la vida que quieres. O puedes sufrir viendo cómo se escapa la vida que pudiste tener.", "CONSTRUYENDO|O *LAMENTANDO*", "horizon"),
    ("Tú decides.", "TÚ *DECIDES*", "void"),
    ("PAUSE", 1.0),

    # ---------------- CAPÍTULO III ----------------
    ("CH", "CAPÍTULO III", "LA DISCIPLINA ES LIBERTAD"),
    ("La motivación es un invitado. Llega cuando quiere y se va sin despedirse.", "LA MOTIVACIÓN|ES UN *INVITADO*", "dust"),
    ("La disciplina es un hogar. Siempre está ahí cuando vuelves.", "LA DISCIPLINA|ES UN *HOGAR*", "rays"),
    ("Los que ganan no se sienten motivados todos los días. Nadie lo hace.", "NADIE SE SIENTE MOTIVADO|*TODOS LOS DÍAS*", "dust"),
    ("La diferencia es que ellos aparecen igual.", "ELLOS *APARECEN*|IGUAL", "rays"),
    ("Con ganas o sin ganas. Con frío o con calor. Tristes, cansados, rotos por dentro.", "CON GANAS|O *SIN GANAS*", "rain"),
    ("Aparecen.", "*APARECEN*", "void"),
    ("PAUSE", 0.6),
    ("Hace casi dos mil años, un emperador romano llamado Marco Aurelio se escribía a sí mismo cada mañana.", "MARCO *AURELIO*", "stars"),
    ("Se recordaba que había nacido para trabajar, no para quedarse bajo las mantas buscando calor.", "NACISTE PARA *ACTUAR*|NO PARA ESCONDERTE", "stars"),
    ("El hombre más poderoso del mundo tenía que convencerse cada día de levantarse de la cama.", "EL HOMBRE MÁS PODEROSO|TAMBIÉN *DUDABA*", "dust"),
    ("¿Y tú crees que a ti te iba a resultar fácil?", "¿Y TÚ CREÍAS|QUE SERÍA *FÁCIL*?", "void"),
    ("No es fácil. Nunca lo fue. Nunca lo será.", "NUNCA FUE *FÁCIL*", "rain"),
    ("Pero cada vez que haces lo difícil, algo dentro de ti se hace más fuerte.", "CADA VEZ QUE HACES LO DIFÍCIL|TE HACES MÁS *FUERTE*", "ember"),
    ("Cada promesa que cumples contigo mismo es un ladrillo. Y con suficientes ladrillos, construyes a una persona nueva.", "CADA PROMESA CUMPLIDA|ES UN *LADRILLO*", "rays"),
    ("La disciplina no te quita libertad. Te la da.", "LA DISCIPLINA|ES *LIBERTAD*", "rays"),
    ("PAUSE", 1.0),

    # ---------------- CAPÍTULO IV ----------------
    ("CH", "CAPÍTULO IV", "MATA A TU ANTIGUO YO"),
    ("Para renacer, primero algo tiene que morir.", "PARA RENACER|ALGO TIENE QUE *MORIR*", "ember"),
    ("Tu antiguo yo. El que se rinde a la primera. El que busca excusas. El que culpa a los demás.", "EL QUE BUSCA|*EXCUSAS*", "rain"),
    ("Ese que lleva años diciéndote que no puedes. Que no eres suficiente. Que es demasiado tarde.", "ES *DEMASIADO TARDE*", "void"),
    ("Él no va a irse por las buenas. Va a luchar.", "VA A *LUCHAR*", "ember"),
    ("Te va a susurrar que mañana empiezas. Que hoy te mereces un descanso. Que total, para qué.", "MAÑANA *EMPIEZO*", "dust"),
    ("Y vas a tener que mirarle a los ojos y decirle: no.", "MÍRALE A LOS OJOS|Y DILE: *NO*", "void"),
    ("PAUSE", 0.6),
    ("Renacer no es un momento mágico. No es un vídeo. No es una frase.", "RENACER NO ES|UN *MOMENTO*", "dust"),
    ("Renacer es una decisión que tomas hoy. Y que vuelves a tomar mañana. Y pasado. Y todos los días que te quedan.", "ES UNA *DECISIÓN*|TODOS LOS DÍAS", "rays"),
    ("El fénix no renace por suerte. Renace porque arde.", "EL FÉNIX RENACE|PORQUE *ARDE*", "ember"),
    ("Así que deja que todo lo que eras se convierta en ceniza.", "DEJA QUE ARDA|LO QUE *ERAS*", "ember"),
    ("Porque de esa ceniza vas a levantarte tú.", "DE LA CENIZA|TE *LEVANTAS*", "horizon"),
    ("PAUSE", 1.0),

    # ---------------- CAPÍTULO V ----------------
    ("CH", "CAPÍTULO V", "LAS REGLAS DEL RENACIMIENTO"),
    ("Así que escucha. Estas son las reglas.", "LAS *REGLAS*", "void"),
    ("Regla número uno. Gana la mañana.", "1. GANA LA *MAÑANA*", "horizon"),
    ("La forma en que empiezas el día decide cómo lo terminas. No toques el móvil nada más despertar. Levántate. Muévete. Haz algo difícil antes de que el mundo se despierte.", "HAZ ALGO DIFÍCIL|ANTES QUE *NADIE*", "horizon"),
    ("Regla número dos. Cuida lo que entra en tu mente.", "2. CUIDA TU *MENTE*", "stars"),
    ("Eres lo que consumes. Si alimentas tu mente con basura, vivirás una vida de basura. Elige lo que lees, lo que escuchas y a quién escuchas.", "ERES LO QUE|*CONSUMES*", "stars"),
    ("Regla número tres. Aléjate de quien te frena.", "3. ALÉJATE DE QUIEN|TE *FRENA*", "rain"),
    ("No todo el mundo merece un asiento en tu vida. Hay personas que te quieren pequeño porque tu grandeza les recuerda lo que ellos no se atrevieron a hacer.", "NO TODOS MERECEN|UN *ASIENTO*", "rain"),
    ("Regla número cuatro. Abraza la incomodidad.", "4. ABRAZA LA|*INCOMODIDAD*", "ember"),
    ("Todo lo que quieres está al otro lado del miedo. Del frío. Del cansancio. Si siempre eliges lo cómodo, siempre tendrás una vida pequeña.", "LO QUE QUIERES ESTÁ|AL OTRO LADO DEL *MIEDO*", "ember"),
    ("Regla número cinco. Cumple tu palabra contigo mismo.", "5. CUMPLE TU *PALABRA*", "rays"),
    ("Si dices que vas a hacerlo, hazlo. Aunque nadie te vea. Aunque nadie lo sepa. Porque tú sí lo sabes.", "PORQUE TÚ|*SÍ LO SABES*", "rays"),
    ("PAUSE", 1.0),

    # ---------------- CAPÍTULO VI ----------------
    ("CH", "CAPÍTULO VI", "CUANDO NADIE TE VE"),
    ("El verdadero trabajo ocurre en la oscuridad.", "EL VERDADERO TRABAJO|OCURRE EN LA *OSCURIDAD*", "void"),
    ("A las cinco de la mañana, cuando todos duermen. A medianoche, cuando todos se han rendido.", "CUANDO TODOS|*DUERMEN*", "stars"),
    ("Nadie aplaude. Nadie te da las gracias. Nadie publica una foto de ese momento.", "NADIE *APLAUDE*", "rain"),
    ("Y está bien. Porque no lo haces para ellos.", "NO LO HACES|PARA *ELLOS*", "dust"),
    ("Las raíces de un árbol crecen bajo tierra durante años antes de que nadie vea el tronco.", "LAS *RAÍCES*|CRECEN EN SILENCIO", "dust"),
    ("Así es tu proceso. Durante mucho tiempo parecerá que no pasa nada.", "PARECERÁ QUE|*NO PASA NADA*", "void"),
    ("La gente dirá que estás perdiendo el tiempo. Que te has vuelto raro. Que has cambiado.", "DIRÁN QUE|HAS *CAMBIADO*", "rain"),
    ("Y tendrán razón. Has cambiado.", "Y TENDRÁN *RAZÓN*", "rays"),
    ("Un día, sin avisar, todo lo que sembraste en silencio va a florecer delante de todos.", "TODO LO QUE SEMBRASTE|VA A *FLORECER*", "horizon"),
    ("Y los mismos que se reían te preguntarán cómo lo hiciste.", "TE PREGUNTARÁN|*CÓMO LO HICISTE*", "rays"),
    ("Y tú solo sonreirás. Porque sabrás que no hubo ningún secreto. Solo días. Muchos días. Uno detrás de otro.", "NO HUBO SECRETO.|SOLO *DÍAS*", "dust"),
    ("PAUSE", 1.2),

    # ---------------- FINAL ----------------
    ("CH", "EPÍLOGO", "EL PRIMER DÍA"),
    ("Así que vuelvo a decírtelo. Nadie va a venir a salvarte.", "NADIE VA A|*SALVARTE*", "void"),
    ("Pero ahora escúchalo de otra manera.", "ESCÚCHALO DE|*OTRA MANERA*", "dust"),
    ("Nadie va a venir a salvarte, porque no lo necesitas.", "PORQUE NO LO|*NECESITAS*", "rays"),
    ("Porque la persona que estabas esperando, la que iba a cambiarlo todo, siempre fuiste tú.", "SIEMPRE FUISTE|*TÚ*", "horizon"),
    ("PAUSE", 0.8),
    ("No mañana. No el lunes. No cuando te sientas preparado.", "NO *MAÑANA*", "rain"),
    ("Hoy.", "*HOY*", "void"),
    ("Apaga esta pantalla. Levántate. Y haz una sola cosa que tu antiguo yo jamás habría hecho.", "LEVÁNTATE.|Y *EMPIEZA*", "ember"),
    ("Ese es tu primer día. El primer día del resto de tu vida.", "EL PRIMER DÍA|DEL RESTO DE TU *VIDA*", "horizon"),
    ("PAUSE", 0.8),
    ("Si este mensaje te ha llegado, suscríbete y compártelo con alguien que necesite escucharlo hoy.", "*SUSCRÍBETE*|Y COMPÁRTELO", "dust"),
    ("Nos vemos en la cima.", "NOS VEMOS EN|LA *CIMA*", "rays"),
    ("PAUSE", 3.0),
]
