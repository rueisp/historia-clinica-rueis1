# app.py (o puedes llamarlo run.py)

from clinica import create_app
from manage import cli 

app = create_app()
app.cli.add_command(cli)

if __name__ == '__main__':
    app.run(debug=True)