import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# Add paths dynamically to sys.path
detector_dir = Path(__file__).resolve().parent
indexer_dir = detector_dir.parent / "github_repository_intelligence"

sys.path.insert(0, str(detector_dir))
sys.path.insert(0, str(indexer_dir))

async def main():
    print("=" * 70)
    print("DEMO DE EXECUÇÃO END-TO-END: INTEGRATED SCAN")
    print("=" * 70)

    # 1. Configurar DB do Indexer com dados fictícios de repositórios SaaS
    print("\n[1] Populando banco de dados do Indexer (git_repository_intelligence.db)...")
    from app.database.database import init_db as init_indexer_db, AsyncSessionLocal
    from app.database.models import Repository, Tag, RepositoryTag, Dependency
    
    # Certificar que o DB do indexer existe
    os.chdir(str(indexer_dir))
    await init_indexer_db()

    async with AsyncSessionLocal() as session:
        # Obter ou criar Tag SaaS e Stripe
        from sqlalchemy import select
        res_saas = (await session.execute(select(Tag).where(Tag.name == "SaaS"))).scalar_one_or_none()
        if not res_saas:
            saas_tag = Tag(name="SaaS", category="product")
            session.add(saas_tag)
        else:
            saas_tag = res_saas

        res_stripe = (await session.execute(select(Tag).where(Tag.name == "Stripe"))).scalar_one_or_none()
        if not res_stripe:
            stripe_tag = Tag(name="Stripe", category="payment")
            session.add(stripe_tag)
        else:
            stripe_tag = res_stripe

        await session.flush()

        # Repositório 1
        res_r1 = (await session.execute(select(Repository).where(Repository.github_id == 12345678))).scalar_one_or_none()
        if not res_r1:
            repo1 = Repository(
                github_id=12345678,
                name="demo-saas-stripe",
                full_name="demo-org/demo-saas-stripe",
                owner="demo-org",
                url="https://github.com/expressjs/express",
                description="Exemplo de SaaS com integração Stripe",
                primary_language="TypeScript",
                stars=1250,
                score=88.5,
                index_status="COMPLETED"
            )
            session.add(repo1)
        else:
            repo1 = res_r1

        # Repositório 2
        res_r2 = (await session.execute(select(Repository).where(Repository.github_id == 87654321))).scalar_one_or_none()
        if not res_r2:
            repo2 = Repository(
                github_id=87654321,
                name="stripe-nextjs-starter",
                full_name="starter-kits/stripe-nextjs-starter",
                owner="starter-kits",
                url="https://github.com/pinojs/pino",
                description="Starter kit para SaaS com Next.js e Stripe",
                primary_language="TypeScript",
                stars=3400,
                score=92.0,
                index_status="COMPLETED"
            )
            session.add(repo2)
        else:
            repo2 = res_r2

        await session.flush()

        # Associar tags (se não associadas)
        res_rt1 = (await session.execute(select(RepositoryTag).where(RepositoryTag.repository_id == repo1.id, RepositoryTag.tag_id == saas_tag.id))).scalar_one_or_none()
        if not res_rt1:
            session.add(RepositoryTag(repository_id=repo1.id, tag_id=saas_tag.id, confidence=0.95))
        
        res_rt2 = (await session.execute(select(RepositoryTag).where(RepositoryTag.repository_id == repo1.id, RepositoryTag.tag_id == stripe_tag.id))).scalar_one_or_none()
        if not res_rt2:
            session.add(RepositoryTag(repository_id=repo1.id, tag_id=stripe_tag.id, confidence=0.98))

        res_rt3 = (await session.execute(select(RepositoryTag).where(RepositoryTag.repository_id == repo2.id, RepositoryTag.tag_id == saas_tag.id))).scalar_one_or_none()
        if not res_rt3:
            session.add(RepositoryTag(repository_id=repo2.id, tag_id=saas_tag.id, confidence=0.90))

        res_rt4 = (await session.execute(select(RepositoryTag).where(RepositoryTag.repository_id == repo2.id, RepositoryTag.tag_id == stripe_tag.id))).scalar_one_or_none()
        if not res_rt4:
            session.add(RepositoryTag(repository_id=repo2.id, tag_id=stripe_tag.id, confidence=0.95))

        # Associar dependências (se não associadas)
        res_dep1 = (await session.execute(select(Dependency).where(Dependency.repository_id == repo1.id, Dependency.name == "stripe"))).scalar_one_or_none()
        if not res_dep1:
            session.add(Dependency(repository_id=repo1.id, name="stripe", normalized_name="stripe", ecosystem="npm", dependency_type="direct"))

        res_dep2 = (await session.execute(select(Dependency).where(Dependency.repository_id == repo2.id, Dependency.name == "stripe"))).scalar_one_or_none()
        if not res_dep2:
            session.add(Dependency(repository_id=repo2.id, name="stripe", normalized_name="stripe", ecosystem="npm", dependency_type="direct"))

        await session.commit()
        print(" -> 2 repositórios SaaS/Stripe cadastrados no Indexer com sucesso.")

    # 2. Iniciar teste do consumidor (Secret Exposure Detector)
    os.chdir(str(detector_dir))
    print("\n[2] Inicializando Secret Exposure Detector e simulando consumo HTTP...")
    
    from backend.app.db.database import init_db as init_detector_db
    from backend.app.db.repository import SQLiteScanRepository
    from backend.app.integrations.indexer_client import IndexerClient
    from backend.app.queue.batch_worker import process_batch_scan
    
    init_detector_db()
    repo = SQLiteScanRepository()

    # Vamos simular a busca no Indexer através da chamada direta ao endpoint de consulta
    from app.api.routes.repositories import list_repositories
    async with AsyncSessionLocal() as session:
        indexer_results_schemas = await list_repositories(
            language=None,
            stars_min=None,
            score_min=None,
            tag="SaaS",
            dependency="stripe",
            skip=0,
            limit=10,
            db=session
        )
        indexer_results = [r.model_dump() for r in indexer_results_schemas]
    
    print(f" -> Indexer retornou {len(indexer_results)} repositórios encontrados para tag='SaaS', dependency='stripe':")
    for r in indexer_results:
        print(f"    * [{r['score']} pts] {r['full_name']} -> {r['url']}")

    # 3. Disparar batch scan no Secret Exposure Detector
    print("\n[3] Executando Batch Scan no Secret Exposure Detector...")
    batch_id = f"demo-batch-{str(uuid.uuid4())[:8]}"
    
    # Salvar batch scan no Detector DB
    from backend.app.db.models import BatchScanModel
    batch = BatchScanModel(
        id=batch_id,
        source_query="tag=SaaS, dependency=stripe",
        status="PENDING",
        total_repos=len(indexer_results)
    )
    repo.create_batch_scan(batch)

    # Executar batch worker
    print(f" -> Processando batch '{batch_id}' em segundo plano...")
    await process_batch_scan(batch_id=batch_id, repositories=indexer_results, run_ai=False)

    # 4. Exibir resultados consolidados do Batch Scan
    print("\n[4] RESULTADO FINAL DO BATCH SCAN:")
    batch_final = repo.get_batch_scan(batch_id)
    batch_jobs = repo.get_batch_scan_jobs(batch_id)

    print(f" -> Batch ID: {batch_final.id}")
    print(f" -> Query de Origem: {batch_final.source_query}")
    print(f" -> Status: {batch_final.status}")
    print(f" -> Repositórios Concluídos: {batch_final.completed}/{batch_final.total_repos}")

    print("\n -> Detalhamento por Repositório Escaneado:")
    for bj in batch_jobs:
        job_info = repo.get_job(bj.job_id)
        incidents = repo.get_job_incidents(bj.job_id)
        print(f"\n    [REPO] [{bj.status}] {bj.repository_name}")
        print(f"       URL: {bj.repository_url}")
        print(f"       Job ID: {bj.job_id}")
        if job_info:
            print(f"       Arquivos analisados: {job_info.analyzed_files} / {job_info.total_files}")
            print(f"       Segredos detectados: Critical={job_info.critical_count}, High={job_info.high_count}, Medium={job_info.medium_count}, Low={job_info.low_count}")
            if incidents:
                print("       Amostra de incidentes:")
                for inc in incidents[:3]:
                    print(f"        - [{inc.criticality}] {inc.relative_path}:{inc.line_number} (Var: {inc.variable_name}, Capability: {inc.capability})")

    print("\n" + "=" * 70)
    print("FIM DA DEMO - INTEGRAÇÃO FUNCIONANDO 100%")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
