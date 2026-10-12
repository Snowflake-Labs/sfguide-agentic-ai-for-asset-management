# Copyright (c) 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Weekly refresh orchestration.

One entry point, `run()`, sequencing the whole cycle. The ordering is not
arbitrary:

  1. watermark          what week are we processing
  2. stream health      recover anything stale before reading it
  3. prices             everything downstream keys off FACT_STOCK_PRICES
  4. structured         transactions, positions, factor exposures
  5. recommendations    needs the new prices; must precede cadence, because
                        `rating_threshold_crossed` is a cadence trigger
  6. cadence            which document types owe a vintage this week
  7. documents          generate through the existing hydration engine
  8. upload             PUT to the PDF stages, then ALTER STAGE REFRESH
  9. pipelines          drive parse and chunk explicitly, then wait
 10. watermark          advance only after everything above succeeded

Every step is independently idempotent, so a rerun after a partial failure
resumes rather than duplicating. The watermark is advanced last and only on
success, so a failed run is retried from the same week rather than skipping it.

Step 9 drives the pipeline tasks explicitly instead of relying on their
schedules. That gives deterministic ordering, and it does not depend on those
tasks having been left resumed - which they are not after a build.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from snowflake.snowpark import Session

import config
from utils.logging import (
    log_detail, log_error, log_info, log_step, log_substep, log_warning,
)
from utils.snowflake import get_max_price_date, reset_max_price_date

REFRESH_KEY = 'weekly_refresh'

# Document types the weekly cycle can generate. Real-sourced types are excluded:
# they arrive through the marketplace, not the hydration engine.
_GENERATABLE_DOC_TYPES = [
    'broker_research', 'internal_research', 'investment_memo',
    'press_releases', 'ngo_reports', 'engagement_notes', 'macro_events',
    'reconciliation_notes', 'custodian_reports', 'report_templates',
    'strategy_documents', 'policy_docs', 'philosophy_docs', 'methodology_docs',
    'ops_procedures', 'sales_templates', 'ssi_documents', 'ips',
]


def _as_date(value: Union[str, date, datetime, None]) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d').date()
    return None


