from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from sabmec import db
from sabmec.models.compra import Compra, CompraItem, STATUS_COMPRA_PENDENTE
from sabmec.routes.comercial.compras.compras import compras_bp
from sabmec.routes.comercial.compras.compras_utils import (
    buscar_ou_criar_fornecedor,
    garantir_schema_compras,
    parse_xml_nfe,
    sugerir_item,
)


@compras_bp.route("/compras/importar", methods=["GET"])
@login_required
def compras_importar():
    return render_template("comercial/compras/compras_importar.html")


@compras_bp.route("/compras/conferir", methods=["POST"])
@login_required
def compras_conferir():
    garantir_schema_compras()

    xml_file = request.files.get("xml_file")
    if not xml_file or xml_file.filename == "":
        flash("Selecione um arquivo XML de nota fiscal.", "warning")
        return redirect(url_for("compras.compras_importar"))

    if not xml_file.filename.lower().endswith(".xml"):
        flash("O arquivo enviado deve ser do tipo .xml", "warning")
        return redirect(url_for("compras.compras_importar"))

    try:
        xml_content = xml_file.read().decode("utf-8", errors="ignore")
        dados = parse_xml_nfe(xml_content)

        nota_existente = Compra.query.filter_by(chave_acesso=dados["chave_acesso"]).first()
        if nota_existente:
            flash(f"Esta nota fiscal (NF {dados['numero_nota']}) ja foi importada anteriormente.", "warning")
            return redirect(url_for("compras.compras", pesquisar=1, tipo_busca="nota", busca=dados["numero_nota"]))

        fornecedor = buscar_ou_criar_fornecedor(dados["fornecedor"])

        compra = Compra(
            fornecedor_id=fornecedor.id,
            data_emissao=datetime.fromisoformat(dados["data_emissao"]),
            data_entrada=datetime.utcnow(),
            numero_nota=dados["numero_nota"],
            serie_nota=dados["serie"],
            chave_acesso=dados["chave_acesso"],
            valor_produtos=dados["valor_produtos"],
            valor_total=dados["valor_total"],
            status=STATUS_COMPRA_PENDENTE,
            xml_original=xml_content,
        )
        db.session.add(compra)
        db.session.flush()

        for item_xml in dados["itens"]:
            sugestao = sugerir_item(item_xml)
            db.session.add(CompraItem(
                compra_id=compra.id,
                item_id=sugestao.id if sugestao else None,
                codigo_fornecedor=item_xml["codigo_fornecedor"],
                descricao_fornecedor=item_xml["descricao"],
                quantidade=item_xml["quantidade"],
                valor_unitario=item_xml["valor_unitario"],
                valor_total=item_xml["valor_total"],
            ))

        db.session.commit()

        flash(f"XML da NF {compra.numero_nota} importado. Confira a nota para vincular/cadastrar os itens.", "success")
        return redirect(url_for("compras.compras", pesquisar=1, tipo_busca="nota", busca=compra.numero_nota))

    except Exception as erro:
        db.session.rollback()
        flash(f"Erro ao importar XML: {erro}", "danger")
        return redirect(url_for("compras.compras_importar"))
