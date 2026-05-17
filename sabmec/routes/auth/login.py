from flask import Blueprint, render_template, flash, redirect, url_for
from sabmec.forms.pessoas_forms import FormLogin
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    from sabmec.models.pessoas import PessoaUsuario
    form_login = FormLogin()

    if form_login.validate_on_submit():
        usuario_input = form_login.usuario.data.upper()
        senha_input = form_login.senha.data

        usuario = PessoaUsuario.query.filter_by(usuario=usuario_input).first()

        if usuario:
            if check_password_hash(usuario.senha_hash, senha_input):
                login_user(usuario)
                return redirect(url_for('main.home'))
            else:
                flash("Senha incorreta!", "danger")
        else:
            flash("Usuário não encontrado!", "danger")

    return render_template('auth/login.html', form=form_login)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))