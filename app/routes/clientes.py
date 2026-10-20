
from flask import Blueprint, render_template, request, current_app
from app.database import obtener_conexion

clientes_bp = Blueprint("clientes", __name__)


@clientes_bp.route("/")
def inicio():
    contenido = None
    conexion = cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM contenido_inicio WHERE id = 1"
        )
        contenido = cursor.fetchone()

    except Exception:
        current_app.logger.exception(
            "No se pudo cargar el contenido de Inicio."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

    return render_template(
        "secciones/inicio.html",
        contenido=contenido
    )


@clientes_bp.route("/nosotros")
def nosotros():
    return render_template("secciones/nosotros.html")


@clientes_bp.route("/productos")
def productos():
    conexion = cursor = None
    lista_productos = []

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, descripcion, categoria,
                   precio, unidad, imagen
            FROM producto
            WHERE activo = 1
            ORDER BY id DESC
        """)

        lista_productos = cursor.fetchall()

    except Exception:
        current_app.logger.exception(
            "Error al consultar la tabla producto."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

    return render_template(
        "secciones/productos.html",
        productos=lista_productos
    )


@clientes_bp.route("/contacto", methods=["GET", "POST"])
def contacto():

    if request.method == "GET":
        return render_template("secciones/contacto.html")

    nombre = request.form.get("nombre", "").strip()
    empresa = request.form.get("empresa", "").strip()
    correo = request.form.get("correo", "").strip()
    telefono = request.form.get("telefono", "").strip()
    asunto = request.form.get("asunto", "").strip()
    mensaje = request.form.get("mensaje", "").strip()

    if not all([nombre, correo, asunto, mensaje]):
        return render_template(
            "secciones/contacto.html",
            error="Completa los campos obligatorios."
        )

    conexion = cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO consultas
                (nombre, empresa, correo, telefono, asunto, mensaje)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            nombre,
            empresa,
            correo,
            telefono,
            asunto,
            mensaje
        ))

        conexion.commit()

        return render_template(
            "secciones/contacto.html",
            enviada=True
        )

    except Exception:
        if conexion:
            conexion.rollback()

        current_app.logger.exception(
            "Error al registrar la consulta en MySQL."
        )

        return render_template(
            "secciones/contacto.html",
            error="No se pudo guardar la consulta. Revisa la terminal."
        ), 500

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@clientes_bp.route("/solicitud", methods=["GET", "POST"])
def solicitud():

    conexion = cursor = None
    lista_productos = []

    # Obtener los productos disponibles para el formulario.
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, unidad
            FROM producto
            WHERE activo = 1
            ORDER BY nombre
        """)

        lista_productos = cursor.fetchall()

    except Exception:
        current_app.logger.exception(
            "No se pudieron cargar los productos para solicitar."
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

    if request.method == "GET":
        return render_template(
            "secciones/solicitud.html",
            productos=lista_productos
        )

    empresa = request.form.get("empresa", "").strip()
    ruc = request.form.get("ruc", "").strip()
    contacto = request.form.get("contacto", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip()
    producto_id = request.form.get("producto_id", "").strip()
    cantidad = request.form.get("cantidad", "").strip()
    fecha = request.form.get("fecha") or None
    mensaje = request.form.get("mensaje", "").strip()

    if not all([
        empresa, ruc, contacto, telefono,
        correo, producto_id, cantidad
    ]):
        return render_template(
            "secciones/solicitud.html",
            productos=lista_productos,
            error="Completa todos los campos obligatorios."
        )

    
    try:
        producto_id = int(producto_id.strip())
        cantidad_texto = cantidad.strip().replace(",", ".")
        cantidad = float(cantidad_texto)

        if producto_id <= 0 or cantidad <= 0:
            raise ValueError

    except (ValueError, TypeError, AttributeError):
        current_app.logger.warning(
            "Solicitud inválida: producto_id=%r, cantidad=%r",
            producto_id,
            cantidad
        )

        return render_template(
            "secciones/solicitud.html",
            productos=lista_productos,
            error="Selecciona un producto y una cantidad válida."
        ), 400


    conexion = cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        # Verificar que el producto exista y esté publicado.
        cursor.execute("""
            SELECT id, nombre, unidad
            FROM producto
            WHERE id = %s AND activo = 1
        """, (producto_id,))

        producto = cursor.fetchone()

        if not producto:
            return render_template(
                "secciones/solicitud.html",
                productos=lista_productos,
                error="El producto seleccionado no está disponible."
            ), 400

        # Guardar la solicitud en la tabla solicitudes.
        cursor.execute("""
            INSERT INTO solicitudes
                (empresa, ruc, contacto, telefono, correo,
                 producto_id, producto, cantidad_kg,
                 cantidad, unidad, fecha, mensaje)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            empresa,
            ruc,
            contacto,
            telefono,
            correo,
            producto["id"],
            producto["nombre"],
            cantidad,
            cantidad,
            producto["unidad"],
            fecha,
            mensaje
        ))

        # Confirmar el registro en la base de datos.
        conexion.commit()

        return render_template(
            "secciones/solicitud.html",
            productos=lista_productos,
            enviada=True
        )

    except Exception:
        if conexion:
            conexion.rollback()

        current_app.logger.exception(
            "Error al guardar la solicitud en MySQL."
        )

        return render_template(
            "secciones/solicitud.html",
            productos=lista_productos,
            error="No se pudo guardar la solicitud. Revisa la terminal."
        ), 500

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()