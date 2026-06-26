from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import xml.etree.ElementTree as ET

from sqlalchemy import text

from sabmec import db
from sabmec.models.contas_pagar import ContaPagar
from sabmec.models.estados_cidades import Cidade, Estado
from sabmec.models.item import Item, ItemMercadoria
from sabmec.models.pessoas import Pessoa, PessoaEndereco, PessoaFornecedor
from sabmec.models.tipos import Status


def garantir_schema_compras():
    colunas_compra = {
        row[1]: row
        for row in db.session.execute(text("PRAGMA table_info(compras)")).fetchall()
    }

    if "status" not in colunas_compra:
        db.session.execute(
            text("ALTER TABLE compras ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE'")
        )

    if "cancelado_em" not in colunas_compra:
        db.session.execute(text("ALTER TABLE compras ADD COLUMN cancelado_em DATETIME"))

    colunas_item = {
        row[1]: row
        for row in db.session.execute(text("PRAGMA table_info(compras_item)")).fetchall()
    }

    if colunas_item and colunas_item.get("item_id") and colunas_item["item_id"][3] == 1:
        db.session.execute(text("PRAGMA foreign_keys=OFF"))
        db.session.execute(text("ALTER TABLE compras_item RENAME TO compras_item_old"))
        db.session.execute(text("""
            CREATE TABLE compras_item (
                id INTEGER NOT NULL,
                compra_id INTEGER NOT NULL,
                item_id INTEGER,
                codigo_fornecedor VARCHAR(50),
                descricao_fornecedor VARCHAR(255),
                quantidade NUMERIC(10, 3) NOT NULL,
                valor_unitario NUMERIC(10, 2) NOT NULL,
                valor_total NUMERIC(10, 2) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(compra_id) REFERENCES compras (id),
                FOREIGN KEY(item_id) REFERENCES itens (id)
            )
        """))
        db.session.execute(text("""
            INSERT INTO compras_item (
                id, compra_id, item_id, codigo_fornecedor, descricao_fornecedor,
                quantidade, valor_unitario, valor_total
            )
            SELECT
                id, compra_id, item_id, codigo_fornecedor, descricao_fornecedor,
                quantidade, valor_unitario, valor_total
            FROM compras_item_old
        """))
        db.session.execute(text("DROP TABLE compras_item_old"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_compra_item_compra_id ON compras_item (compra_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_compra_item_item_id ON compras_item (item_id)"))
        db.session.execute(text("PRAGMA foreign_keys=ON"))

    db.session.commit()


def decimal_ou_zero(valor):
    if valor in [None, ""]:
        return Decimal("0")

    valor = str(valor).strip()

    try:
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        return Decimal(valor)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def parse_xml_nfe(xml_content):
    xml_content = re.sub(r' xmlns="[^"]+"', "", xml_content)
    xml_content = re.sub(r' xmlns:[a-zA-Z0-9]+="[^"]+"', "", xml_content)

    root = ET.fromstring(xml_content)

    ide = root.find(".//ide")
    n_nf = int(ide.find("nNF").text) if ide is not None and ide.find("nNF") is not None else 0
    serie = ide.find("serie").text if ide is not None and ide.find("serie") is not None else "1"
    dh_emi_str = None

    if ide is not None:
        dh_emi_str = ide.find("dhEmi").text if ide.find("dhEmi") is not None else None
        if not dh_emi_str and ide.find("dEmi") is not None:
            dh_emi_str = ide.find("dEmi").text

    if dh_emi_str:
        try:
            dh_emi = datetime.fromisoformat(dh_emi_str[:19])
        except ValueError:
            dh_emi = datetime.utcnow()
    else:
        dh_emi = datetime.utcnow()

    ch_nfe = ""
    inf_prot = root.find(".//infProt")
    if inf_prot is not None and inf_prot.find("chNFe") is not None:
        ch_nfe = inf_prot.find("chNFe").text
    else:
        inf_nfe = root.find(".//infNFe")
        if inf_nfe is not None and "Id" in inf_nfe.attrib:
            ch_nfe = inf_nfe.attrib["Id"].replace("NFe", "")

    total_tag = root.find(".//ICMSTot")
    v_prod = (
        decimal_ou_zero(total_tag.find("vProd").text)
        if total_tag is not None and total_tag.find("vProd") is not None
        else Decimal("0")
    )
    v_nf = (
        decimal_ou_zero(total_tag.find("vNF").text)
        if total_tag is not None and total_tag.find("vNF") is not None
        else Decimal("0")
    )

    emit = root.find(".//emit")
    cnpj = None
    if emit is not None:
        cnpj = emit.find("CNPJ").text if emit.find("CNPJ") is not None else None
        if not cnpj and emit.find("CPF") is not None:
            cnpj = emit.find("CPF").text

    x_nome = emit.find("xNome").text if emit is not None and emit.find("xNome") is not None else "Fornecedor Importado"
    x_fant = emit.find("xFant").text if emit is not None and emit.find("xFant") is not None else None
    ie = emit.find("IE").text if emit is not None and emit.find("IE") is not None else None

    logradouro = numero = complemento = bairro = cep = c_mun = x_mun = uf = None
    ender_emit = emit.find("enderEmit") if emit is not None else None
    if ender_emit is not None:
        logradouro = ender_emit.find("xLgr").text if ender_emit.find("xLgr") is not None else None
        numero = ender_emit.find("nro").text if ender_emit.find("nro") is not None else "S/N"
        complemento = ender_emit.find("xCpl").text if ender_emit.find("xCpl") is not None else None
        bairro = ender_emit.find("xBairro").text if ender_emit.find("xBairro") is not None else None
        cep = ender_emit.find("CEP").text if ender_emit.find("CEP") is not None else None
        c_mun = ender_emit.find("cMun").text if ender_emit.find("cMun") is not None else None
        x_mun = ender_emit.find("xMun").text if ender_emit.find("xMun") is not None else None
        uf = ender_emit.find("UF").text if ender_emit.find("UF") is not None else None

    itens = []
    for det in root.findall(".//det"):
        prod = det.find("prod")
        if prod is None:
            continue

        itens.append({
            "codigo_fornecedor": prod.find("cProd").text if prod.find("cProd") is not None else None,
            "descricao": (prod.find("xProd").text if prod.find("xProd") is not None else "PRODUTO SEM DESCRICAO").upper(),
            "ncm": prod.find("NCM").text if prod.find("NCM") is not None else None,
            "origem": prod.find("orig").text if prod.find("orig") is not None else "0",
            "quantidade": float(decimal_ou_zero(prod.find("qCom").text) if prod.find("qCom") is not None else Decimal("0")),
            "valor_unitario": float(decimal_ou_zero(prod.find("vUnCom").text) if prod.find("vUnCom") is not None else Decimal("0")),
            "valor_total": float(decimal_ou_zero(prod.find("vProd").text) if prod.find("vProd") is not None else Decimal("0")),
        })

    duplicatas = []
    for dup in root.findall(".//dup"):
        vencimento = date.today()
        vencimento_texto = dup.find("dVenc").text if dup.find("dVenc") is not None else None
        if vencimento_texto:
            try:
                vencimento = date.fromisoformat(vencimento_texto)
            except ValueError:
                vencimento = date.today()

        duplicatas.append({
            "numero": dup.find("nDup").text if dup.find("nDup") is not None else "",
            "vencimento": vencimento.isoformat(),
            "valor": float(decimal_ou_zero(dup.find("vDup").text) if dup.find("vDup") is not None else Decimal("0")),
        })

    return {
        "numero_nota": n_nf,
        "serie": serie,
        "data_emissao": dh_emi.isoformat(),
        "chave_acesso": ch_nfe,
        "valor_produtos": float(v_prod),
        "valor_total": float(v_nf),
        "fornecedor": {
            "cnpj": cnpj,
            "nome": x_nome.upper(),
            "nome_fantasia": x_fant.upper() if x_fant else None,
            "ie": ie,
            "logradouro": logradouro,
            "numero": numero,
            "complemento": complemento,
            "bairro": bairro,
            "cep": cep,
            "c_mun": c_mun,
            "x_mun": x_mun,
            "uf": uf,
        },
        "itens": itens,
        "duplicatas": duplicatas,
    }


def buscar_ou_criar_fornecedor(dados_fornecedor):
    fornecedor = Pessoa.query.filter(
        Pessoa.eh_fornecedor.is_(True),
        Pessoa.documento_fiscal == dados_fornecedor["cnpj"],
    ).first()

    if fornecedor:
        return fornecedor

    fornecedor = Pessoa(
        nome=dados_fornecedor["nome"],
        nome_fantasia=dados_fornecedor["nome_fantasia"],
        documento_fiscal=dados_fornecedor["cnpj"],
        ie_rg=dados_fornecedor["ie"],
        entidade="PJ",
        eh_fornecedor=True,
        ativo=True,
    )
    db.session.add(fornecedor)
    db.session.flush()

    db.session.add(PessoaFornecedor(pessoa_id=fornecedor.id, fornecedor_ativo=True))

    if dados_fornecedor["logradouro"]:
        criar_endereco_fornecedor(fornecedor, dados_fornecedor)

    return fornecedor


def criar_endereco_fornecedor(fornecedor, dados_fornecedor):
    cidade_id = None
    estado_id = None

    if dados_fornecedor["uf"]:
        estado = Estado.query.filter_by(uf=dados_fornecedor["uf"].strip().upper()).first()
        if estado:
            estado_id = estado.id

            if dados_fornecedor["c_mun"]:
                c_mun_int = int(dados_fornecedor["c_mun"])
                cidade = Cidade.query.filter(
                    (Cidade.codigo_ibge == c_mun_int)
                    | (Cidade.codigo_ibge == c_mun_int // 10)
                ).first()

                if cidade:
                    cidade_id = cidade.id
                    estado_id = cidade.estado_id
                elif dados_fornecedor["x_mun"]:
                    cidade = Cidade.query.filter(
                        Cidade.nome.ilike(dados_fornecedor["x_mun"].strip()),
                        Cidade.estado_id == estado.id,
                    ).first()
                    if cidade:
                        cidade_id = cidade.id

    if estado_id and not cidade_id:
        cidade = Cidade.query.filter_by(estado_id=estado_id).first()
        if cidade:
            cidade_id = cidade.id

    if cidade_id and estado_id:
        db.session.add(PessoaEndereco(
            pessoa_id=fornecedor.id,
            logradouro=dados_fornecedor["logradouro"].upper(),
            numero=dados_fornecedor["numero"].upper() if dados_fornecedor["numero"] else "S/N",
            complemento=dados_fornecedor["complemento"].upper() if dados_fornecedor["complemento"] else None,
            bairro=dados_fornecedor["bairro"].upper() if dados_fornecedor["bairro"] else "CENTRO",
            cidade_id=cidade_id,
            estado_id=estado_id,
            cep=dados_fornecedor["cep"] if dados_fornecedor["cep"] else "00000000",
            principal=True,
        ))


def sugerir_item(item_xml):
    primeira_palavra = (item_xml["descricao"].split() or [""])[0]

    sugestao = Item.query.filter(
        Item.tipo == "Produto",
        Item.nome.ilike(f"%{primeira_palavra}%"),
    ).first()

    if not sugestao:
        sugestao = Item.query.filter(
            Item.tipo == "Produto",
            Item.nome.ilike(f"%{item_xml['descricao']}%"),
        ).first()

    return sugestao


def dados_conferencia(compra):
    dados = parse_xml_nfe(compra.xml_original)
    itens = []

    for index, item_xml in enumerate(dados["itens"]):
        compra_item = compra.itens[index] if index < len(compra.itens) else None
        sugestao = compra_item.item if compra_item and compra_item.item else sugerir_item(item_xml)

        itens.append({
            "index": index,
            "codigo_fornecedor": item_xml["codigo_fornecedor"],
            "descricao": item_xml["descricao"],
            "ncm": item_xml["ncm"],
            "origem": item_xml["origem"],
            "quantidade": item_xml["quantidade"],
            "valor_unitario": item_xml["valor_unitario"],
            "valor_total": item_xml["valor_total"],
            "sugestao_id": sugestao.id if sugestao else 0,
            "sugestao_nome": sugestao.nome if sugestao else None,
        })

    return dados, itens


def aplicar_estoque_item(compra_item, item_xml, item_id):
    produto = Item.query.get(item_id)

    if not produto or not produto.mercadoria:
        raise ValueError(f"Produto vinculado ao item {item_xml['descricao']} nao possui cadastro de mercadoria.")

    produto.mercadoria.estoque = (produto.mercadoria.estoque or 0) + int(decimal_ou_zero(item_xml["quantidade"]))
    produto.mercadoria.custo = Decimal(str(item_xml["valor_unitario"]))

    if not produto.mercadoria.ncm:
        produto.mercadoria.ncm = item_xml["ncm"]
    if not produto.mercadoria.origem:
        produto.mercadoria.origem = item_xml["origem"]

    compra_item.item_id = item_id


def criar_produto_compra(item_xml):
    preco_venda = Decimal(str(item_xml["valor_unitario"])) * Decimal("1.5")

    novo_produto = Item(
        nome=item_xml["descricao"],
        preco=preco_venda.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        tipo="Produto",
        ativo=True,
    )
    db.session.add(novo_produto)
    db.session.flush()

    db.session.add(ItemMercadoria(
        item_id=novo_produto.id,
        estoque=int(decimal_ou_zero(item_xml["quantidade"])),
        custo=Decimal(str(item_xml["valor_unitario"])),
        ncm=item_xml["ncm"],
        origem=item_xml["origem"],
    ))

    return novo_produto


def gerar_contas_pagar(compra, dados):
    status_pendente = Status.query.filter(Status.situacao.ilike("PENDENTE")).first()
    if not status_pendente:
        raise ValueError("Cadastre o status PENDENTE antes de confirmar entradas.")

    excluir_contas_pagar_compra(compra)

    if dados["duplicatas"]:
        for dup in dados["duplicatas"]:
            db.session.add(ContaPagar(
                fornecedor_id=compra.fornecedor_id,
                status_id=status_pendente.id,
                origem="COMPRA",
                referencia_id=compra.id,
                descricao=f"NF {compra.numero_nota}/{compra.serie_nota} - DUPLICATA {dup['numero'] or '1'}",
                parcela=dup["numero"] if dup["numero"] else "1/1",
                documento=str(compra.numero_nota),
                valor=Decimal(str(dup["valor"])),
                vencimento=date.fromisoformat(dup["vencimento"]),
                observacao=f"PARCELA IMPORTADA VIA XML. CHAVE: {compra.chave_acesso}",
            ))
        return

    db.session.add(ContaPagar(
        fornecedor_id=compra.fornecedor_id,
        status_id=status_pendente.id,
        origem="COMPRA",
        referencia_id=compra.id,
        descricao=f"NF {compra.numero_nota}/{compra.serie_nota} - UNICA",
        parcela="1/1",
        documento=str(compra.numero_nota),
        valor=compra.valor_total,
        vencimento=date.today(),
        observacao=f"PARCELA UNICA GERADA AUTOMATICAMENTE. CHAVE: {compra.chave_acesso}",
    ))


def excluir_contas_pagar_compra(compra):
    for conta in ContaPagar.query.filter_by(origem="COMPRA", referencia_id=compra.id).all():
        db.session.delete(conta)