def run(
    session: Session,
    as_of: Union[str, date, None] = None,
    dry_run: bool = False,
    skip_pipelines: bool = False,
) -> Dict[str, Any]:
    """Execute one weekly refresh cycle.

    Args:
        session: Snowpark session.
        as_of: Target date. Defaults to the latest available price date, so the
            refresh follows the data rather than the wall clock - the demo's
            market data ends at a fixed point and using today's date would
            produce an empty window.
        dry_run: Report what would happen without writing anything.
        skip_pipelines: Skip document upload and parse, the Marketplace corpus
            pipelines, and morning briefing generation. Useful when iterating on the
            structured half, since PDF parsing, transcript speaker mapping and the
            per-portfolio agent calls dominate the runtime.

    Returns a summary dict. Raises on failure, having left the watermark
    unadvanced so the same week is retried.
    """
    from data import cadence, incremental

    log_step("Weekly refresh")
    summary: Dict[str, Any] = {'dry_run': dry_run}

    # --- 1. Watermark and target week ------------------------------------
    cadence.ensure_tables(session)
    watermark = cadence.get_watermark(session, REFRESH_KEY)
    target = _as_date(as_of) or incremental.get_source_max_price_date(session)
    if target is None:
        raise RuntimeError(
            "Cannot determine a target date: the Marketplace price share is empty."
        )
    if get_max_price_date(session) is None:
        raise RuntimeError(
            "FACT_STOCK_PRICES is empty. Run the full build first."
        )
    summary['watermark_before'] = str(watermark) if watermark else None
    summary['target_date'] = str(target)

    if watermark and watermark >= target:
        log_info(
            f"Already refreshed through {watermark}, and no data beyond it "
            f"({target}). Nothing to do."
        )
        summary['status'] = 'UP_TO_DATE'
        return summary

    # A first run has no watermark, so bound the window rather than reprocessing
    # the entire history.
    window_start = (watermark + timedelta(days=1)) if watermark else (target - timedelta(days=7))
    summary['window'] = [str(window_start), str(target)]
    log_detail(f"  Processing {window_start} .. {target}")

    if dry_run:
        return _dry_run_report(session, target, summary)

    try:
        # --- 1. Prices ---------------------------------------------------
        log_substep("Appending Marketplace prices...")
        summary['prices_added'] = incremental.append_stock_prices(
            session, window_start, target
        )
        reset_max_price_date()

        # --- 2. Structured -----------------------------------------------
        summary['structured'] = incremental.refresh_structured(session, target)

        # --- 3. Private markets -----------------------------------------
        # PE and private credit used to be rebuilt only on a full build, which
        # made them the one part of the demo that never moved. Advance them here
        # so a presenter's "this refreshes itself" holds for both halves.
        try:
            from data import private_markets
            summary['private_markets'] = private_markets.refresh_private_markets(
                session, target
            )
        except Exception as exc:
            log_warning(f"  Private markets refresh failed: {str(exc)[:200]}")
            summary['private_markets'] = {'error': str(exc)[:200]}

        # --- 3b. ML rescoring ---------------------------------------------
        # Rescore regime and credit PD with the PRODUCTION model versions against
        # this week's prices and borrower financials. Never retrains: a new model
        # version is a build decision, not a weekly side effect.
        try:
            from ai.tools.ml_models import score_ml_models
            summary['ml_rescore'] = score_ml_models(session)
        except Exception as exc:
            log_warning(f"  ML rescoring failed: {str(exc)[:200]}")
            summary['ml_rescore'] = {'error': str(exc)[:200]}

        # --- 4. Marketplace corpora --------------------------------------
        # Transcripts and SEC filing text used to be loaded only by the full
        # build, so both corpora were frozen at build time while every other part
        # of the demo moved. A presenter asking for the latest earnings call got
        # whatever was current on build day.
        try:
            summary['marketplace_corpora'] = _refresh_marketplace_corpora(
                session, skip_pipelines=skip_pipelines
            )
        except Exception as exc:
            log_warning(f"  Marketplace corpora refresh failed: {str(exc)[:200]}")
            summary['marketplace_corpora'] = {'error': str(exc)[:200]}

        # --- 5. Recommendations ------------------------------------------
        # Before cadence: rating_threshold_crossed is a cadence trigger, so the
        # new vintage has to exist before cadence can see the crossing.
        log_substep("Refreshing recommendations...")
        from data import market_data, recommendations
        recommendations.ensure_vintage(session, target)
        market_data.build_estimate_data(session)

        # --- 5b. Coverage backfill ------------------------------------------
        try:
            backfill = backfill_coverage_gaps(session, target)
        except Exception as exc:
            log_warning(f"  Coverage backfill failed: {str(exc)[:200]}")
            backfill = {'failures': {'coverage_backfill': str(exc)[:200]}}
        summary['coverage_backfill'] = backfill

        # --- 6. Cadence ---------------------------------------------------
        due = _evaluate_due_documents(session, target, cadence)
        summary['documents_due'] = {k: len(v) for k, v in due.items()}

        # --- 7. Documents -------------------------------------------------
        generated, doc_failures = _generate_documents(session, due, target)
        for doc_type, count in backfill.get('generated', {}).items():
            generated[doc_type] = generated.get(doc_type, 0) + count
        backfill_failures = backfill.get('failures', {})
        summary['documents_generated'] = generated
        if doc_failures:
            summary['documents_failed'] = doc_failures

        # Record what was published. Without this the ledger never grows, so
        # min_days_between has nothing to anti-join against and an event-driven
        # type would re-trigger every week on the same entity.
        summary['vintages_logged'] = _log_generated_vintages(
            session, due, generated, target, cadence
        )

        # --- 8. Upload and document pipelines -----------------------------------
        pipeline_outcomes: Dict[str, Any] = {}
        if skip_pipelines:
            log_detail("  Skipping upload and parse (skip_pipelines)")
            pipeline_outcomes = {'skipped': True}
        elif any(generated.values()):
            # any(values), not just a non-empty dict: if every due type failed,
            # `generated` is {'x': 0, ...} - truthy, but there is nothing to
            # upload, and running the pipelines would report a misleading
            # NO_NEW_FILES success.
            pipeline_outcomes = _run_document_pipelines(session)
        else:
            log_detail("  No new documents, skipping upload and parse")
        summary['pipelines'] = pipeline_outcomes

        # --- 8b. ESG controversies -----------------------------------------
        # Derived from the parsed NGO reports in PDF_EXTERNAL_CORPUS, so it must
        # run after the parse or this week's reports never reach
        # SAM_PORTFOLIO_VIEW. A failure is recorded as a failed pipeline so the
        # run reports PARTIAL; the watermark still advances because the next
        # run rebuilds the table from the full corpus.
        try:
            from data.structured import build_fact_esg_controversy
            summary['esg_controversies'] = build_fact_esg_controversy(session)
        except Exception as exc:
            log_warning(f"  FACT_ESG_CONTROVERSY rebuild failed: {str(exc)[:200]}")
            summary['esg_controversies'] = {'error': str(exc)[:200]}
            pipeline_outcomes['esg_controversy'] = 'FAILED'

        # --- 9. Morning briefings ------------------------------------------
        # Last of the content steps, so the briefings are written against this week's
        # prices, recommendations, documents and corpora rather than last week's. They
        # were previously generated only by the full build and expired after a day, so
        # a demo given any later than build day had no live briefings at all.
        #
        # Skipped with skip_pipelines: this is a DATA_AGENT_RUN per portfolio and fund,
        # which is the most expensive step in the refresh.
        if skip_pipelines:
            log_detail("  Skipping morning briefings (skip_pipelines)")
            summary['briefings'] = 'SKIPPED'
        else:
            try:
                from ai.proactive_insights import seed_morning_briefings
                log_substep("Regenerating morning briefings...")
                seed_morning_briefings(session)
                summary['briefings'] = 'REGENERATED'
            except Exception as exc:
                # Non-fatal: stale briefings are a worse demo than fresh ones, but not a
                # reason to hold the watermark and redo the whole week.
                log_warning(f"  Morning briefing generation failed: {str(exc)[:200]}")
                summary['briefings'] = {'error': str(exc)[:200]}

        # --- 10. Retention -------------------------------------------------
        # Proactive insights and alerts are append-only logs written by daily tasks, so
        # without this they grow for as long as the demo lives. Runs after generation so
        # this week's briefings are already in place before anything is removed.
        # Non-fatal: failing to prune is untidy, not a reason to retry the week.
        try:
            from ai.proactive_insights import prune_expired_insights
            summary['retention'] = prune_expired_insights(session)
        except Exception as exc:
            log_warning(f"  Retention prune failed: {str(exc)[:200]}")
            summary['retention'] = {'error': str(exc)[:200]}

        # --- 11. Watermark -------------------------------------------------
        # A failed pipeline means documents exist on the stage but never reached
        # the corpus, so the agent cannot retrieve them. Report that as PARTIAL
        # rather than SUCCESS - reporting success here is precisely the silent
        # degradation this refresh is meant to avoid. The watermark still
        # advances, because the structured half did complete and the parse is
        # recoverable on the next run once the stream has data.
        failed_pipelines = [
            k for k, v in pipeline_outcomes.items() if v == 'FAILED'
        ]
        status_text = 'PARTIAL' if (failed_pipelines or doc_failures or backfill_failures) else 'SUCCESS'
        if doc_failures:
            # Documents were due and did not get written. Reporting SUCCESS here
            # would let the demo quietly stop producing new research while every
            # signal said the refresh was healthy.
            log_warning(
                f"  {len(doc_failures)} document type(s) failed to generate: "
                + ", ".join(f"{k} ({v})" for k, v in doc_failures.items())
            )
        if failed_pipelines:
            log_warning(
                f"  Refresh completed but {len(failed_pipelines)} pipeline(s) "
                f"failed: {', '.join(failed_pipelines)}. Documents were generated "
                "but are not yet searchable."
            )
        # Whether to advance depends on WHICH half failed, and the two are not
        # equivalent:
        #
        #   pipeline failure  -> the PDFs are already on the stage. The next run's
        #       ALTER STAGE REFRESH and stream read pick them up, so advancing is
        #       safe and avoids regenerating everything.
        #
        #   generation failure -> the documents were never written, so there is
        #       nothing for a later parse to recover. Advancing would move past
        #       the week permanently and silently lose that week's research - a
        #       broken template would skip a week every week while the task kept
        #       reporting. Hold the watermark so the same week is retried once the
        #       cause is fixed.
        if doc_failures:
            effective_target = watermark or window_start
            log_warning(
                f"  Holding the watermark at {effective_target}: documents for "
                f"{target} were not generated, so this week will be retried "
                "rather than skipped."
            )
        else:
            effective_target = target
        cadence.set_watermark(
            session, REFRESH_KEY, effective_target, status=status_text
        )
        summary['watermark_after'] = str(effective_target)
        summary['watermark_advanced'] = effective_target == target
        summary['status'] = status_text
        log_info(f"Weekly refresh {status_text.lower()} through {target}")
        return summary

    except Exception as exc:
        # Record the failure but leave LAST_DATE where it was, so the next run
        # retries this week instead of skipping it.
        try:
            cadence.set_watermark(
                session, REFRESH_KEY, watermark or window_start, status=f'FAILED: {exc}'[:200]
            )
        except Exception:
            log_warning("  Could not record failure state in REFRESH_STATE")
        log_error(f"Weekly refresh failed: {exc}")
        raise


