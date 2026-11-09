AGENDA DE CONTACTOS CON ACCESO ALEATORIO

Aplicación de escritorio desarrollada en Python que permite administrar una agenda de contactos mediante archivos de registros de tamaño fijo y acceso aleatorio.

El sistema utiliza una interfaz gráfica desarrollada con PySide6, un índice primario en JSON para realizar búsquedas por ID y mecanismos de verificación de integridad mediante SHA-256.

También permite exportar la información a JSON y PDF, generar respaldos comprimidos en formato ZIP y consultar los metadatos del archivo de contactos.


Funcionalidades:

Contactos
- Agregar nuevos contactos.
- Buscar contactos mediante su ID.
- Modificar la información de contactos existentes.
- Mostrar todos los contactos registrados.
- Validar que no existan ID duplicados.
- Detectar cuando no se realizan modificaciones.

Exportar
- Exportar los contactos a un archivo JSON.
- Generar un reporte PDF a partir del JSON exportado.
- Incluir la fecha de generación y el listado de contactos.

Herramientas
- Verificar la integridad de contactos.dat mediante SHA-256.
- Detectar modificaciones realizadas fuera de la aplicación.
- Actualizar automáticamente el hash después de guardar cambios.
- Crear respaldos comprimidos en formato ZIP.
- Mostrar el tamaño original y comprimido de los respaldos.
- Consultar el tamaño, fecha de modificación y permisos del archivo.

Ayuda
- Mostrar información general sobre la aplicación.

Tecnologías utilizadas:

- Python: lenguaje de programación principal.
- PySide6: desarrollo de la interfaz gráfica.
- ReportLab: generación de reportes PDF.
- JSON: almacenamiento del índice y exportación de contactos.
- hashlib: verificación de integridad SHA-256.
- zipfile: creación de respaldos comprimidos.
- pathlib y os: administración de rutas, archivos y permisos.

Estructura del proyecto:

Proyecto2Manejo/
|
|-- datos/
|   |-- contactos.dat
|   |-- contactos.sha256
|   |-- indice.json
|
|-- reportes/
|   |-- contactos.json
|   |-- reporte_contactos.pdf
|
|-- respaldos/
|   |-- respaldo_contactos_YYYYMMDD_HHMMSS. y otros ZIP generados
|
|-- contactos.py
|-- indice.py
|-- exportacion.py
|-- herramientas.py
|-- interfaz.py
|-- main.py
|-- requirements.txt
|-- README.md
|-- .gitattributes



Cada contacto contiene los siguientes campos:

| Campo | Tamaño |
| ID | 8 bytes |
| Nombre | 40 bytes |
| Teléfono | 18 bytes |
| Correo | 50 bytes |
| Ciudad | 35 bytes |
| Salto de línea | 1 byte |
| Total | 152 bytes |

Los campos se almacenan utilizando UTF-8 y se completan con espacios mediante "ljust()" para garantizar que cada registro ocupe exactamente 152 bytes.

Acceso aleatorio:

La aplicación utiliza "seek()" para posicionarse directamente en un registro y "tell()" para consultar la posición actual del puntero dentro del archivo.

La posición se calcula mediante:

python
posicion = numero_registro * TAM_REGISTRO


Esto permite buscar y modificar contactos sin recorrer secuencialmente todo el archivo de datos.

Índice primario JSON

El archivo "indice.json" relaciona cada ID con su número de registro.

Ejemplo:
{
    "101": 0,
    "102": 1,
    "103": 2,
    "104": 3,
    "105": 4
}


Cuando se realiza una búsqueda, primero se consulta el índice y después se utiliza "seek()" para leer directamente el registro correspondiente.

## Verificación de integridad

La aplicación calcula el hash SHA-256 del archivo "contactos.dat" y lo almacena en "contactos.sha256".

Al iniciar el programa se verifica que el contenido del archivo coincida con el hash guardado.

Si se detecta una modificación externa, la aplicación muestra una advertencia.

Después de agregar o modificar un contacto correctamente, el hash se actualiza automáticamente.

Respaldos:

La aplicación utiliza "zipfile" para crear respaldos que contienen:

"contactos.dat"
"indice.json"

Los respaldos se generan con nombres que incluyen la fecha y hora para evitar sobrescribir archivos anteriores.

También se muestra el tamaño original de los archivos y el tamaño final del ZIP.


Dependencias:

El archivo "requirements.txt" contiene:

PySide6
reportlab


Las demás bibliotecas utilizadas forman parte de la biblioteca estándar de Python.

Manejo de errores:

La aplicación incluye validaciones para:

- ID inexistentes.
- ID duplicados.
- ID no numéricos.
- Archivos faltantes.
- Índice JSON corrupto.
- Registros con tamaño inválido.
- Archivos modificados externamente.
- Falta de permisos de lectura o escritura.

Los errores se muestran mediante ventanas informativas para evitar que la aplicación se cierre inesperadamente.

Ejecución del proyecto:

Para iniciar la agenda, se debe ejecutar "main.py".

Desde la interfaz gráfica se pueden utilizar las secciones Contactos, Exportar, Herramientas y Ayuda.

Los archivos generados se almacenan en las carpetas "datos", "reportes" y "respaldos".
