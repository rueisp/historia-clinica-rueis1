# manage.py
import click
from flask.cli import with_appcontext
from clinica import create_app
from clinica.extensions import db
from clinica.models import Usuario

app = create_app()

@click.group()
def cli():
    """Comandos de gestión."""
    pass

@click.command("crear-usuario")
@with_appcontext
@click.argument("username")
@click.argument("email")
@click.password_option() # Pide la contraseña de forma segura
@click.option("--admin", is_flag=True, help="Marcar este usuario como administrador.")
def crear_usuario(username, email, password, admin):
    """Crea un nuevo usuario en la base de datos."""
    if Usuario.query.filter_by(username=username).first():
        print(f"Error: El nombre de usuario '{username}' ya existe.")
        return
    if Usuario.query.filter_by(email=email).first():
        print(f"Error: El email '{email}' ya está en uso.")
        return
    
    nuevo_usuario = Usuario(
        username=username, 
        email=email, 
        is_admin=admin
    )
    nuevo_usuario.set_password(password)
    db.session.add(nuevo_usuario)
    db.session.commit()
    print(f"¡Usuario '{username}' creado exitosamente!")

cli.add_command(crear_usuario)

if __name__ == "__main__":
    cli()