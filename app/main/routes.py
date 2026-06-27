from collections import defaultdict
from datetime import datetime
from functools import wraps

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app import db
from app.models import Entity, Site, Credential, User, AuditLog
from app.main import bp


# ── Decoradores de permisos ────────────────────────────────────────────────

def editor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role == 'viewer':
            flash('No tienes permisos para realizar esta acción.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def _log(action, entity_type, entity_id, description):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        timestamp=datetime.utcnow(),
    ))


# ── Dashboard / Búsqueda ──────────────────────────────────────────────────

@bp.route('/')
@login_required
def dashboard():
    q = request.args.get('q', '').strip()
    entities = []
    if q:
        entities = Entity.query.filter(
            db.or_(
                Entity.cedula_nit.ilike(f'%{q}%'),
                Entity.name.ilike(f'%{q}%'),
            )
        ).order_by(Entity.name).all()
    recientes = Entity.query.order_by(Entity.created_at.desc()).limit(8).all()
    total_entities = Entity.query.count()
    total_credentials = Credential.query.count()
    return render_template('dashboard.html',
                           entities=entities, query=q,
                           recientes=recientes,
                           total_entities=total_entities,
                           total_credentials=total_credentials)


# ── Entidades ─────────────────────────────────────────────────────────────

@bp.route('/entity/<int:entity_id>')
@login_required
def entity_detail(entity_id):
    entity = Entity.query.get_or_404(entity_id)
    credentials = (Credential.query
                   .filter_by(entity_id=entity_id)
                   .join(Site)
                   .order_by(Site.category, Site.name)
                   .all())

    creds_by_cat = defaultdict(list)
    for cred in credentials:
        creds_by_cat[cred.site.category or 'otro'].append(cred)

    categories = [
        ('impuestos', 'Impuestos y Tributario', 'fa-calculator'),
        ('aportes',   'Aportes y Nómina',       'fa-users'),
        ('correo',    'Correos',                 'fa-envelope'),
        ('camara',    'Cámara de Comercio',      'fa-store'),
        ('banco',     'Bancos',                  'fa-university'),
        ('otro',      'Otros',                   'fa-ellipsis-h'),
    ]

    return render_template('entity_detail.html',
                           entity=entity,
                           creds_by_cat=dict(creds_by_cat),
                           categories=categories,
                           total=len(credentials))


@bp.route('/entity/new', methods=['GET', 'POST'])
@login_required
@editor_required
def new_entity():
    if request.method == 'POST':
        cedula = request.form.get('cedula_nit', '').strip()
        name = request.form.get('name', '').strip()
        etype = request.form.get('entity_type', 'persona')
        notes = request.form.get('notes', '').strip()

        if not cedula or not name:
            flash('Cédula/NIT y nombre son obligatorios.', 'danger')
            return render_template('entity_form.html', entity=None)

        if Entity.query.filter_by(cedula_nit=cedula).first():
            flash(f'Ya existe una entidad con cédula/NIT {cedula}.', 'danger')
            return render_template('entity_form.html', entity=None)

        entity = Entity(cedula_nit=cedula, name=name, entity_type=etype,
                        notes=notes, created_by_id=current_user.id)
        db.session.add(entity)
        db.session.flush()
        _log('create', 'entity', entity.id, f'Creó entidad: {name} ({cedula})')
        db.session.commit()
        flash(f'Entidad "{name}" creada exitosamente.', 'success')
        return redirect(url_for('main.entity_detail', entity_id=entity.id))

    return render_template('entity_form.html', entity=None)


@bp.route('/entity/<int:entity_id>/edit', methods=['GET', 'POST'])
@login_required
@editor_required
def edit_entity(entity_id):
    entity = Entity.query.get_or_404(entity_id)

    if request.method == 'POST':
        entity.name = request.form.get('name', '').strip()
        entity.entity_type = request.form.get('entity_type', entity.entity_type)
        entity.notes = request.form.get('notes', '').strip()
        _log('update', 'entity', entity.id, f'Modificó entidad: {entity.name}')
        db.session.commit()
        flash('Entidad actualizada correctamente.', 'success')
        return redirect(url_for('main.entity_detail', entity_id=entity.id))

    return render_template('entity_form.html', entity=entity)


# ── Credenciales ──────────────────────────────────────────────────────────

@bp.route('/entity/<int:entity_id>/credential/new', methods=['GET', 'POST'])
@login_required
@editor_required
def new_credential(entity_id):
    entity = Entity.query.get_or_404(entity_id)
    sites = Site.query.filter_by(is_active=True).order_by(Site.category, Site.name).all()

    if request.method == 'POST':
        site_id = request.form.get('site_id', '')
        if not site_id:
            flash('Debes seleccionar un sitio web.', 'danger')
            return render_template('credential_form.html', entity=entity, sites=sites, credential=None)

        cred = Credential(
            entity_id=entity_id,
            site_id=int(site_id),
            username=request.form.get('username', '').strip(),
            alt_username=request.form.get('alt_username', '').strip(),
            notes=request.form.get('notes', '').strip(),
            created_by_id=current_user.id,
        )
        password = request.form.get('password', '').strip()
        if password:
            cred.set_password(password)

        db.session.add(cred)
        db.session.flush()
        site = Site.query.get(int(site_id))
        _log('create', 'credential', cred.id,
             f'Agregó credencial para {entity.name} en {site.name}')
        db.session.commit()
        flash('Credencial agregada exitosamente.', 'success')
        return redirect(url_for('main.entity_detail', entity_id=entity_id))

    return render_template('credential_form.html', entity=entity, sites=sites, credential=None)


