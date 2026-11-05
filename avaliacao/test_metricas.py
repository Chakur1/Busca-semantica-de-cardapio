import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from avaliar import normalizar, recall_em_k, reciprocal_rank


def test_recall_acerto_total():
    assert recall_em_k([1, 2], [1, 2, 3, 4, 5]) == 1.0


def test_recall_parcial():
    assert recall_em_k([1, 2, 3, 4], [1, 9, 3, 8, 7]) == 0.5


def test_recall_nenhum():
    assert recall_em_k([1, 2], [3, 4, 5, 6, 7]) == 0.0


def test_recall_ignora_o_que_esta_alem_do_k():
    assert recall_em_k([1], [2, 3, 4, 5, 6, 1]) == 0.0


def test_reciprocal_rank_primeiro_lugar():
    assert reciprocal_rank([7], [7, 2, 3]) == 1.0


def test_reciprocal_rank_segundo_lugar():
    assert reciprocal_rank([7], [2, 7, 3]) == 0.5


def test_reciprocal_rank_terceiro_lugar():
    assert reciprocal_rank([7], [2, 3, 7]) == 1 / 3


def test_reciprocal_rank_nenhum():
    assert reciprocal_rank([7], [1, 2, 3]) == 0.0


def test_normalizar_remove_acentos_pontuacao_e_palavras_ignoradas():
    assert normalizar("Quero um Açaí, com Granola!") == ["acai", "granola"]