def run_catch_up(
    session: Session,
    max_weeks: int = 12,
    skip_pipelines: bool = False,
) -> List[Dict[str, Any]]:
    """Advance one week at a time until caught up with the available data.

    A demo handed to other people sits idle for weeks, so the watermark can fall
    well behind. Jumping straight to the latest date in one run would collapse
    those weeks into a single vintage and lose the week-by-week history the demo
    is meant to show - rating changes, document cadence, position drift. So each
    iteration processes exactly one week and advances the watermark, producing the
    same result as if the schedule had run all along.

    Bounded by max_weeks so an account idle for a year cannot run unbounded.
    """
    from data import cadence

    cadence.ensure_tables(session)
    latest = get_max_price_date(session)
    if latest is None:
        raise RuntimeError("FACT_STOCK_PRICES is empty - run the full build first")

    results: List[Dict[str, Any]] = []
    for iteration in range(max_weeks):
        watermark = cadence.get_watermark(session, REFRESH_KEY)
        if watermark is None:
            # No history: process the most recent week and let subsequent runs
            # move forward normally.
            target = latest
        elif watermark >= latest:
            log_info(f"Caught up: watermark {watermark} is current with {latest}")
            break
        else:
            target = min(watermark + timedelta(days=7), latest)

        log_info(f"Catch-up {iteration + 1}/{max_weeks}: targeting {target}")
        result = run(session, as_of=target, skip_pipelines=skip_pipelines)
        results.append(result)
        if result.get('status') == 'UP_TO_DATE':
            break
    else:
        log_warning(
            f"  Stopped after {max_weeks} weeks without catching up. Run again to "
            "continue."
        )

    return results


def _log_generated_vintages(
    session: Session,
    due: Dict[str, List[Dict[str, Any]]],
    generated: Dict[str, int],
    target: date,
    cadence_module: Any,
) -> int:
    """Write one ledger row per published document.

    Carries the rating snapshot for research types, so DOCUMENT_VINTAGE_LOG
    doubles as the rating history for what was actually published rather than
    only what was computed.
    """
    from utils.snowflake import prefetch_recommendations

    database = config.DATABASE['name']
    total = 0

    for doc_type, entities in due.items():
        if not generated.get(doc_type):
            continue

        rec_by_security: Dict[Any, Dict[str, Any]] = {}
        if doc_type in ('broker_research', 'internal_research', 'investment_memo'):
            security_ids = [e['id'] for e in entities if isinstance(e.get('id'), int)]
            prefetched = prefetch_recommendations(session, database, security_ids)
            # Newest vintage first, so the first row is the current view.
            rec_by_security = {
                sid: rows[0] for sid, rows in prefetched.items() if rows
            }

        records = []
        for entity in entities:
            rec = rec_by_security.get(entity['id']) or {}
            records.append({
                'entity_id': entity['id'],
                'vintage_date': target,
                'document_id': None,
                'trigger_reason': entity.get('trigger_reason'),
                'rating': rec.get('RATING'),
                'prior_rating': rec.get('PRIORRATING'),
                'rating_action': rec.get('RATINGACTION'),
                'price_target': rec.get('PRICETARGET'),
                'close_price': rec.get('CLOSEPRICE'),
                'upside_pct': rec.get('UPSIDEPCT'),
            })
        total += cadence_module.log_vintages(session, doc_type, records)

    log_detail(f"  Logged {total} vintage(s) to DOCUMENT_VINTAGE_LOG")
    return total