@bp.route('/credential/<int:credential_id>/edit', methods=['GET', 'POST'])
@login_required
@editor_required
def edit_credential(credential_id):
    cred = Credential.query.get_or_404(credential_id)
    entity = cred.entity
    sites = Site.query.filter_by(is_active=True).order_by(Site.category, Site.name).all()

    if request.method == 'POST':
        cred.site_id = int(request.form.get('site_id', cred.site_id))
        cred.username = request.form.get('username', '').strip()
        cred.alt_username = request.form.get('alt_username', '').strip()
        cred.notes = request.form.get('notes', '').strip()
        cred.updated_by_id = current_user.id
        cred.updated_at = datetime.utcnow()

        password = request.form.get('password', '').strip()
        if password:
            cred.set_password(password)

        _log('update', 'credential', cred.id,
             f'Modificó credencial de {entity.name} en {cred.site.name}')
        db.session.commit()
        flash('Credencial actualizada.', 'success')
        return redirect(url_for('main.entity_detail', entity_id=entity.id))

    return render_template('credential_form.html', entity=entity, sites=sites, credential=cred)


@bp.route('/credential/<int:credential_id>/delete', methods=['POST'])
@login_required
@editor_required
def delete_credential(credential_id):
    cred = Credential.query.get_or_404(credential_id)
    entity_id = cred.entity_id
    _log('delete', 'credential', credential_id,
         f'Eliminó credencial de {cred.entity.name} en {cred.site.name}')
    db.session.delete(cred)
    db.session.commit()
    flash('Credencial eliminada.', 'success')
    return redirect(url_for('main.entity_detail', entity_id=entity_id))


@bp.route('/credential/<int:credential_id>/password')
@login_required
def reveal_password(credential_id):
    cred = Credential.query.get_or_404(credential_id)
    try:
        pwd = cred.get_password()
        _log('view', 'credential', credential_id,
             f'Reveló contraseña de {cred.entity.name} en {cred.site.name}')
        db.session.commit()
        return jsonify({'password': pwd})
    except Exception:
        return jsonify({'error': 'No se pudo descifrar la contraseña.'}), 500


# ── Admin: Usuarios ───────────────────────────────────────────────────────

@bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.role, User.username).all()
    return render_template('admin/users.html', users=users)


@bp.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'viewer')

        if not all([username, email, password]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', user=None)

        if User.query.filter_by(username=username).first():
            flash('Ese nombre de usuario ya está en uso.', 'danger')
            return render_template('admin/user_form.html', user=None)

        if User.query.filter_by(email=email).first():
            flash('Ese correo ya está registrado.', 'danger')
            return render_template('admin/user_form.html', user=None)

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        _log('create', 'user', user.id, f'Creó usuario: {username} ({role})')
        db.session.commit()
        flash(f'Usuario "{username}" creado exitosamente.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('admin/user_form.html', user=None)


@bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.email = request.form.get('email', '').strip()
        new_role = request.form.get('role', user.role)
        if user.id == current_user.id and new_role != 'admin':
            flash('No puedes quitarte el rol de administrador a ti mismo.', 'danger')
            return render_template('admin/user_form.html', user=user)
        user.role = new_role
        user.is_active = 'is_active' in request.form

        password = request.form.get('password', '').strip()
        if password:
            user.set_password(password)

        _log('update', 'user', user.id, f'Modificó usuario: {user.username}')
        db.session.commit()
        flash(f'Usuario "{user.username}" actualizado.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('admin/user_form.html', user=user)


# ── Admin: Sitios ─────────────────────────────────────────────────────────

@bp.route('/admin/sites')
@login_required
@admin_required
def admin_sites():
    sites = Site.query.order_by(Site.category, Site.name).all()
    return render_template('admin/sites.html', sites=sites)


@bp.route('/admin/sites/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_site():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        url = request.form.get('url', '').strip()
        category = request.form.get('category', 'otro')

        if not name:
            flash('El nombre del sitio es obligatorio.', 'danger')
            return render_template('admin/site_form.html', site=None,
                                   categories=Site.CATEGORIES)

        if Site.query.filter_by(name=name).first():
            flash('Ya existe un sitio con ese nombre.', 'danger')
            return render_template('admin/site_form.html', site=None,
                                   categories=Site.CATEGORIES)

        site = Site(name=name, url=url, category=category)
        db.session.add(site)
        db.session.flush()
        _log('create', 'site', site.id, f'Creó sitio web: {name}')
        db.session.commit()
        flash(f'Sitio "{name}" agregado.', 'success')
        return redirect(url_for('main.admin_sites'))

    return render_template('admin/site_form.html', site=None, categories=Site.CATEGORIES)


@bp.route('/admin/sites/<int:site_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_site(site_id):
    site = Site.query.get_or_404(site_id)

    if request.method == 'POST':
        site.name = request.form.get('name', '').strip()
        site.url = request.form.get('url', '').strip()
        site.category = request.form.get('category', site.category)
        site.is_active = 'is_active' in request.form
        _log('update', 'site', site.id, f'Modificó sitio: {site.name}')
        db.session.commit()
        flash('Sitio actualizado.', 'success')
        return redirect(url_for('main.admin_sites'))

    return render_template('admin/site_form.html', site=site, categories=Site.CATEGORIES)


# ── Admin: Auditoría ──────────────────────────────────────────────────────

@bp.route('/admin/audit')
@login_required
@admin_required
def admin_audit():
    page = request.args.get('page', 1, type=int)
    logs = (AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .paginate(page=page, per_page=50, error_out=False))
    return render_template('admin/audit.html', logs=logs)
