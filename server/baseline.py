"""
Supply Chain OpenEnv — Baseline Inference Script
Run deterministic heuristic agents across all 3 tasks and report scores.

Usage:
    python scripts/baseline.py
    python scripts/baseline.py --task task_hard
    python scripts/baseline.py --render
"""

import argparse
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env.environment import SupplyChainEnv
from env.models import AgentAction, ActionType, ShipmentStatus, Priority
from tasks.graders import grade_episode, TASK_REGISTRY


# ─────────────────────────────────────────────
# Heuristic Baseline Agents
# ─────────────────────────────────────────────

class HeuristicAgent:
    """
    Rule-based agent that applies simple supply chain triage logic.
    Serves as a reproducible baseline (no randomness).
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._notified_orders: set = set()
        self._contacted_suppliers: set = set()

    def act(self, obs) -> AgentAction:
        """Choose an action given current observation."""

        # Priority 1: Contact suppliers for active disruptions
        for dis in obs.active_disruptions:
            for sup_id in dis.affected_supplier_ids:
                if sup_id not in self._contacted_suppliers:
                    self._contacted_suppliers.add(sup_id)
                    return AgentAction(
                        action_type=ActionType.CONTACT_SUPPLIER,
                        target_id=sup_id,
                        reasoning=f"Contacting supplier {sup_id} for disruption {dis.id}",
                    )

        # Priority 2: Reroute URGENT/HIGH shipments that are BLOCKED
        urgent_blocked = sorted(
            [s for s in obs.shipments if s.status == ShipmentStatus.BLOCKED],
            key=lambda s: (
                0 if s.priority == Priority.URGENT else
                1 if s.priority == Priority.HIGH else
                2 if s.priority == Priority.MEDIUM else 3,
                -s.cargo_value_usd,
            )
        )
        if urgent_blocked:
            target = urgent_blocked[0]
            if target.reroute_cost_usd <= obs.budget_remaining_usd:
                return AgentAction(
                    action_type=ActionType.REROUTE_SHIPMENT,
                    target_id=target.id,
                    reasoning=f"Rerouting {target.priority} shipment {target.id}",
                )

        # Priority 3: Issue customer alerts for delayed orders
        for order in obs.customer_orders:
            if order.order_id not in self._notified_orders and order.current_delay_days > 0:
                self._notified_orders.add(order.order_id)
                return AgentAction(
                    action_type=ActionType.ISSUE_CUSTOMER_ALERT,
                    target_id=order.order_id,
                    reasoning=f"Alerting customer for order {order.order_id}",
                )

        # Priority 4: Hold production if inventory is critical
        critical_inv = [i for i in obs.inventory if i.days_of_stock < 3]
        if critical_inv:
            return AgentAction(
                action_type=ActionType.HOLD_PRODUCTION,
                reasoning="Holding production — critical inventory levels",
            )

        # Priority 5: Expedite rerouted shipments that are still delayed
        rerouted_delayed = [
            s for s in obs.shipments
            if s.status == ShipmentStatus.REROUTED and s.days_delayed > 2
        ]
        if rerouted_delayed:
            target = rerouted_delayed[0]
            if target.expedite_cost_usd <= obs.budget_remaining_usd * 0.3:
                return AgentAction(
                    action_type=ActionType.EXPEDITE_ORDER,
                    target_id=target.id,
                    reasoning=f"Expediting still-delayed shipment {target.id}",
                )

        # Priority 6: Reallocate surplus inventory
        surplus = [i for i in obs.inventory if i.quantity_on_hand > i.reorder_point * 3]
        shortage = [i for i in obs.inventory if i.days_of_stock < 5]
        if surplus and shortage:
            return AgentAction(
                action_type=ActionType.REQUEST_INVENTORY_DUMP,
                reasoning="Reallocating surplus inventory to cover shortage",
            )

        return AgentAction(
            action_type=ActionType.NO_OP,
            reasoning="No high-priority action identified this step",
        )


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def run_episode(task_id: str, render: bool = False) -> dict:
    env = SupplyChainEnv()
    agent = HeuristicAgent(task_id)

    obs = env.reset(task_id)
    trajectory = []
    total_reward = 0.0

    if render:
        print(f"\n{'='*60}")
        print(f"  TASK: {TASK_REGISTRY[task_id].name}")
        print(f"  Difficulty: {TASK_REGISTRY[task_id].difficulty.upper()}")
        print(f"  Max Steps: {TASK_REGISTRY[task_id].max_steps}")
        print(f"  Budget: ${TASK_REGISTRY[task_id].budget_usd:,.0f}")
        print(f"{'='*60}")
        print(f"\n  Active disruptions: {len(obs.active_disruptions)}")
        for d in obs.active_disruptions:
            print(f"  ⚠  [{d.type.value}] {d.description[:60]}...")

    done = False
    while not done:
        action = agent.act(obs)
        result = env.step(action)

        trajectory.append({
            "step": obs.step,
            "action": action.action_type,
            "target_id": action.target_id,
            "reasoning": action.reasoning,
            "reward": result.reward,
            "events": result.info.get("events", []),
        })

        total_reward += result.reward
        obs = result.observation
        done = result.done

        if render:
            print(f"\n  Step {obs.step:2d} | {action.action_type.value:<25} "
                  f"target={action.target_id or 'n/a':<12} "
                  f"reward={result.reward:+.4f}")
            for ev in result.info.get("events", []):
                print(f"          └─ {ev}")

    ep_result = env.get_episode_result()
    scores = grade_episode(task_id, trajectory, obs, ep_result)

    if render:
        print(f"\n{'─'*60}")
        print(f"  EPISODE COMPLETE")
        print(f"  Steps: {obs.step} / {obs.max_steps}")
        print(f"  SLA Breaches: {obs.sla_breach_count}")
        print(f"  Budget Spent: ${ep_result.financial_loss_usd:,.0f} / "
              f"${TASK_REGISTRY[task_id].budget_usd:,.0f}")
        delivered = sum(1 for s in obs.shipments if s.status == ShipmentStatus.DELIVERED)
        print(f"  Shipments Delivered: {delivered} / {len(obs.shipments)}")
        print(f"\n  GRADER SCORES:")
        for k, v in scores.items():
            bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        bar = "█" * int(scores["total"] * 20) + "░" * (20 - int(scores["total"] * 20))
        threshold = TASK_REGISTRY[task_id].reward_threshold_pass
        passed = scores["total"] >= threshold
        print(f"\n  FINAL SCORE: {scores['total']:.3f}  [{bar}]")
        print(f"  PASS THRESHOLD: {threshold}  →  {'✅ PASS' if passed else '❌ FAIL'}")

    return {
        "task_id": task_id,
        "scores": scores,
        "steps": obs.step,
        "sla_breaches": obs.sla_breach_count,
        "budget_spent": ep_result.financial_loss_usd,
        "passed": scores["total"] >= TASK_REGISTRY[task_id].reward_threshold_pass,
    }


def run_all(render: bool = False) -> dict:
    results = {}
    for task_id in ["task_easy", "task_medium", "task_hard"]:
        results[task_id] = run_episode(task_id, render=render)

    if render:
        print(f"\n{'='*60}")
        print("  BENCHMARK SUMMARY")
        print(f"{'='*60}")
        for tid, r in results.items():
            status = "✅" if r["passed"] else "❌"
            print(f"  {status} {tid:<15} score={r['scores']['total']:.3f}  "
                  f"sla_breaches={r['sla_breaches']}  steps={r['steps']}")
        overall = sum(r["scores"]["total"] for r in results.values()) / len(results)
        print(f"\n  Overall Mean Score: {overall:.3f}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Supply Chain OpenEnv baseline")
    parser.add_argument("--task", choices=["task_easy", "task_medium", "task_hard", "all"],
                        default="all", help="Which task to run")
    parser.add_argument("--render", action="store_true", help="Print step-by-step output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if args.task == "all":
        results = run_all(render=args.render or not args.json)
    else:
        result = run_episode(args.task, render=args.render or not args.json)
        results = {args.task: result}

    if args.json:
        print(json.dumps(results, indent=2, default=str))