_RECOMMENDATION_BACKFILL_KEY = 'recommendation_backfill'


def _coverage_gaps_sql(starter_pack: List[str]) -> str:
    """Universe names lacking a corpus document of each starter-pack type that
    has not already been generated (logged) for them."""
    from core import hydration_engine
    from utils.demo_helpers import get_demo_company_priority_sql

    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    branches = []
    for doc_type in starter_pack:
        doc_cfg = config.DOCUMENT_TYPES[doc_type]
        entity_col = 'u.SecurityID' if doc_cfg['linkage_level'] == 'security' else 'u.IssuerID'
        branches.append(f"""
            SELECT u.Ticker, u.SecurityID, u.IssuerID, '{doc_type}' AS DocType,
                   {entity_col} AS EntityID
            FROM universe u
            WHERE NOT EXISTS (
                SELECT 1 FROM {database}.{curated}.{doc_cfg['corpus_name']} c
                WHERE c.TICKER = u.Ticker AND c.DOCUMENT_TYPE = '{doc_type}'
            )
              AND NOT EXISTS (
                SELECT 1 FROM {database}.RAW.DOCUMENT_VINTAGE_LOG v
                WHERE v.DOC_TYPE = '{doc_type}' AND v.ENTITY_ID = TO_VARCHAR({entity_col})
            )""")
    return f"""
        WITH universe AS ({hydration_engine.get_coverage_universe_sql()}),
        gaps AS ({' UNION ALL '.join(branches)})
        SELECT g.Ticker, g.SecurityID, g.IssuerID, g.DocType, g.EntityID,
               EXISTS (
                   SELECT 1 FROM {database}.{curated}.FACT_RECOMMENDATION r
                   WHERE r.SecurityID = g.SecurityID
               ) AS HasRecommendation,
               EXISTS (
                   SELECT 1 FROM {database}.RAW.DOCUMENT_VINTAGE_LOG v
                   WHERE v.DOC_TYPE = '{_RECOMMENDATION_BACKFILL_KEY}'
                     AND v.ENTITY_ID = TO_VARCHAR(g.SecurityID)
               ) AS RecommendationAttempted
        FROM gaps g
        JOIN {database}.{curated}.DIM_SECURITY s ON s.SecurityID = g.SecurityID
        ORDER BY CASE {get_demo_company_priority_sql()} ELSE 10 END, g.Ticker, g.DocType
    """


def _backfill_recommendations(
    session: Session, security_ids: List[int], target: date, cadence_module: Any,
) -> List[int]:
    """Re-run the grounded vintage generator across the existing vintages so any
    newly valuable name gains a history, then record the attempt so names the
    generator cannot value are not retried every week. Returns the securities
    that now have a recommendation."""
    from data import recommendations

    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    vintages = [
        r['VINTAGEDATE'] for r in session.sql(f"""
            SELECT DISTINCT VintageDate FROM {database}.{curated}.FACT_RECOMMENDATION
            ORDER BY VintageDate
        """).collect()
    ]
    log_detail(
        f"  Backfilling recommendations across {len(vintages)} vintage(s) "
        f"for {len(security_ids)} uncovered name(s)"
    )
    for vintage in vintages:
        recommendations.build_fact_recommendation(session, vintage, append=True)
    recommendations.apply_rating_actions(session)

    covered = [
        r['SECURITYID'] for r in session.sql(f"""
            SELECT DISTINCT SecurityID FROM {database}.{curated}.FACT_RECOMMENDATION
            WHERE SecurityID IN ({', '.join(str(int(s)) for s in security_ids)})
        """).collect()
    ]
    cadence_module.log_vintages(session, _RECOMMENDATION_BACKFILL_KEY, [
        {
            'entity_id': sid,
            'vintage_date': target,
            'trigger_reason': 'coverage_backfill' if sid in covered else 'coverage_backfill_unvaluable',
        }
        for sid in security_ids
    ])
    return covered


