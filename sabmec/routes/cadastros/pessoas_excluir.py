from sqlalchemy import select, func
from flask import redirect, url_for, flash
from flask_login import login_required

from sabmec import db
from sabmec.routes.cadastros.pessoas import pessoas_bp
from sabmec.models.pessoas import (
    Pessoa,
    PessoaCliente,
    PessoaContato,
    PessoaEndereco,
    PessoaFornecedor,
    PessoaUsuario,
    PessoaFilial,
)


TABELAS_INTERNAS_PESSOA = {
    "pessoas_cliente",
    "pessoas_contato",
    "pessoas_endereco",
    "pessoas_fornecedor",
    "pessoas_usuario",
    "pessoas_filial",
}


def buscar_vinculos_bloqueantes(pessoa_id):
    vinculos = []

    for tabela in db.metadata.tables.values():
        if tabela.name == "pessoas" or tabela.name in TABELAS_INTERNAS_PESSOA:
            continue

        for fk in tabela.foreign_keys:
            if fk.column.table.name == "pessoas":
                total = db.session.execute(
                    select(func.count())
                    .select_from(tabela)
                    .where(fk.parent == pessoa_id)
                ).scalar()

                if total:
                    vinculos.append(f"{tabela.name} ({total})")

    return vinculos


def excluir_dados_internos_pessoa(pessoa_id):
    PessoaContato.query.filter_by(pessoa_id=pessoa_id).delete()
    PessoaEndereco.query.filter_by(pessoa_id=pessoa_id).delete()
    PessoaCliente.query.filter_by(pessoa_id=pessoa_id).delete()
    PessoaFornecedor.query.filter_by(pessoa_id=pessoa_id).delete()
    PessoaUsuario.query.filter_by(pessoa_id=pessoa_id).delete()
    # PessoaFilial.query.filter_by(pessoa_id=pessoa_id).delete()


@pessoas_bp.route("/pessoas/<int:id>/excluir", methods=["POST"])
@login_required
def pessoas_excluir(id):
    pessoa = Pessoa.query.get_or_404(id)


    if PessoaFilial.query.filter_by(pessoa_id=id).first() is not None:
        flash("Este cadastro é da Filial! Não é possivel excluir", "warning")
        return redirect(url_for("pessoas.pessoas"))

    try:
        vinculos = buscar_vinculos_bloqueantes(pessoa.id)

        if vinculos:
            pessoa.ativo = False
            db.session.commit()

            flash(
                "Este cadastro possui vínculos no sistema e não pode ser excluído. "
                "Ele foi inativado. Vínculos encontrados: " + ", ".join(vinculos),
                "warning",
            )
            return redirect(url_for("pessoas.pessoas"))

        excluir_dados_internos_pessoa(pessoa.id)
        db.session.delete(pessoa)
        db.session.commit()

        flash("Pessoa excluída com sucesso.", "success")
        return redirect(url_for("pessoas.pessoas"))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao excluir pessoa: {erro}", "danger")
        return redirect(url_for("pessoas.pessoas"))
