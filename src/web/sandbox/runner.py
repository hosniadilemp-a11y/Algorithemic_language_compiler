import subprocess
import sys
import tempfile
import os
import json
import time

def _normalize_output(value):
    """Normalize outputs before comparison to avoid false negatives on whitespace."""
    text = '' if value is None else str(value)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

def execute_code(python_code, test_cases):
    """
    Executes the provided Python code against a list of test cases in a restricted subprocess.
    Requires python_code to read from stdin and write to stdout.
    """
    results = []
    
    # Write the compiled python code to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_script:
        temp_script.write(python_code)
        script_path = temp_script.name

    try:
        for tc in test_cases:
            tc_id = tc['id']
            input_data = tc['input']
            expected_output = _normalize_output(tc.get('expected_output', ''))

            try:
                # Run the subprocess with a tight timeout
                start_time = time.time()
                process = subprocess.run(
                    [sys.executable, script_path],
                    input=input_data,
                    text=True,
                    capture_output=True,
                    timeout=2.0 # 2 seconds max execution time per test
                )
                
                actual_output = process.stdout.strip()
                error_output = process.stderr.strip()
                
                if process.returncode == 0:
                    normalized_actual = _normalize_output(actual_output)
                    # Keep strict compare first, then allow whitespace-only differences.
                    passed = (
                        normalized_actual == expected_output
                        or normalized_actual.split() == expected_output.split()
                    )
                    results.append({
                        'test_case_id': tc_id,
                        'input': input_data,
                        'expected_output': expected_output,
                        'passed': passed,
                        'actual_output': actual_output,
                        'error': None
                    })
                else:
                    results.append({
                        'test_case_id': tc_id,
                        'input': input_data,
                        'expected_output': expected_output,
                        'passed': False,
                        'actual_output': actual_output,
                        'error': error_output or "Execution Failed"
                    })
                    
            except subprocess.TimeoutExpired:
                results.append({
                    'test_case_id': tc_id,
                    'input': input_data,
                    'expected_output': expected_output,
                    'passed': False,
                    'actual_output': "",
                    'error': "Timeout: Maximum execution time exceeded."
                })
            except Exception as e:
                results.append({
                    'test_case_id': tc_id,
                    'input': input_data,
                    'expected_output': expected_output,
                    'passed': False,
                    'actual_output': "",
                    'error': f"System Error: {str(e)}"
                })
                
    finally:
        # Cleanup temp file
        if os.path.exists(script_path):
            os.remove(script_path)

    return results