def backfill_coverage_gaps(
    session: Session, target: date, dry_run: bool = False,
) -> Dict[str, Any]:
    """Give every coverage-universe name a starter pack of documents.

    A name that enters a scenario portfolio's top N has no research, press,
    NGO or engagement documents, because the build only covered the names in
    the universe at the time. For each such name: create a recommendation
    history if it has none (research quotes a grounded rating), generate the
    starter pack at this vintage through the normal hydrate path, and log it in
    DOCUMENT_VINTAGE_LOG so the regular cadence takes over.

    Idempotent: a logged vintage removes the gap even before the parse lands in
    the corpus, and a recommendation attempt is logged once per name. Bounded by
    coverage.backfill_max_names. Nothing is deleted when a name leaves the top N.
    """
    from core import hydration_engine
    from data import cadence

    settings = hydration_engine.get_coverage_settings()
    starter_pack = [t for t in settings['starter_pack'] if t in config.DOCUMENT_TYPES]
    log_substep("Checking coverage universe for document gaps...")

    rows = session.sql(_coverage_gaps_sql(starter_pack)).collect()
    tickers: List[str] = []
    for r in rows:
        if r['TICKER'] not in tickers:
            tickers.append(r['TICKER'])
    selected = set(tickers[:settings['backfill_max_names']])
    rows = [r for r in rows if r['TICKER'] in selected]

    out: Dict[str, Any] = {
        'gap_names': sorted(selected),
        'deferred_names': sorted(set(tickers) - selected),
        'gaps': sorted(f"{r['TICKER']}:{r['DOCTYPE']}" for r in rows),
        'generated': {},
        'failures': {},
        'unvaluable': [],
    }
    if not rows:
        log_detail("  No coverage gaps")
        return out

    needs_rec = sorted({
        r['SECURITYID'] for r in rows
        if not r['HASRECOMMENDATION'] and not r['RECOMMENDATIONATTEMPTED']
    })
    out['recommendations_needed'] = sorted({
        r['TICKER'] for r in rows if r['SECURITYID'] in needs_rec
    })
    if dry_run:
        log_detail(
            f"  {len(rows)} gap(s) across {len(selected)} name(s); "
            f"{len(needs_rec)} need a recommendation history"
        )
        return out

    with_rec = {r['SECURITYID'] for r in rows if r['HASRECOMMENDATION']}
    if needs_rec:
        with_rec.update(_backfill_recommendations(session, needs_rec, target, cadence))

    hydration_engine._anchor_date = target
    for doc_type in starter_pack:
        type_rows = [r for r in rows if r['DOCTYPE'] == doc_type]
        if doc_type in ('broker_research', 'internal_research', 'investment_memo'):
            skipped = sorted({r['TICKER'] for r in type_rows if r['SECURITYID'] not in with_rec})
            out['unvaluable'] = sorted(set(out['unvaluable']) | set(skipped))
            type_rows = [r for r in type_rows if r['SECURITYID'] in with_rec]
        entities = [
            {'id': r['ENTITYID'], 'trigger_reason': 'coverage_backfill'}
            for r in type_rows
        ]
        if not entities:
            continue
        try:
            count = hydration_engine.hydrate_documents(
                session, doc_type, test_mode=False, entities=entities
            )
        except Exception as exc:
            log_warning(f"  coverage backfill {doc_type}: generation failed ({exc})")
            out['failures'][doc_type] = str(exc)[:200]
            continue
        if not count:
            out['failures'][doc_type] = 'produced no documents'
            continue
        out['generated'][doc_type] = count
        _log_generated_vintages(session, {doc_type: entities}, {doc_type: count}, target, cadence)

    if out['unvaluable']:
        log_warning(
            "  No grounded recommendation possible, research skipped for: "
            + ", ".join(out['unvaluable'])
        )
    log_detail(
        f"  Coverage backfill: {sum(out['generated'].values())} document(s) "
        f"for {len(selected)} name(s)"
    )
    return out


def _evaluate_due_documents(
    session: Session, target: date, cadence_module: Any,
) -> Dict[str, List[Dict[str, Any]]]:
    """Ask the cadence registry which entities owe a document this week."""
    from core import hydration_engine

    log_substep("Evaluating document cadence...")
    due: Dict[str, List[Dict[str, Any]]] = {}

    for doc_type in _GENERATABLE_DOC_TYPES:
        if doc_type not in config.DOCUMENT_TYPES:
            continue
        try:
            entities = hydration_engine.get_entities_for_doc_type(
                session, doc_type, test_mode=False
            )
        except Exception as exc:
            log_warning(f"  {doc_type}: could not resolve entities ({exc})")
            continue
        if not entities:
            continue

        decisions = cadence_module.evaluate_cadence(session, doc_type, entities, target)
        due_entities = [
            {**e, 'trigger_reason': decisions[e['id']][2]}
            for e in entities
            if decisions.get(e['id'], (False,))[0]
        ]
        if due_entities:
            due[doc_type] = due_entities

    total = sum(len(v) for v in due.values())
    log_detail(f"  {total} document(s) due across {len(due)} type(s)")
    return due


def _generate_documents(
    session: Session, due: Dict[str, List[Dict[str, Any]]], target: date,
) -> Tuple[Dict[str, int], Dict[str, str]]:
    """Generate the due documents through the existing hydration engine.

    Reuses hydrate_documents rather than reimplementing generation, so weekly
    documents are produced by exactly the same code path - and therefore the same
    grounding, stance and determinism - as the initial build.
    """
    from core import hydration_engine

    if not due:
        return {}, {}

    log_substep("Generating due documents...")
    hydration_engine._anchor_date = target

    generated: Dict[str, int] = {}
    failures: Dict[str, str] = {}
    for doc_type, due_entities in due.items():
        try:
            # Pass the due entities explicitly. Without this, hydrate_documents
            # regenerates the whole coverage set, so one triggered stock would
            # give every stock a new note - the weekly churn cadence exists to
            # prevent.
            count = hydration_engine.hydrate_documents(
                session, doc_type, test_mode=False, entities=due_entities
            )
            generated[doc_type] = count
            log_detail(f"  {doc_type}: {count} document(s)")
        except Exception as exc:
            # One failing document type must not abandon the rest of the cycle,
            # but it must be visible rather than swallowed. Returning the reason
            # is what lets run() report PARTIAL instead of a false SUCCESS.
            log_warning(f"  {doc_type}: generation failed ({exc})")
            generated[doc_type] = 0
            failures[doc_type] = str(exc)

    # A due document type that produced nothing without raising is also a
    # failure - silently generating zero is the outcome we must never call
    # success.
    for doc_type, count in generated.items():
        if count == 0 and doc_type not in failures:
            failures[doc_type] = 'produced no documents'
            log_warning(f"  {doc_type}: due but produced no documents")

    return generated, failures


