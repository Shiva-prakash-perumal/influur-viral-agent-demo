import os
import subprocess

def run_dbt():
    project_dir = os.path.join(os.path.dirname(__file__), "..", "dbt")
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = project_dir
    subprocess.check_call(["dbt", "run"], cwd=project_dir, env=env)

if __name__ == "__main__":
    run_dbt()
