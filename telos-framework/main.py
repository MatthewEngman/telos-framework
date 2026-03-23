import os
import sys

from telos.agent import TelosAgent
from telos.tir_compiler import TelosCompiler
from telos.schema import Invariant, Ontology, Teleology, TIRSchema

# Optional: Add your OpenAI API key here so you can test custom prompts
# os.environ["OPENAI_API_KEY"] = "sk-proj-..."
#
# Local LLM (no key): run `ollama serve`, pull a model (e.g. `ollama pull llama3.2`),
# then either omit OPENAI_API_KEY or set TELOS_LLM_BACKEND=ollama.
# Override host/model: OLLAMA_HOST, TELOS_OLLAMA_MODEL.


def run():
    print("========================================")
    print("       TELOS FRAMEWORK v0.1 ALPHA       ")
    print("========================================")

    # 1. The Human Intent
    intent = """
    I have a cloud app with 3 regional servers: US, EU, and Asia.
    Balance 100% of my traffic. Costs per unit are $10 for US, $20 for EU, and $30 for Asia.
    Minimize my total cost.
    Constraint: The US server is undergoing maintenance, mathematically guarantee it never takes more than 40% of the load.
    Also, due to privacy laws, Asia cannot process more than 5% of the data.
    """

    print(f"\n[Human Intent]:\n{intent.strip()}\n")

    # 2. Layer 1: Agent Translation
    agent = TelosAgent()
    tir_schema = agent.translate(intent)

    print("\n[Generated TIR Schema]:")
    print(tir_schema.model_dump_json(indent=2))
    print("-" * 40)

    # 3. Layer 2: Core Compilation
    compiler = TelosCompiler(tir_schema)
    matrix = compiler.compile()

    print("\n========================================")
    print(" FINAL EXECUTABLE MATRIX (Software state)")
    print("========================================")
    for var, val in matrix.items():
        print(f" > {var}: {val}")
    print("========================================\n")


def run_finance_tir():
    """Same universal compiler, different domain: portfolio weights (hand-authored TIR, no LLM)."""
    print("========================================")
    print("  TELOS - universal TIR (finance domain)  ")
    print("========================================")

    tir = TIRSchema(
        ontology=Ontology(
            variables=["stocks", "bonds", "cash"],
            bounds=[(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)],
        ),
        teleology=Teleology(
            direction="maximize",
            objective="0.10*stocks + 0.04*bonds + 0.01*cash",
        ),
        invariants=[
            Invariant(type="eq", expression="stocks + bonds + cash - 1.0"),
            Invariant(type="ineq", expression="cash - 0.15"),
            Invariant(type="ineq", expression="0.50 - stocks"),
        ],
    )

    print("\n[TIR] (authored directly - proves domain-agnostic engine)\n")
    print(tir.model_dump_json(indent=2))
    print("-" * 40)

    compiler = TelosCompiler(tir)
    matrix = compiler.compile()

    print("\n========================================")
    print(" FINAL EXECUTABLE MATRIX (Software state)")
    print("========================================")
    for var, val in matrix.items():
        print(f" > {var}: {val}")
    print("========================================\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "finance":
        run_finance_tir()
    else:
        run()