def _refresh_marketplace_corpora(
    session: Session, skip_pipelines: bool = False,
) -> Dict[str, Any]:
    """Load new transcripts and SEC filing text, then drive their corpus pipelines.

    Both loaders are MERGEs keyed on the document, so calling them here is safe even
    though the full build calls them too - an already-loaded document is skipped
    rather than duplicated. That is the whole reason the initial-build loaders can be
    reused for the weekly refresh instead of maintaining a second code path.

    Neither loader is given a `since` window, deliberately. It would narrow the source
    scan, but it would also open a gap: on the first refresh after a build there is no
    watermark, so the window would be the last seven days, and anything published
    between build day and that window would never be picked up. The MERGE makes a full
    scan correct rather than merely cheap, and for this universe it costs seconds.

    Returns a per-corpus summary so a frozen corpus shows up in the refresh output
    rather than being silently skipped.
    """
    from data import pipelines, transcripts

    log_substep("Refreshing Marketplace corpora (transcripts, SEC filings)...")

    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    out: Dict[str, Any] = {}

    # --- Load the raw tables -------------------------------------------------
    try:
        out['transcripts_added'] = transcripts.load_raw_table(session)
    except Exception as exc:
        log_warning(f"  Transcript load failed: {str(exc)[:200]}")
        out['transcripts_added'] = 0
        out['transcripts_error'] = str(exc)[:200]

    try:
        out['sec_filings_added'] = pipelines.load_sec_filings_raw(session)
    except Exception as exc:
        log_warning(f"  SEC filing load failed: {str(exc)[:200]}")
        out['sec_filings_added'] = 0
        out['sec_filings_error'] = str(exc)[:200]

    if skip_pipelines:
        log_detail("  Skipping corpus pipelines (skip_pipelines)")
        out['pipelines'] = 'SKIPPED'
        return out

    # --- Drive the corpus pipelines -----------------------------------------
    # Keyed by root task, with every stream that feeds the graph. The transcripts
    # graph has two consumers reading two separate streams off the same table, so
    # checking only one of them would skip a graph that still has work to do.
    graphs = {
        'transcripts': {
            'root': f"{database}.{raw_schema}.TRANSCRIPTS_PIPELINE_ROOT",
            'streams': [
                f"{database}.{raw_schema}.TRANSCRIPTS_SPEAKER_STREAM",
                f"{database}.{raw_schema}.TRANSCRIPTS_CORPUS_STREAM",
            ],
        },
        'sec_filings': {
            'root': f"{database}.{raw_schema}.SEC_FILINGS_PIPELINE_ROOT",
            'streams': [f"{database}.{raw_schema}.SEC_FILINGS_RAW_STREAM"],
        },
    }

    for key, graph in graphs.items():
        has_data = False
        for stream in graph['streams']:
            try:
                if session.sql(
                    f"SELECT SYSTEM$STREAM_HAS_DATA('{stream}') AS h"
                ).collect()[0]['H']:
                    has_data = True
                    break
            except Exception as exc:
                log_warning(f"  {key}: could not check {stream} ({exc})")
                # Assume there is work rather than silently skipping the corpus.
                has_data = True
                break

        if not has_data:
            log_detail(f"  {key}: corpus already current")
            out[f'{key}_pipeline'] = 'NO_NEW_DATA'
            continue

        out[f'{key}_pipeline'] = _drive_marketplace_graph(
            session, key, graph['root'], graph['streams']
        )

    return out


def _drive_marketplace_graph(
    session: Session, key: str, root: str, streams: list,
) -> str:
    """Run one marketplace corpus graph to completion, then leave it suspended.

    These graphs carry their own `SCHEDULE = '5 MINUTE'` with a
    `WHEN SYSTEM$STREAM_HAS_DATA` guard, which makes driving them manually delicate in
    exactly the way the PDF driver above documents. Resuming the graph and then calling
    EXECUTE TASK loses a race: a scheduled run fires first, consumes the stream, and the
    manual run is then SKIPPED by its WHEN clause - and a skipped root does not run its
    children. Observed directly here, with the scheduled run completing the whole graph
    while the manual run's wait timed out after an hour reporting 0 of 3 tasks done.

    So the root is SUSPENDED first and the children resumed. EXECUTE TASK on a suspended
    root still runs the entire graph, which removes the race without preventing the run.
    Suspend order matters: Snowflake refuses to suspend a child while the root is
    resumed, so it is root first, then children, and the reverse on the way back.

    Completion is judged by the streams draining rather than by task state, because a
    concurrent scheduled run can leave the state looking like a failure after the work
    has actually finished.
    """
    import time

    from data import pipelines

    children = _graph_children(session, root)

    try:
        session.sql(f"ALTER TASK {root} SUSPEND").collect()
        for child in children:
            session.sql(f"ALTER TASK {child} RESUME").collect()
    except Exception as exc:
        log_warning(f"  {key}: could not prepare task graph ({exc})")

    try:
        try:
            session.sql(f"EXECUTE TASK {root}").collect()
        except Exception as exc:
            log_warning(f"  {key}: could not execute root task ({exc})")
            return 'FAILED'

        # Poll until every stream feeding the graph has drained.
        deadline = time.time() + 3600
        drained = False
        while time.time() < deadline:
            time.sleep(15)
            try:
                drained = all(
                    not session.sql(
                        f"SELECT SYSTEM$STREAM_HAS_DATA('{s}') AS h"
                    ).collect()[0]['H']
                    for s in streams
                )
            except Exception as exc:
                log_warning(f"  {key}: could not check streams while waiting ({exc})")
                break
            if drained:
                break

        if not drained:
            log_warning(
                f"  {key}: new rows are in RAW but have not reached the corpus - "
                "they are not yet searchable"
            )
            return 'FAILED'

        # The streams drain when the first consumer reads them, which is before the
        # last task in the graph has written the corpus. Wait for the leaf to settle.
        leaf = children[-1] if children else root
        for _ in range(60):
            rows = session.sql(f"""
                SELECT STATE FROM TABLE({config.DATABASE['name']}.INFORMATION_SCHEMA.TASK_HISTORY(
                    TASK_NAME => '{leaf.split('.')[-1]}',
                    SCHEDULED_TIME_RANGE_START => DATEADD('minute', -75, CURRENT_TIMESTAMP())))
                ORDER BY SCHEDULED_TIME DESC LIMIT 1
            """).collect()
            if rows and rows[0]['STATE'] in ('SUCCEEDED', 'FAILED', 'SKIPPED'):
                break
            time.sleep(15)

        return 'SUCCESS'

    except Exception as exc:
        log_warning(f"  {key}: pipeline error ({str(exc)[:200]})")
        return 'FAILED'
    finally:
        # Leave the whole graph suspended: these tasks are scheduled, and a resumed
        # graph competes with the next run for the same stream.
        try:
            pipelines.suspend_task_graph(session, root)
        except Exception:
            log_warning(f"  {key}: could not suspend task graph afterwards")


