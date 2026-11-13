from app.ferramentas import extrair_cnpj, extrair_data_emissao, extrair_valor_total, validar_cnpj


def test_cnpj_valido_e_invalido():
    assert validar_cnpj("11.222.333/0001-81")
    assert not validar_cnpj("11.222.333/0001-82")
    assert not validar_cnpj("00000000000000")


def test_extrai_cnpj_ignorando_invalidos():
    texto = "CNPJ errado 11.222.333/0001-99 e certo 11.222.333/0001-81"
    assert extrair_cnpj(texto) == "11222333000181"


def test_valor_total_prefere_linha_de_total():
    texto = "Valor dos serviços: R$ 1.250,00\nISS: R$ 62,50\nVALOR TOTAL DA NOTA: R$ 1.187,50"
    assert extrair_valor_total(texto) == 1187.50


def test_valor_total_sem_linha_usa_maior():
    assert extrair_valor_total("Item R$ 10,00\nItem R$ 2.000,10") == 2000.10


def test_datas_br_e_iso():
    assert extrair_data_emissao("Emitida em 05/03/2026") == "2026-03-05"
    assert extrair_data_emissao("Emitida em 2026-02-14") == "2026-02-14"
    assert extrair_data_emissao("31/02/2026 inválida") is None
