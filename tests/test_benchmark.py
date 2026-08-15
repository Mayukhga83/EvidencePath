from evidencepath.cases import generated_cases
from evidencepath.logic import evaluate
from evidencepath.benchmark import run_benchmark,evaluate_one,STRATEGIES
from evidencepath.retrieval import rank_documents


def test_generator_is_reproducible():
    a,b=generated_cases(7,seed=4),generated_cases(7,seed=4)
    assert [(x.initial,x.supplier_answers) for x in a]==[(x.initial,x.supplier_answers) for x in b]


def test_benchmark_baselines():
    raw,summary=run_benchmark(15,7)
    assert len(raw)==15*len(STRATEGIES)
    assert len(summary)==len(STRATEGIES)
    assert (raw['incorrect_decisions']==0).all()
    assert (raw['cost']>=0).all()


def test_retrieval_modes():
    case=generated_cases(1)[0]
    for mode in ('bm25','dense','hybrid'):
        ranked=rank_documents('audit logging data',list(case.documents),mode)
        assert len(ranked)==len(case.documents)
        assert all(score>=-0.000001 for _,score in ranked) if mode!='dense' else True