def _graph_children(session: Session, root: str) -> list:
    """Return the non-root tasks in a graph, ordered root-first by dependency depth.

    Discovered from TASK_DEPENDENTS rather than hardcoded, so the transcripts graph
    (speaker mapping then corpus build) and the single-child SEC graph are handled by
    the same code, and adding a stage to either does not silently leave it suspended.
    """
    database = root.split('.')[0]
    try:
        rows = session.sql(f"""
            SELECT NAME FROM TABLE({database}.INFORMATION_SCHEMA.TASK_DEPENDENTS(
                TASK_NAME => '{root}', RECURSIVE => TRUE))
        """).collect()
    except Exception as exc:
        log_warning(f"  Could not resolve children of {root} ({exc})")
        return []

    root_name = root.split('.')[-1]
    prefix = '.'.join(root.split('.')[:-1])
    return [
        f"{prefix}.{r['NAME']}" for r in rows if r['NAME'] != root_name
    ]


def _run_document_pipelines(session: Session) -> Dict[str, Any]:
    """Upload the new PDFs and drive the parse and chunk tasks to completion.

    Returns a per-pipeline outcome so the caller can surface failures instead of
    reporting overall success while the corpus never updated.
    """
    from data import pipelines

    log_substep("Uploading documents and running pipelines...")
    uploaded, failed = pipelines.upload_pdfs_to_stages(session)
    log_detail(f"  Uploaded {uploaded} PDF(s) ({failed} failed)")
    pipelines.refresh_pdf_stages(session)

    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    outcomes: Dict[str, Any] = {'uploaded': uploaded, 'upload_failed': failed}

    for key, pipeline in pipelines.PDF_PIPELINES.items():
        root = f"{database}.{raw_schema}.{pipeline['parse_task']}"
        stream = f"{database}.{raw_schema}.{pipeline['stream_name']}"

        # Only run the graph when the directory stream actually has new files.
        # Documents are deterministic, so an unchanged document re-uploads to the
        # same path with the same ETAG and the stream sees nothing. The root task
        # is then SKIPPED by its WHEN clause, and because a skipped root does not
        # run its children, wait_for_task_completion reports a timeout that looks
        # like a failure but is really "nothing to do".
        try:
            has_data = session.sql(
                f"SELECT SYSTEM$STREAM_HAS_DATA('{stream}') AS h"
            ).collect()[0]['H']
        except Exception as exc:
            log_warning(f"  {key}: could not check stream ({exc})")
            has_data = True

        if not has_data:
            log_detail(f"  {key}: no new files to parse")
            outcomes[key] = 'NO_NEW_FILES'
            continue

        chunk = f"{database}.{raw_schema}.{pipeline['chunk_task']}"
        outcomes[key] = _drive_pipeline_graph(session, key, root, chunk, stream)

    return outcomes


def _drive_pipeline_graph(
    session: Session, key: str, root: str, chunk: str, stream: str,
) -> str:
    """Run one parse/chunk graph to completion and verify by outcome.

    The parse task carries its own `SCHEDULE = '5 MINUTE'` with a
    `WHEN SYSTEM$STREAM_HAS_DATA` guard, which makes driving it manually
    surprisingly delicate:

      - If the root is left resumed, a scheduled run races the manual one and
        consumes the stream first. The manual run then finds the stream empty, is
        SKIPPED by its WHEN clause, and **a skipped root does not run its
        children** - so RAW gains rows while the corpus never does. Observed
        exactly that: PDF_INTERNAL_RAW +34, corpus +0.
      - `EXECUTE TASK` on a *suspended* root still runs the whole graph, verified
        directly, so suspending the root removes the race without preventing the
        manual run.
      - Suspend order matters: Snowflake refuses to suspend a child while the root
        is resumed ("Unable to update graph with root task ... since that root
        task is not suspended"). Root first, then children; resume in reverse.

    Success is judged by whether the stream drained, not by task state, because a
    concurrent scheduled run can make the state look like a failure after the work
    has actually completed.
    """
    import time

    try:
        session.sql(f"ALTER TASK {root} SUSPEND").collect()
        # The child must stay resumed to participate in a manually triggered run.
        session.sql(f"ALTER TASK {chunk} RESUME").collect()
    except Exception as exc:
        log_warning(f"  {key}: could not prepare task graph ({exc})")

    try:
        session.sql(f"EXECUTE TASK {root}").collect()
    except Exception as exc:
        log_warning(f"  {key}: could not execute parse task ({exc})")
        return 'FAILED'

    # Poll until the stream drains, which is the real completion signal.
    deadline = time.time() + 1800
    drained = False
    while time.time() < deadline:
        time.sleep(15)
        try:
            drained = not session.sql(
                f"SELECT SYSTEM$STREAM_HAS_DATA('{stream}') AS h"
            ).collect()[0]['H']
        except Exception as exc:
            # Stop polling, but say why. The outcome below is already reported as
            # FAILED; without this line the reason for a stalled pipeline is lost
            # and the only symptom is an unexplained timeout.
            log_warning(f"  Could not check stream {stream} while waiting: {exc}")
            break
        if drained:
            break

    if not drained:
        log_warning(
            f"  Pipeline {key} left unparsed files on the stage - documents are "
            "generated but not yet searchable"
        )
        return 'FAILED'

    # Give the chunk task a chance to finish now that parse has consumed the
    # stream; the corpus, not the stream, is what the agent reads.
    for _ in range(40):
        rows = session.sql(f"""
            SELECT STATE FROM TABLE({config.DATABASE['name']}.INFORMATION_SCHEMA.TASK_HISTORY(
                TASK_NAME => '{chunk.split('.')[-1]}',
                SCHEDULED_TIME_RANGE_START => DATEADD('minute', -45, CURRENT_TIMESTAMP())))
            ORDER BY SCHEDULED_TIME DESC LIMIT 1
        """).collect()
        if rows and rows[0]['STATE'] in ('SUCCEEDED', 'FAILED', 'SKIPPED'):
            break
        time.sleep(15)

    return 'SUCCESS'



