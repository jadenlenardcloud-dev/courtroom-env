import os
import json
import logging
from openai import OpenAI
from environment import CourtroomEnvironment

# Load required environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# Initialize OpenAI client
client = OpenAI(
    api_key=HF_TOKEN or os.getenv("OPENAI_API_KEY", "dummy"),
    base_url=API_BASE_URL
)

def run_task(task_id: str, max_steps: int = 15):
    env = CourtroomEnvironment()

    try:
        print("START")

        state = env.reset(task_id)
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
        elif hasattr(state, 'dict'):
            state_dict = state.dict()
        else:
            state_dict = state

        system_prompt = (
            "You are a criminal defense attorney in a courtroom simulation. "
            "You must return purely a JSON object with two string fields: "
            "1. 'action_type' - the type of action to take (e.g., 'object', 'cross_examine', 'present_evidence', 'deliver_statement'). "
            "2. 'action_content' - the exact text to say to the courtroom."
        )

        for step_idx in range(max_steps):
            state_str = json.dumps(state_dict)

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Current State: {state_str}\n\nWhat is your next action? Return ONLY JSON."}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content
                action = json.loads(content)

            except Exception as e:
                logging.error(f"LLM call failed at step {step_idx}: {e}")
                action = {
                    "action_type": "deliver_statement",
                    "action_content": "The defense requests a brief recess."
                }

            action_type = action.get("action_type", "deliver_statement")
            action_content = action.get("action_content", "No further questions.")

            try:
                state, reward, done, truncated, info = env.step(action_type, action_content)
            except Exception as e:
                logging.error(f"Environment step failed at step {step_idx}: {e}")
                break

            if hasattr(state, 'model_dump'):
                state_dict = state.model_dump()
            elif hasattr(state, 'dict'):
                state_dict = state.dict()
            else:
                state_dict = state

            print("STEP")

            if done or truncated:
                break

    finally:
        print("END")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Courtroom Argument Simulator Inference")
    # KEY FIX: default="task_easy" instead of required=True
    # This prevents a crash when the validator calls inference.py with no arguments
   
    args = parser.parse_args()
parser.add_argument(
    "--task",
    type=str,
    default="task_easy",   # ← ADD this instead
    help="Task ID (e.g., task_easy, task_medium, task_hard)"
)

    if LOCAL_IMAGE_NAME:
        print(f"Using local image: {LOCAL_IMAGE_NAME}")

    run_task(args.task)
