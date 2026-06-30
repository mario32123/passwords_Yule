# GestorPass Colombia

Aplicativo web en la nube para la gestión centralizada de contraseñas de empresas y personas naturales, pensado para el contexto contable/tributario colombiano (DIAN, Aportes en Línea, Cámara de Comercio, correos, bancos).

Permite buscar por cédula o NIT y ver de forma visual todas las credenciales asociadas a esa entidad, con contraseñas cifradas, control de acceso por roles, auditoría de cambios y alertas automáticas del calendario tributario DIAN.

## Funcionalidades principales

- **Búsqueda por cédula/NIT o nombre**: resultados visuales con tarjetas por entidad.
- **Contraseñas cifradas**: ocultas por defecto, con botones para revelar y copiar.
- **Roles de usuario**:
  - **Administrador**: control total, gestión de usuarios, sitios y calendario tributario.
  - **Editor**: puede crear y modificar entidades y credenciales.
  - **Visualizador**: solo puede consultar.
- **Auditoría**: registro de quién creó, modificó, eliminó o reveló cada credencial.
- **Sitios configurables**: DIAN, Aportes en Línea, Cámara de Comercio, correos, bancos, y opción de agregar un sitio personalizado al vuelo desde el formulario de credencial.
- **Listado alfabético de entidades** con filtros por tipo (empresa/persona) y por lugar.
- **Calendario tributario DIAN**: alertas en el dashboard de las empresas con declaraciones (Retención en la Fuente, IVA Bimestral, IVA Cuatrimestral, Renta Persona Jurídica) próximas a vencer, calculadas según el último dígito del NIT. El calendario es administrable cada año desde el panel de administración.
- **Campo "Lugar"** por entidad (municipio), visible y buscable.

## Tecnologías

- **Backend**: Flask 3 (application factory + blueprints), SQLAlchemy 2, Flask-Login
- **Cifrado**: Fernet (librería `cryptography`) para las contraseñas almacenadas
- **Base de datos**: PostgreSQL (Supabase) en producción, SQLite en desarrollo local
- **Frontend**: Bootstrap 5 + Font Awesome (sin frameworks de JS, solo JS vanilla)
- **Despliegue**: Render.com (Gunicorn como servidor WSGI)

## Estructura del proyecto

```
app/
  __init__.py        # Application factory, seed de datos y calendario tributario
  models.py           # Modelos: User, Entity, Site, Credential, AuditLog, TaxDeadline
  auth/                # Login / logout
  main/                # Rutas principales (dashboard, entidades, credenciales, admin)
  templates/           # Plantillas Jinja2 (Bootstrap 5)
config.py              # Configuración (BD, cifrado, sesión)
run.py                 # Punto de entrada local
render.yaml             # Blueprint de despliegue en Render
scripts/
  import_excel.py       # Importación puntual de datos desde Excel (uso local)
```

## Configuración local

1. Clonar el repositorio e instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Crear un archivo `.env` en la raíz (puedes basarte en `.env.example`) con:
   ```
   SECRET_KEY=una-clave-secreta
   DATABASE_URL=sqlite:///passwords.db
   ENCRYPTION_KEY=clave-generada-con-fernet
   ```
   Para generar una `ENCRYPTION_KEY` válida:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. Ejecutar la aplicación:
   ```bash
   python run.py
   ```
   o hacer doble clic en `INICIAR_APP.bat` (Windows).
4. Abrir [http://localhost:5000](http://localhost:5000). Usuario administrador creado automáticamente:
   - **Usuario**: `admin`
   - **Contraseña**: `Admin123!` *(cámbiala después del primer ingreso)*

## Despliegue en producción

- **Hosting**: Render.com, usando `render.yaml` como Blueprint.
- **Base de datos**: PostgreSQL externo en Supabase (plan gratuito, sin expiración), conectado mediante el *connection pooler* de Supabase (necesario porque el plan gratuito de Render no soporta IPv6 hacia la conexión directa de Supabase).
- **Variables de entorno requeridas en Render**:
  - `SECRET_KEY`
  - `DATABASE_URL` (cadena de conexión del pooler de Supabase)
  - `ENCRYPTION_KEY`

Cualquier cambio subido a la rama `main` se despliega automáticamente en Render.

## Importación de datos desde Excel

El script `scripts/import_excel.py` permite importar de forma masiva un listado de empresas (hoja `EMPRESAS`) con sus accesos a correo, DIAN, Aportes en Línea y Cámara de Comercio. Es de uso local únicamente; el archivo Excel original **no** se sube al repositorio por contener contraseñas en texto plano.

```bash
python scripts/import_excel.py            # dry-run (no guarda cambios)
python scripts/import_excel.py --apply     # aplica los cambios
```

Para importar directamente en producción (Supabase), se ejecuta el mismo script localmente apuntando `DATABASE_URL` a la cadena de conexión de Supabase.

## Seguridad

- Las contraseñas se almacenan cifradas con Fernet (cifrado simétrico AES) usando `ENCRYPTION_KEY`; nunca se guardan en texto plano.
- Cada acceso a una contraseña (revelar) queda registrado en el log de auditoría.
- Las cookies de sesión son `HttpOnly` y `SameSite=Lax`.