def _dry_run_report(session: Session, target: date, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Report what a real run would do, touching nothing."""
    from data import cadence

    log_substep("Dry run - no changes will be written")
    summary['marketplace_corpora'] = _describe_corpora_backlog(session)
    summary['coverage_backfill'] = backfill_coverage_gaps(session, target, dry_run=True)
    due = _evaluate_due_documents(session, target, cadence)
    summary['documents_due'] = {k: len(v) for k, v in due.items()}
    summary['status'] = 'DRY_RUN'
    return summary


def _describe_corpora_backlog(session: Session) -> Dict[str, Any]:
    """Report how much the transcript and SEC filing corpora are behind the source.

    Counts what a real run would load, without loading it. The loaders are MERGEs, so
    "behind" is simply how many source documents have no matching row yet.

    The filters here must mirror the loaders exactly - the same DIM_SECURITY join and
    the same transcript-type rule. A looser query reports a backlog that the loader
    will never clear, which is worse than reporting nothing: it looks like the refresh
    is permanently failing.
    """
    database = config.DATABASE['name']
    raw_schema = config.DATABASE['schemas']['raw']
    real_db = config.REAL_DATA_SOURCES['database']
    real_schema = config.REAL_DATA_SOURCES['schema']
    curated = config.DATABASE['schemas']['curated']
    years = config.YEARS_OF_HISTORY
    ts_table = config.REAL_DATA_SOURCES['tables']['company_event_transcripts']['table']
    sec_table = config.REAL_DATA_SOURCES['tables']['sec_filing_text']['table']

    out: Dict[str, Any] = {}

    try:
        out['transcripts_pending'] = session.sql(f"""
            SELECT COUNT(*) AS n FROM (
                SELECT t.COMPANY_ID, t.EVENT_TIMESTAMP
                FROM {real_db}.{real_schema}.{ts_table} t
                INNER JOIN {database}.{curated}.DIM_ISSUER i
                    ON t.COMPANY_ID = i.PROVIDERCOMPANYID
                INNER JOIN {database}.{curated}.DIM_SECURITY s
                    ON i.IssuerID = s.IssuerID AND s.AssetClass = 'Equity'
                WHERE t.EVENT_TIMESTAMP >= DATEADD('year', -{years}, CURRENT_DATE())
                  AND ((t.EVENT_TYPE = 'Earnings Call'
                        AND t.TRANSCRIPT_TYPE = 'SPEAKERS_ANNOTATED')
                       OR t.EVENT_TYPE != 'Earnings Call')
                GROUP BY 1, 2
                EXCEPT
                SELECT COMPANY_ID, EVENT_TIMESTAMP
                FROM {database}.{raw_schema}.COMPANY_EVENT_TRANSCRIPTS_RAW
                GROUP BY 1, 2
            )
        """).collect()[0]['N']
    except Exception as exc:
        out['transcripts_pending'] = f'unknown ({str(exc)[:80]})'

    try:
        out['sec_filings_pending'] = session.sql(f"""
            SELECT COUNT(*) AS n
            FROM {real_db}.{real_schema}.{sec_table} t
            INNER JOIN {database}.{curated}.DIM_ISSUER i ON t.CIK = i.CIK
            INNER JOIN {database}.{curated}.DIM_COVERAGE_UNIVERSE cu
                ON i.IssuerID = cu.ISSUERID
            LEFT JOIN {database}.{raw_schema}.SEC_FILING_TEXT_RAW r
                ON t.SEC_DOCUMENT_ID = r.SEC_DOCUMENT_ID
            WHERE t.PERIOD_END_DATE >= DATEADD('year', -{years}, CURRENT_DATE())
              AND LENGTH(t.VALUE) > 100
              AND r.SEC_DOCUMENT_ID IS NULL
        """).collect()[0]['N']
    except Exception as exc:
        out['sec_filings_pending'] = f'unknown ({str(exc)[:80]})'

    return out


def status(session: Session) -> Dict[str, Any]:
    """Health snapshot for the --status command."""
    from data import cadence

    database = config.DATABASE['name']
    out: Dict[str, Any] = {}
    out['watermark'] = str(cadence.get_watermark(session, REFRESH_KEY) or 'never run')
    out['latest_price_date'] = str(get_max_price_date(session))
    out['marketplace_corpora'] = _describe_corpora_backlog(session)

    rows = session.sql(f"""
        SELECT DOC_TYPE, COUNT(*) AS vintages, MAX(VINTAGE_DATE) AS latest
        FROM {database}.RAW.DOCUMENT_VINTAGE_LOG
        GROUP BY DOC_TYPE ORDER BY DOC_TYPE
    """).collect()
    out['vintage_log'] = [r.as_dict() for r in rows]
    return out
