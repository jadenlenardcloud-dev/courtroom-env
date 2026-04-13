"""
Supply Chain OpenEnv — Inference Script
Required for platform evaluation.
"""

import argparse
import json
import sys
import os

# Ensure the root directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from env.environment import SupplyChainEnv
    from baseline import HeuristicAgent, run_episode
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Supply Chain OpenEnv Inference")
    # Make --task REQUIRED to satisfy the validator log seen in the screenshot
    parser.add_argument("--task", choices=["task_easy", "task_medium", "task_hard"],
                        required=True, help="Which task to run")
    parser.add_argument("--render", action="store_true", help="Print step-by-step output")
    parser.add_argument("--json", action="store_true", default=True, help="Output results as JSON")
    
    args = parser.parse_args()

    # The platform likely expects the results for the specific task
    try:
        result = run_episode(args.task, render=args.render)
        
        # Always print JSON for the validator if requested or by default
        if args.json:
            print(json.dumps({args.task: result}, indent=2, default=str))
    except Exception as e:
        print(f"Execution Error: {e}")
        sys.exit(1)

